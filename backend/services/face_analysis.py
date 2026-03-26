import asyncio
import os
from functools import partial
from pathlib import Path

import cv2
import numpy as np

from models.response import FaceAnalysisResult

# ---------------------------------------------------------------------------
# Load OpenCV DNN models for age, gender, emotion
# ---------------------------------------------------------------------------
_MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "cv_models"

AGE_BUCKETS = [
    "(0-2)", "(4-6)", "(8-12)", "(15-20)",
    "(25-32)", "(38-43)", "(48-53)", "(60-100)",
]
AGE_MIDPOINTS = [1, 5, 10, 17, 28, 40, 50, 80]
GENDERS = ["Male", "Female"]
EMOTIONS = [
    "neutral", "happy", "surprise", "sad",
    "angry", "disgust", "fear", "contempt",
]

_age_net = None
_gender_net = None
_emotion_net = None


def _load_models():
    global _age_net, _gender_net, _emotion_net
    try:
        age_proto = str(_MODELS_DIR / "age_deploy.prototxt")
        age_model = str(_MODELS_DIR / "age_net.caffemodel")
        gender_proto = str(_MODELS_DIR / "gender_deploy.prototxt")
        gender_model = str(_MODELS_DIR / "gender_net.caffemodel")
        emotion_model = str(_MODELS_DIR / "emotion-ferplus-8.onnx")

        if os.path.exists(age_model) and os.path.getsize(age_model) > 1000:
            _age_net = cv2.dnn.readNet(age_proto, age_model)
        if os.path.exists(gender_model) and os.path.getsize(gender_model) > 1000:
            _gender_net = cv2.dnn.readNet(gender_proto, gender_model)
        if os.path.exists(emotion_model) and os.path.getsize(emotion_model) > 1000:
            _emotion_net = cv2.dnn.readNetFromONNX(emotion_model)

        loaded = sum(1 for n in [_age_net, _gender_net, _emotion_net] if n is not None)
        print(f"[FaceAnalysis] Loaded {loaded}/3 DNN models")
    except Exception as e:
        print(f"[FaceAnalysis] Model loading error: {e}")


_load_models()

MODEL_MEAN = (78.4263377603, 87.7689143744, 114.895847746)


def _predict_age_gender_emotion(img_bgr, x, y, fw, fh):
    """Run age, gender, and emotion prediction on a detected face region."""
    # Pad the face region slightly for better predictions
    pad = int(0.2 * max(fw, fh))
    h, w = img_bgr.shape[:2]
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w, x + fw + pad)
    y2 = min(h, y + fh + pad)
    face_roi = img_bgr[y1:y2, x1:x2]

    if face_roi.size == 0:
        return None, None, None, {}

    gender = None
    age = None
    emotion = None
    emotion_scores = {}

    # Age & Gender use 227x227 blob
    if _age_net or _gender_net:
        blob = cv2.dnn.blobFromImage(
            face_roi, 1.0, (227, 227), MODEL_MEAN, swapRB=False
        )

        if _gender_net:
            _gender_net.setInput(blob)
            preds = _gender_net.forward()
            gender = GENDERS[preds[0].argmax()]

        if _age_net:
            _age_net.setInput(blob)
            preds = _age_net.forward()
            age = AGE_MIDPOINTS[preds[0].argmax()]

    # Emotion uses 64x64 grayscale
    if _emotion_net:
        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        blob = cv2.dnn.blobFromImage(gray_face, 1.0 / 255.0, (64, 64))
        _emotion_net.setInput(blob)
        preds = _emotion_net.forward()
        # Softmax
        exp_preds = np.exp(preds[0] - np.max(preds[0]))
        probs = exp_preds / exp_preds.sum()
        emotion = EMOTIONS[probs.argmax()]
        emotion_scores = {e: round(float(p) * 100, 1) for e, p in zip(EMOTIONS, probs)}

    return gender, age, emotion, emotion_scores


def _compute_image_quality_metrics(image_path: str) -> dict:
    """Compute image quality metrics that indicate professional photography."""
    img = cv2.imread(image_path)
    if img is None:
        return {}

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness_std = float(np.std(gray))
    brightness_mean = float(np.mean(gray))

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation_mean = float(np.mean(hsv[:, :, 1]))

    mid = w // 2
    left = gray[:, :mid]
    right = cv2.flip(gray[:, mid:mid + left.shape[1]], 1)
    if left.shape == right.shape:
        symmetry = float(np.mean(np.abs(left.astype(float) - right.astype(float))))
    else:
        symmetry = 999

    return {
        "resolution": (w, h),
        "sharpness": laplacian_var,
        "brightness_std": brightness_std,
        "brightness_mean": brightness_mean,
        "saturation_mean": saturation_mean,
        "symmetry_diff": symmetry,
    }


def _analyze_face(image_path: str) -> FaceAnalysisResult:
    signals: list[str] = []
    risk = 50

    img = cv2.imread(image_path)
    if img is None:
        signals.append("Could not read image")
        return FaceAnalysisResult(suspicious_signals=signals, risk_score=50)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )

    num_faces = len(faces)

    if num_faces == 0:
        signals.append("No face detected in image")
        faces_lenient = face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30)
        )
        if len(faces_lenient) > 0:
            signals.append(f"Possible face(s) detected with lower confidence ({len(faces_lenient)})")
            num_faces = len(faces_lenient)
            faces = faces_lenient
        else:
            return FaceAnalysisResult(
                faces_detected=0,
                suspicious_signals=signals,
                risk_score=50,
            )

    signals.append(f"{num_faces} face(s) detected")

    x, y, fw, fh = faces[0]
    face_area_ratio = (fw * fh) / (w * h)

    metrics = _compute_image_quality_metrics(image_path)

    # --- Age / Gender / Emotion via OpenCV DNN ---
    gender, age, dominant_emotion, emotion_scores = _predict_age_gender_emotion(
        img, x, y, fw, fh
    )

    if age and gender:
        signals.append(f"Estimated: {gender}, age ~{age}")

    happy_score = emotion_scores.get("happy", 0)

    # --- Scoring signals ---

    if num_faces == 1:
        risk += 5
        face_cx = x + fw / 2
        face_cy = y + fh / 2
        center_offset_x = abs(face_cx - w / 2) / w
        center_offset_y = abs(face_cy - h / 2) / h
        if center_offset_x < 0.15 and center_offset_y < 0.2:
            signals.append("Face is centered -- common in profile/stock photos")
            risk += 10
    elif num_faces > 1:
        signals.append("Multiple faces -- less likely a catfish profile photo")
        risk -= 10

    if face_area_ratio > 0.15:
        signals.append(f"Face occupies {face_area_ratio:.0%} of image -- close-up portrait")
        risk += 5

    if fw > 300 and fh > 300:
        signals.append(f"High-resolution face region ({fw}x{fh}px)")
        risk += 5

    if metrics:
        res_w, res_h = metrics["resolution"]

        if metrics["sharpness"] > 500:
            signals.append(f"Very sharp image (score: {metrics['sharpness']:.0f})")
            risk += 5

        if metrics["brightness_std"] < 40:
            signals.append("Uniform lighting detected -- possible studio photo")
            risk += 10

        if metrics["saturation_mean"] > 130:
            signals.append(f"High color saturation ({metrics['saturation_mean']:.0f}) -- may be filtered/enhanced")
            risk += 5

        if metrics["symmetry_diff"] < 15:
            signals.append("High facial symmetry -- possible AI-generated or professional")
            risk += 10

        if res_w >= 2000 or res_h >= 2000:
            signals.append(f"High resolution: {res_w}x{res_h}")

    if happy_score > 60:
        signals.append(f"Very high 'happy' expression ({happy_score:.0f}%) -- common in stock photos")
        risk += 15

    face_confidence = None
    if dominant_emotion:
        face_confidence = round(max(emotion_scores.values()) / 100.0, 3) if emotion_scores else None

    return FaceAnalysisResult(
        faces_detected=num_faces,
        dominant_emotion=dominant_emotion,
        estimated_age=age,
        gender=gender,
        is_high_quality=metrics.get("sharpness", 0) > 500,
        face_confidence=face_confidence,
        suspicious_signals=signals,
        risk_score=min(100, max(0, risk)),
    )


async def analyze_face(image_path: str) -> FaceAnalysisResult:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_analyze_face, image_path))
