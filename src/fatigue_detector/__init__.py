from .metrics import eye_aspect_ratio, mouth_aspect_ratio

__all__ = ["eye_aspect_ratio", "mouth_aspect_ratio", "FatigueDetector", "FatigueState"]


def __getattr__(name):
    # Lazy import so the math helpers work (and tests run) without OpenCV/MediaPipe installed
    if name in ("FatigueDetector", "FatigueState"):
        from . import detector
        return getattr(detector, name)
    raise AttributeError(name)
