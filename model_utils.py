import urllib.request
from pathlib import Path

from config import FACE_MODEL_PATH, FACE_MODEL_URL, MODELS_DIR


def ensure_face_model() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if FACE_MODEL_PATH.exists():
        return FACE_MODEL_PATH

    print(f"Downloading face model to {FACE_MODEL_PATH} ...")
    urllib.request.urlretrieve(FACE_MODEL_URL, FACE_MODEL_PATH)
    print("Face model ready.")
    return FACE_MODEL_PATH
