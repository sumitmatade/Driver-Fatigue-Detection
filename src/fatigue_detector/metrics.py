"""Pure math helpers. No camera or MediaPipe needed, so they are easy to test."""
import numpy as np


def _dist(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


def eye_aspect_ratio(eye) -> float:
    """EAR from 6 eye points ordered p1..p6 (Soukupova & Cech, 2016).

    Open eye ~0.25-0.35. Closed eye drops toward 0.
    """
    p1, p2, p3, p4, p5, p6 = eye
    horizontal = _dist(p1, p4)
    if horizontal == 0:
        return 0.0
    return (_dist(p2, p6) + _dist(p3, p5)) / (2.0 * horizontal)


def mouth_aspect_ratio(top, bottom, left, right) -> float:
    """Mouth opening divided by mouth width. A yawn gives a high value."""
    width = _dist(left, right)
    if width == 0:
        return 0.0
    return _dist(top, bottom) / width
