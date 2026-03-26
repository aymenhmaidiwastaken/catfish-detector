"""Download pre-trained models for face analysis (age, gender, emotion)."""

import os
import sys
import urllib.request

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models", "cv_models")

MODELS = {
    "age_net.caffemodel": {
        "url": "https://www.dropbox.com/s/xfb20y596869vbb/age_net.caffemodel?dl=1",
        "size_mb": 43.5,
    },
    "gender_net.caffemodel": {
        "url": "https://www.dropbox.com/s/iyv483wz7ztr9gh/gender_net.caffemodel?dl=1",
        "size_mb": 43.5,
    },
    "emotion-ferplus-8.onnx": {
        "url": "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx",
        "size_mb": 33.4,
    },
}


def download():
    os.makedirs(MODELS_DIR, exist_ok=True)

    for name, info in MODELS.items():
        path = os.path.join(MODELS_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            print(f"  {name} already exists, skipping")
            continue

        print(f"  Downloading {name} ({info['size_mb']:.1f} MB)...")
        try:
            urllib.request.urlretrieve(info["url"], path)
            size = os.path.getsize(path) / 1_048_576
            print(f"  Done ({size:.1f} MB)")
        except Exception as e:
            print(f"  Failed: {e}", file=sys.stderr)
            sys.exit(1)

    print("\nAll models ready.")


if __name__ == "__main__":
    print("Downloading face analysis models...\n")
    download()
