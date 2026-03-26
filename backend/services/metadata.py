import asyncio
from functools import partial

import exifread
from PIL import Image
from PIL.ExifTags import TAGS

from models.response import MetadataResult

EDITING_SOFTWARE = [
    "photoshop", "gimp", "facetune", "faceapp", "lightroom",
    "snapseed", "beautycam", "meitu", "remini", "pixlr",
]


def _extract_metadata(image_path: str) -> MetadataResult:
    signals: list[str] = []
    risk = 50  # Start neutral

    # Extract EXIF with exifread
    with open(image_path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    has_exif = len(tags) > 0

    if not has_exif:
        signals.append("No EXIF metadata found — may be stripped or screenshot")
        risk += 30
        return MetadataResult(
            has_exif=False,
            suspicious_signals=signals,
            risk_score=min(100, max(0, risk)),
        )

    # Camera info
    camera_make = str(tags.get("Image Make", "")).strip() or None
    camera_model = str(tags.get("Image Model", "")).strip() or None
    software = str(tags.get("Image Software", "")).strip() or None
    original_date = str(tags.get("EXIF DateTimeOriginal", "")).strip() or None
    has_thumbnail = "JPEGThumbnail" in tags

    # GPS check
    gps_present = any(k.startswith("GPS") for k in tags)

    # Scoring
    if camera_make and camera_model:
        signals.append(f"Camera: {camera_make} {camera_model}")
        risk -= 20

    if gps_present:
        signals.append("GPS location data present")
        risk -= 15

    if original_date:
        signals.append(f"Original date: {original_date}")
        risk -= 10

    if software:
        sw_lower = software.lower()
        for editor in EDITING_SOFTWARE:
            if editor in sw_lower:
                signals.append(f"Edited with: {software}")
                risk += 20
                break
        else:
            signals.append(f"Software: {software}")

    if has_thumbnail:
        risk -= 5

    # Check image dimensions via Pillow for quality assessment
    try:
        img = Image.open(image_path)
        w, h = img.size
        if w > 2000 or h > 2000:
            signals.append(f"High resolution: {w}x{h}")
        if w == h:
            signals.append("Square aspect ratio — common for profile pictures")
            risk += 5
    except Exception:
        pass

    return MetadataResult(
        has_exif=has_exif,
        camera_make=camera_make,
        camera_model=camera_model,
        software=software,
        gps_present=gps_present,
        original_date=original_date,
        has_thumbnail=has_thumbnail,
        suspicious_signals=signals,
        risk_score=min(100, max(0, risk)),
    )


async def analyze_metadata(image_path: str) -> MetadataResult:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_extract_metadata, image_path))
