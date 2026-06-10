from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
ASSETS_DIR = BASE_DIR / "assets"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"

SNAPSHOT_INTERVAL_SEC = 5
DISTRACTED_THRESHOLD_SEC = 2

# Safe zone (degrees). Screen + keyboard/desk = focused.
YAW_MIN = -20.0
YAW_MAX = 20.0
PITCH_MIN = -190.0
PITCH_MAX = -140.0

CAMERA_INDEX = 0
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
FACE_MODEL_PATH = MODELS_DIR / "face_landmarker.task"
ALARM_SOUND_PATH = ASSETS_DIR / "alarm.wav"
