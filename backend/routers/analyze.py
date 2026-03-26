import time

from fastapi import APIRouter, UploadFile, File

from models.response import CatfishResult
from services.analyzer import run_analysis
from utils.image import validate_upload, save_temp_file, cleanup_temp_files

router = APIRouter()


@router.post("/analyze", response_model=CatfishResult)
async def analyze_image(file: UploadFile = File(...)):
    validate_upload(file)

    temp_path = await save_temp_file(file)
    start = time.time()

    try:
        result = await run_analysis(temp_path)
        result.analysis_duration_ms = int((time.time() - start) * 1000)
        return result
    finally:
        cleanup_temp_files(temp_path)
