import os
import uuid
from pathlib import Path

from PIL import Image
from fastapi import UploadFile, HTTPException

from config import settings

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_DIMENSION = 1920


def validate_upload(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG, WebP",
        )


async def save_temp_file(file: UploadFile) -> str:
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = temp_dir / filename

    content = await file.read()

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    with open(filepath, "wb") as f:
        f.write(content)

    return str(filepath)


def resize_for_analysis(image_path: str) -> str:
    """Resize image if too large, returns path to resized copy."""
    img = Image.open(image_path)
    if max(img.size) <= MAX_DIMENSION:
        return image_path

    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    resized_path = image_path.rsplit(".", 1)[0] + "_resized." + image_path.rsplit(".", 1)[1]
    img.save(resized_path)
    return resized_path


def cleanup_temp_files(*paths: str) -> None:
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
