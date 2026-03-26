import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.analyze import router as analyze_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    # Verify OpenCV face detector is available (no downloads needed)
    import cv2
    cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if os.path.exists(cascade):
        print("OpenCV face detector ready.")
    # Optionally try DeepFace (may fail if models not downloaded)
    try:
        from deepface import DeepFace
        DeepFace.build_model("Facenet")
        print("DeepFace models loaded (enhanced analysis available).")
    except Exception:
        print("DeepFace models unavailable - using OpenCV face analysis only.")
    yield
    # Cleanup temp dir on shutdown
    import shutil
    if os.path.exists(settings.TEMP_DIR):
        shutil.rmtree(settings.TEMP_DIR, ignore_errors=True)


app = FastAPI(
    title="Catfish Detector API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
