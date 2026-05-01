"""
distance_utils.py
-----------------
Estimates the user's face-to-screen distance using a simple
pinhole-camera (focal-length) model.

Formula:
    distance = (KNOWN_FACE_WIDTH * FOCAL_LENGTH) / bounding_box_pixel_width

Calibration constant FOCAL_LENGTH is derived once from a reference measurement:
    FOCAL_LENGTH = (ref_pixel_width * ref_distance_cm) / KNOWN_FACE_WIDTH
"""

import numpy as np

# ── Anthropometric constant ──────────────────────────────────────────────────
# Average adult face width ~14 cm (inter-cheekbone).
KNOWN_FACE_WIDTH_CM: float = 14.0

# ── Default focal length (pixels) ────────────────────────────────────────────
# Pre-computed from a typical 1280×720 webcam at 60 cm where the face
# bounding-box was ~180 px wide:
#   FL = (180 * 60) / 14  ≈ 771
DEFAULT_FOCAL_LENGTH: float = 771.0


def estimate_distance(
    face_pixel_width: float,
    focal_length: float = DEFAULT_FOCAL_LENGTH,
    known_face_width: float = KNOWN_FACE_WIDTH_CM,
) -> float:
    """
    Estimate the distance (cm) between the webcam and the user's face.

    Parameters
    ----------
    face_pixel_width : float
        Width of the face bounding box in pixels (from the detector).
    focal_length : float
        Focal length in pixel units (calibrated or default).
    known_face_width : float
        Real-world face width in cm.

    Returns
    -------
    float
        Estimated distance in centimetres, or -1.0 if input is invalid.
    """
    if face_pixel_width <= 0:
        return -1.0  # sentinel: no face detected

    distance_cm = (known_face_width * focal_length) / face_pixel_width
    return round(distance_cm, 1)


def calibrate_focal_length(
    ref_pixel_width: float,
    ref_distance_cm: float,
    known_face_width: float = KNOWN_FACE_WIDTH_CM,
) -> float:
    """
    Compute a personalised focal length from a single reference measurement.

    Parameters
    ----------
    ref_pixel_width  : Face bounding-box width (px) at the reference distance.
    ref_distance_cm  : Actual distance (cm) during calibration.
    known_face_width : Real-world face width (cm).

    Returns
    -------
    float
        Calibrated focal length in pixels.
    """
    if ref_pixel_width <= 0 or ref_distance_cm <= 0:
        return DEFAULT_FOCAL_LENGTH
    return (ref_pixel_width * ref_distance_cm) / known_face_width


def distance_status(
    distance_cm: float,
    min_safe_cm: float = 45.0,
    max_safe_cm: float = 90.0,
) -> str:
    """
    Classify the distance into one of three ergonomic zones.

    Returns
    -------
    str  : "too_close" | "too_far" | "good"
    """
    if distance_cm < 0:
        return "unknown"
    if distance_cm < min_safe_cm:
        return "too_close"
    if distance_cm > max_safe_cm:
        return "too_far"
    return "good"
