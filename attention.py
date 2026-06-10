from dataclasses import dataclass
from typing import Optional

from config import DISTRACTED_THRESHOLD_SEC, SNAPSHOT_INTERVAL_SEC
from pose import HeadPose


@dataclass
class AttentionState:
    distracted_seconds: float = 0.0
    is_focused: bool = True
    last_pose: Optional[HeadPose] = None
    face_detected: bool = False

    def update(
        self,
        pose: Optional[HeadPose],
        interval_sec: float = SNAPSHOT_INTERVAL_SEC,
    ) -> bool:
        """Update state and return True if alarm should start."""
        self.last_pose = pose
        self.face_detected = pose is not None

        if pose is None:
            self.is_focused = False
            self.distracted_seconds += interval_sec
            return self.distracted_seconds >= DISTRACTED_THRESHOLD_SEC

        self.is_focused = pose.is_focused()
        if self.is_focused:
            self.distracted_seconds = 0.0
            return False

        self.distracted_seconds += interval_sec
        return self.distracted_seconds >= DISTRACTED_THRESHOLD_SEC

    def should_ring(self) -> bool:
        return not self.is_focused and self.distracted_seconds >= DISTRACTED_THRESHOLD_SEC

    def reset(self) -> None:
        self.distracted_seconds = 0.0
        self.is_focused = True
