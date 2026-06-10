import math
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from mediapipe.tasks.python.core import base_options as base_options_lib
from mediapipe.tasks.python.vision import face_landmarker as face_landmarker_lib
from mediapipe.tasks.python.vision.core import image as mp_image_lib
from mediapipe.tasks.python.vision.core import vision_task_running_mode as running_mode_lib

from config import (
    PITCH_MAX,
    PITCH_MIN,
    YAW_MAX,
    YAW_MIN,
)
from model_utils import ensure_face_model

# MediaPipe landmark indices used for head pose (6-point model).
LANDMARK_NOSE_TIP = 1
LANDMARK_CHIN = 152
LANDMARK_LEFT_EYE = 33
LANDMARK_RIGHT_EYE = 263
LANDMARK_LEFT_MOUTH = 61
LANDMARK_RIGHT_MOUTH = 291
LANDMARK_INDICES = (
    LANDMARK_NOSE_TIP,
    LANDMARK_CHIN,
    LANDMARK_LEFT_EYE,
    LANDMARK_RIGHT_EYE,
    LANDMARK_LEFT_MOUTH,
    LANDMARK_RIGHT_MOUTH,
)

MODEL_POINTS_3D = np.array(
    [
        (0.0, 0.0, 0.0),
        (0.0, -330.0, -65.0),
        (-225.0, 170.0, -135.0),
        (225.0, 170.0, -135.0),
        (-150.0, -150.0, -125.0),
        (150.0, -150.0, -125.0),
    ],
    dtype=np.float64,
)


@dataclass
class HeadPose:
    yaw: float
    pitch: float
    roll: float

    def is_focused(self) -> bool:
        return (
            YAW_MIN <= self.yaw <= YAW_MAX
            and PITCH_MIN <= self.pitch <= PITCH_MAX
        )


class HeadPoseEstimator:
    def __init__(self) -> None:
        model_path = ensure_face_model()
        options = face_landmarker_lib.FaceLandmarkerOptions(
            base_options=base_options_lib.BaseOptions(model_asset_path=str(model_path)),
            running_mode=running_mode_lib.VisionTaskRunningMode.IMAGE,
            num_faces=1,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = face_landmarker_lib.FaceLandmarker.create_from_options(options)

    def close(self) -> None:
        self._landmarker.close()

    def estimate(self, frame_bgr: np.ndarray) -> Optional[HeadPose]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp_image_lib.Image(image_format=mp_image_lib.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        if not result.face_landmarks:
            return None

        pose = _pose_from_solve_pnp(result.face_landmarks[0], frame_bgr.shape)
        if pose is not None:
            return pose

        if result.facial_transformation_matrixes:
            return _pose_from_transform_matrix(result.facial_transformation_matrixes[0])

        return None


def _pose_from_transform_matrix(matrix: np.ndarray) -> HeadPose:
    rotation = matrix[:3, :3]
    yaw, pitch, roll = _decompose_rotation(rotation)
    return HeadPose(yaw=yaw, pitch=pitch, roll=roll)


def _pose_from_solve_pnp(landmarks, shape: tuple[int, ...]) -> Optional[HeadPose]:
    height, width = shape[:2]
    image_points = np.array(
        [
            (landmarks[idx].x * width, landmarks[idx].y * height)
            for idx in LANDMARK_INDICES
        ],
        dtype=np.float64,
    )

    focal_length = float(width)
    center = (width / 2.0, height / 2.0)
    camera_matrix = np.array(
        [
            [focal_length, 0.0, center[0]],
            [0.0, focal_length, center[1]],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rotation_vector, translation_vector = cv2.solvePnP(
        MODEL_POINTS_3D,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    yaw, pitch, roll = _decompose_rotation(rotation_matrix)
    return HeadPose(yaw=yaw, pitch=pitch, roll=roll)


def _decompose_rotation(rotation_matrix: np.ndarray) -> tuple[float, float, float]:
    rotation = np.asarray(rotation_matrix, dtype=np.float64)[:3, :3]
    sy = math.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2)
    if sy >= 1e-6:
        pitch = math.degrees(math.atan2(rotation[2, 1], rotation[2, 2]))
        yaw = math.degrees(math.atan2(-rotation[2, 0], sy))
        roll = math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
    else:
        pitch = math.degrees(math.atan2(-rotation[1, 2], rotation[1, 1]))
        yaw = math.degrees(math.atan2(-rotation[2, 0], sy))
        roll = 0.0
    return _normalize_angles(yaw, pitch, roll)


def _normalize_angles(yaw: float, pitch: float, roll: float) -> tuple[float, float, float]:
    def norm(angle: float) -> float:
        while angle > 180.0:
            angle -= 360.0
        while angle < -180.0:
            angle += 360.0
        return angle

    return norm(yaw), norm(pitch), norm(roll)
