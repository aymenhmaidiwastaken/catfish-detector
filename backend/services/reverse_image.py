import asyncio
import base64
import io
import re
from urllib.parse import urlparse

import httpx
from PIL import Image

from config import settings
from models.response import ReverseImageMatch, ReverseImageResult

STOCK_DOMAINS = {
    "shutterstock.com", "gettyimages.com", "istockphoto.com",
    "adobestock.com", "stock.adobe.com", "pexels.com", "unsplash.com",
    "depositphotos.com", "123rf.com", "dreamstime.com", "alamy.com",
    "bigstockphoto.com", "stocksy.com", "eyeem.com", "pond5.com",
    "vectorstock.com", "canstockphoto.com", "freepik.com",
    "pixabay.com", "rawpixel.com", "stockvault.net",
    "thispersondoesnotexist.com",
}

SOCIAL_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tiktok.com", "linkedin.com", "pinterest.com", "tumblr.com",
    "vk.com", "ok.ru", "reddit.com", "flickr.com",
}

IGNORE_DOMAINS = {
    "google.com", "googleapis.com", "gstatic.com", "googleusercontent.com",
    "bing.com", "bing.net", "yandex.com", "yandex.net", "yandex.ru",
    "yahoo.com", "duckduckgo.com", "baidu.com", "lens.google.com",
    "w3.org", "schema.org", "iili.io", "freeimage.host",
    "support.google.com",
}

# Shopping / e-commerce / product sites — matches here mean the search engine
# found a similar-looking *product*, NOT the same photo reused elsewhere.
SHOPPING_DOMAINS = {
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.co.jp",
    "amazon.ca", "amazon.com.au", "amazon.in", "amazon.co.za",
    "ebay.com", "ebay.co.uk", "ebay.de",
    "walmart.com", "target.com", "bestbuy.com", "newegg.com",
    "aliexpress.com", "alibaba.com", "wish.com", "temu.com", "shein.com",
    "etsy.com", "wayfair.com", "overstock.com",
    "dell.com", "hp.com", "lenovo.com", "asus.com", "acer.com",
    "apple.com", "samsung.com", "microsoft.com",
    "bhphotovideo.com", "adorama.com",
    "shopify.com", "squarespace.com", "woocommerce.com",
    "rakuten.com", "flipkart.com", "lazada.com", "shopee.com",
    "costco.com", "homedepot.com", "lowes.com",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def _get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _is_stock_site(url: str) -> bool:
    domain = _get_domain(url)
    return any(stock in domain for stock in STOCK_DOMAINS)


def _is_social_media(url: str) -> bool:
    domain = _get_domain(url)
    return any(social in domain for social in SOCIAL_DOMAINS)


def _is_shopping_site(url: str) -> bool:
    domain = _get_domain(url)
    return any(shop in domain for shop in SHOPPING_DOMAINS)


def _should_ignore(url: str) -> bool:
    domain = _get_domain(url)
    if not domain or len(domain) < 4:
        return True
    return any(ign in domain for ign in IGNORE_DOMAINS)


def _compress_image(image_path: str, max_dim: int = 800, quality: int = 75) -> bytes:
    """Resize and compress image to JPEG bytes for upload to search engines."""
    img = Image.open(image_path)
    img = img.convert("RGB")  # PNG/RGBA -> RGB for JPEG
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _read_image_b64(image_path: str) -> str:
    return base64.b64encode(_compress_image(image_path)).decode()


def _read_image(image_path: str) -> bytes:
    return _compress_image(image_path)


# ---------------------------------------------------------------------------
# Helper: Upload image to get a temporary public URL
# ---------------------------------------------------------------------------
async def _get_public_url(image_path: str) -> str | None:
    """Upload to freeimage.host to get a temporary public URL."""
    try:
        b64 = _read_image_b64(image_path)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://freeimage.host/api/1/upload",
                data={
                    "key": "6d207e02198a847aa98d0a2a901485a5",
                    "source": b64,
                    "format": "json",
                },
            )
            if resp.status_code == 200:
                return resp.json().get("image", {}).get("url")
    except Exception as e:
        print(f"[ImageHost] Upload failed: {e}")
    return None


# ---------------------------------------------------------------------------
# Strategy 1: Serper.dev Google Lens (BEST - 2500 free/month)
# ---------------------------------------------------------------------------
async def _search_serper_lens(public_url: str | None) -> tuple[str, list[ReverseImageMatch]]:
    if not settings.SERPER_API_KEY or not public_url:
        return "Serper", []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://google.serper.dev/lens",
                headers={
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"url": public_url},
            )

            if resp.status_code != 200:
                print(f"[Serper] Status {resp.status_code}: {resp.text[:200]}")
                return "Serper", []

            data = resp.json()
            matches = []

            # Serper Lens returns "organic" as the main results — these are
            # pages where Google Lens found this image or visually similar ones.
            # Filter out shopping/product sites (they match objects IN the photo,
            # not the photo itself) and search engines.
            for key in ("organic", "exact_matches", "visual_matches"):
                for item in data.get(key, []):
                    url = item.get("link", "")
                    if url and not _should_ignore(url) and not _is_shopping_site(url):
                        matches.append(ReverseImageMatch(
                            source_url=url,
                            page_title=item.get("title", ""),
                            thumbnail_url=item.get("thumbnailUrl") or item.get("imageUrl"),
                            is_stock_site=_is_stock_site(url),
                        ))

            return "Serper", matches[:15]
    except Exception as e:
        print(f"[Serper] Error: {e}")
        return "Serper", []


# ---------------------------------------------------------------------------
# Strategy 2: SerpAPI (if configured)
# ---------------------------------------------------------------------------
async def _search_serpapi(image_path: str) -> tuple[str, list[ReverseImageMatch]]:
    if not settings.SERP_API_KEY:
        return "SerpAPI", []

    try:
        from serpapi import GoogleSearch

        b64 = _read_image_b64(image_path)
        params = {
            "engine": "google_reverse_image",
            "image": f"data:image/jpeg;base64,{b64}",
            "api_key": settings.SERP_API_KEY,
        }

        loop = asyncio.get_event_loop()
        search = await loop.run_in_executor(None, lambda: GoogleSearch(params))
        results = await loop.run_in_executor(None, search.get_dict)

        matches = []
        for item in results.get("image_results", [])[:15]:
            url = item.get("link", "")
            if not _should_ignore(url) and not _is_shopping_site(url):
                matches.append(ReverseImageMatch(
                    source_url=url,
                    page_title=item.get("title", ""),
                    thumbnail_url=item.get("thumbnail"),
                    is_stock_site=_is_stock_site(url),
                ))
        return "SerpAPI", matches
    except Exception as e:
        print(f"[SerpAPI] Error: {e}")
        return "SerpAPI", []


# ---------------------------------------------------------------------------
# Strategy 3: Yandex (scraping fallback)
# ---------------------------------------------------------------------------
async def _search_yandex(image_path: str) -> tuple[str, list[ReverseImageMatch]]:
    try:
        image_data = _read_image(image_path)

        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True, headers={"User-Agent": UA}
        ) as client:
            resp = await client.post(
                "https://yandex.com/images-apphost/image-download",
                files={"upfile": ("image.jpg", image_data, "image/jpeg")},
            )

            if resp.status_code != 200:
                return "Yandex", []

            data = resp.json()
            image_url = data.get("url", "")
            image_id = data.get("id", "") or data.get("image_id", "")

            if not image_id and not image_url:
                return "Yandex", []

            params = {"rpt": "imageview", "url": image_url}
            if image_id:
                params["cbir_id"] = image_id

            search_resp = await client.get(
                "https://yandex.com/images/search", params=params
            )

            text = search_resp.text
            matches = []
            seen = set()

            for pattern in [
                r'"url":"(https?://[^"]+)"',
                r'"source_url":"(https?://[^"]+)"',
                r'"originalImage":\{"url":"(https?://[^"]+)"',
                r'"page_url":"(https?://[^"]+)"',
            ]:
                for url in re.findall(pattern, text):
                    url = url.replace("\\/", "/")
                    if _should_ignore(url) or _is_shopping_site(url) or url in seen:
                        continue
                    seen.add(url)
                    matches.append(ReverseImageMatch(
                        source_url=url,
                        page_title="",
                        is_stock_site=_is_stock_site(url),
                    ))

            return "Yandex", matches[:15]
    except Exception as e:
        print(f"[Yandex] Error: {e}")
        return "Yandex", []


# ---------------------------------------------------------------------------
# Strategy 4: Google Lens direct (scraping fallback)
# ---------------------------------------------------------------------------
async def _search_google_lens(image_path: str) -> tuple[str, list[ReverseImageMatch]]:
    try:
        image_data = _read_image(image_path)

        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True, headers={"User-Agent": UA}
        ) as client:
            resp = await client.post(
                "https://lens.google.com/v3/upload",
                files={"encoded_image": ("image.jpg", image_data, "image/jpeg")},
                data={"sbisrc": "Chromium"},
            )

            if resp.status_code != 200:
                return "Google Lens", []

            text = resp.text
            matches = []
            seen = set()

            # Target known domains in the response
            known_pattern = r'"(https?://(?:www\.)?(?:' + "|".join(
                d.replace(".", r"\.")
                for d in (STOCK_DOMAINS | SOCIAL_DOMAINS)
            ) + r')[^"]*)"'

            for url in re.findall(known_pattern, text):
                url = url.split("\\")[0]
                if url not in seen and not _is_shopping_site(url):
                    seen.add(url)
                    matches.append(ReverseImageMatch(
                        source_url=url,
                        page_title="",
                        is_stock_site=_is_stock_site(url),
                    ))

            return "Google Lens", matches[:15]
    except Exception as e:
        print(f"[Google Lens] Error: {e}")
        return "Google Lens", []


# ===========================================================================
# Main orchestrator
# ===========================================================================
async def search_reverse_image(image_path: str) -> ReverseImageResult:
    signals: list[str] = []
    risk = 50

    # Step 1: Upload image to get a public URL (for Serper)
    public_url = await _get_public_url(image_path)

    # Step 2: Run all searches concurrently
    results = await asyncio.gather(
        _search_serper_lens(public_url),
        _search_serpapi(image_path),
        _search_google_lens(image_path),
        _search_yandex(image_path),
        return_exceptions=True,
    )

    engines_with_results = []
    engines_searched = []
    all_raw: list[ReverseImageMatch] = []

    for result in results:
        if isinstance(result, Exception):
            continue
        name, matches = result
        if name == "Serper" and not settings.SERPER_API_KEY:
            continue  # Don't list engines with no key
        if name == "SerpAPI" and not settings.SERP_API_KEY:
            continue
        engines_searched.append(name)
        if matches:
            engines_with_results.append(name)
            all_raw.extend(matches)

    # Deduplicate by domain
    seen_domains = set()
    all_matches: list[ReverseImageMatch] = []
    for m in all_raw:
        domain = _get_domain(m.source_url)
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            all_matches.append(m)

    total = len(all_matches)
    found_stock = any(m.is_stock_site for m in all_matches)
    found_social = any(_is_social_media(m.source_url) for m in all_matches)

    # Build signals
    if engines_searched:
        signals.append(f"Searched via: {', '.join(engines_searched)}")
    if engines_with_results:
        signals.append(f"Matches from: {', '.join(engines_with_results)}")

    if total == 0:
        signals.append("Image not found elsewhere online")
        risk -= 10
    elif total == 1:
        signals.append(f"Found on 1 site")
    else:
        signals.append(f"Found on {total} different sites")

    if found_stock:
        stock_names = sorted(set(_get_domain(m.source_url) for m in all_matches if m.is_stock_site))
        signals.append(f"Stock photo site(s): {', '.join(stock_names)}")
        risk += 40

    if found_social:
        social_names = sorted(set(_get_domain(m.source_url) for m in all_matches if _is_social_media(m.source_url)))
        signals.append(f"Social media: {', '.join(social_names)}")
        risk += 10

    if total >= 5:
        signals.append("Widely distributed image")
        risk += 25
    elif total >= 3:
        risk += 15

    has_api = settings.SERPER_API_KEY or settings.SERP_API_KEY
    if not has_api:
        signals.append("Get free API key at serper.dev for better results")

    return ReverseImageResult(
        total_matches=total,
        matches=all_matches[:10],
        found_on_stock_sites=found_stock,
        found_on_social_media=found_social,
        suspicious_signals=signals,
        risk_score=min(100, max(0, risk)),
    )
