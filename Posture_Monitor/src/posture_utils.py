"""
posture_utils.py
----------------
Utilities for MediaPipe Face-Mesh processing and overlay drawing.
(Posture/Pose logic has been removed in favor of the 20-20-20 rule tracker).
"""

import numpy as np
try:
    from mediapipe.solutions import face_mesh
except ImportError:
    from mediapipe.python.solutions import face_mesh

_mp_face_mesh = face_mesh

def create_face_mesh(
    max_faces: int = 1,
    refine_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> face_mesh.FaceMesh:
    """
    Instantiate and return a MediaPipe FaceMesh object.
    """
    return _mp_face_mesh.FaceMesh(
        max_num_faces=max_faces,
        refine_landmarks=refine_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )


def get_face_bbox(landmarks, image_width: int, image_height: int):
    """
    Compute the axis-aligned bounding box of all face landmarks.

    Returns
    -------
    tuple (x_min, y_min, x_max, y_max) in pixel coordinates,
    or None if no landmarks.
    """
    if landmarks is None:
        return None

    xs = [lm.x * image_width  for lm in landmarks.landmark]
    ys = [lm.y * image_height for lm in landmarks.landmark]

    return (
        int(min(xs)), int(min(ys)),
        int(max(xs)), int(max(ys)),
    )


def draw_face_overlay(
    frame: np.ndarray,
    landmarks,
    image_width: int,
    image_height: int,
    status: str,
) -> np.ndarray:
    """
    Draw bounding box on the frame for visual feedback.
    """
    import cv2

    if landmarks is None:
        return frame

    color = (0, 200, 0) if status == "good" else (0, 0, 220)

    # Bounding box
    bbox = get_face_bbox(landmarks, image_width, image_height)
    if bbox:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)

    return frame
