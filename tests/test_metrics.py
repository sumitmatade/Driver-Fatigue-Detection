import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fatigue_detector.metrics import eye_aspect_ratio, mouth_aspect_ratio  # noqa: E402


def test_open_eye_has_high_ear():
    eye = [(0, 0), (1, 1), (3, 1), (4, 0), (3, -1), (1, -1)]
    assert eye_aspect_ratio(eye) > 0.4


def test_closed_eye_has_low_ear():
    eye = [(0, 0), (1, 0.05), (3, 0.05), (4, 0), (3, -0.05), (1, -0.05)]
    assert eye_aspect_ratio(eye) < 0.1


def test_yawn_has_high_mar():
    assert mouth_aspect_ratio((5, 0), (5, 8), (0, 4), (10, 4)) > 0.65


def test_closed_mouth_has_low_mar():
    assert mouth_aspect_ratio((5, 0), (5, 0.5), (0, 0), (10, 0)) < 0.2


def test_zero_width_is_safe():
    assert eye_aspect_ratio([(0, 0)] * 6) == 0.0
    assert mouth_aspect_ratio((0, 0), (0, 1), (0, 0), (0, 0)) == 0.0
