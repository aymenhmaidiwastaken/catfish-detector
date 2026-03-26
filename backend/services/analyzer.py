import asyncio

from models.response import CatfishResult
from services.metadata import analyze_metadata
from services.face_analysis import analyze_face
from services.reverse_image import search_reverse_image
from services.scoring import compute_overall_score
from utils.image import resize_for_analysis, cleanup_temp_files


async def run_analysis(image_path: str) -> CatfishResult:
    # Create a resized copy for face/reverse search analysis
    resized_path = resize_for_analysis(image_path)

    try:
        # Run all analyses concurrently
        metadata_result, face_result, reverse_result = await asyncio.gather(
            analyze_metadata(image_path),       # Use original for full EXIF
            analyze_face(resized_path),          # Use resized for speed
            search_reverse_image(resized_path),  # Use resized for upload
        )

        score, verdict = compute_overall_score(
            metadata_score=metadata_result.risk_score,
            reverse_image_score=reverse_result.risk_score,
            face_analysis_score=face_result.risk_score,
        )

        return CatfishResult(
            overall_score=score,
            verdict=verdict,
            metadata=metadata_result,
            reverse_image=reverse_result,
            face_analysis=face_result,
            analysis_duration_ms=0,  # Will be set by the router
        )
    finally:
        if resized_path != image_path:
            cleanup_temp_files(resized_path)
