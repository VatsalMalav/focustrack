from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from config import CAMERA_INDEX, SNAPSHOTS_DIR
from pose import HeadPose

STATUS_COLORS = {
    "FOCUSED": (0, 200, 0),
    "DISTRACTED": (0, 0, 220),
    "NO_FACE": (0, 165, 255),
    "CAMERA_ERROR": (128, 128, 128),
}


def capture_snapshot() -> Optional[np.ndarray]:
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        return None

    for _ in range(3):
        cap.read()

    success, frame = cap.read()
    cap.release()

    if not success or frame is None:
        return None

    return frame


def save_labeled_snapshot(
    frame: np.ndarray,
    status: str,
    pose: Optional[HeadPose],
    distracted_seconds: float = 0.0,
    alarm_active: bool = False,
) -> str:
    """Save a labeled snapshot for later analysis. Returns the saved file path."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    captured_at = datetime.now()
    filename = captured_at.strftime("%Y%m%d_%H%M%S") + f"_{status}.jpg"
    output_path = SNAPSHOTS_DIR / filename

    labeled = frame.copy()
    _draw_label(
        labeled,
        status=status,
        pose=pose,
        distracted_seconds=distracted_seconds,
        alarm_active=alarm_active,
        captured_at=captured_at,
    )
    cv2.imwrite(str(output_path), labeled)
    return str(output_path)


def _draw_label(
    frame: np.ndarray,
    status: str,
    pose: Optional[HeadPose],
    distracted_seconds: float,
    alarm_active: bool,
    captured_at: datetime,
) -> None:
    color = STATUS_COLORS.get(status, (255, 255, 255))
    lines = [
        f"Status: {status}",
        f"Time: {captured_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if pose is not None:
        lines.append(f"Yaw: {pose.yaw:+.1f}  Pitch: {pose.pitch:+.1f}  Roll: {pose.roll:+.1f}")
    else:
        lines.append("Pose: no face detected")

    if status == "DISTRACTED":
        lines.append(f"Distracted for: {distracted_seconds:.0f}s")

    lines.append(f"Alarm: {'ON' if alarm_active else 'OFF'}")

    x, y = 12, 28
    line_height = 28
    padding = 8

    text_width = 0
    for line in lines:
        size, _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        text_width = max(text_width, size[0])

    box_height = len(lines) * line_height + padding * 2
    box_width = text_width + padding * 2
    cv2.rectangle(frame, (x - padding, y - 22), (x + box_width, y - 22 + box_height), (0, 0, 0), -1)

    for i, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (x, y + i * line_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color if i == 0 else (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
