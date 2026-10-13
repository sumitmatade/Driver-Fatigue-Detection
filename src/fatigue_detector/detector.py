"""Core logic: MediaPipe Face Mesh -> EAR / MAR / head pitch -> fatigue state."""
from collections import deque
from dataclasses import dataclass, field
import time

import cv2
import numpy as np
import mediapipe as mp

from .metrics import eye_aspect_ratio, mouth_aspect_ratio

# Face Mesh landmark indices (468-point model)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH_TOP, MOUTH_BOTTOM, MOUTH_LEFT, MOUTH_RIGHT = 13, 14, 78, 308

# 6 points used for head pose: nose, chin, eye corners, mouth corners
POSE_IDS = [1, 152, 263, 33, 291, 61]
# Generic 3D face model (arbitrary units)
POSE_MODEL = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0),
], dtype=np.float64)


@dataclass
class FatigueState:
    face_found: bool = False
    ear: float = 0.0
    mar: float = 0.0
    pitch: float = 0.0
    perclos: float = 0.0
    eyes_closed_s: float = 0.0
    yawns: int = 0
    drowsy: bool = False
    reasons: list = field(default_factory=list)


class FatigueDetector:
    def __init__(self, ear_thresh=0.21, mar_thresh=0.65, closed_seconds=1.5,
                 perclos_thresh=0.30, window_s=60, nod_pitch=-20.0):
        self.ear_thresh = ear_thresh
        self.mar_thresh = mar_thresh
        self.closed_seconds = closed_seconds
        self.perclos_thresh = perclos_thresh
        self.window_s = window_s
        self.nod_pitch = nod_pitch

        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self._history = deque()          # (timestamp, eye_closed_bool)
        self._closed_since = None
        self._yawn_active = False
        self.yawns = 0

    @staticmethod
    def _pts(lm, ids, w, h):
        return [(lm[i].x * w, lm[i].y * h) for i in ids]

    def _pitch(self, lm, w, h):
        img_pts = np.array(self._pts(lm, POSE_IDS, w, h), dtype=np.float64)
        cam = np.array([[w, 0, w / 2], [0, w, h / 2], [0, 0, 1]], dtype=np.float64)
        ok, rvec, _ = cv2.solvePnP(POSE_MODEL, img_pts, cam, np.zeros((4, 1)),
                                   flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return 0.0
        rmat, _ = cv2.Rodrigues(rvec)
        angles, *_ = cv2.RQDecomp3x3(rmat)
        pitch = angles[0]
        # Normalise so a straight-ahead face is near 0
        return pitch - 180 if pitch > 90 else pitch + 180 if pitch < -90 else pitch

    def process(self, frame_bgr) -> FatigueState:
        now = time.time()
        h, w = frame_bgr.shape[:2]
        result = self.mesh.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        st = FatigueState(yawns=self.yawns)
        if not result.multi_face_landmarks:
            self._closed_since = None
            return st

        lm = result.multi_face_landmarks[0].landmark
        st.face_found = True
        st.ear = (eye_aspect_ratio(self._pts(lm, LEFT_EYE, w, h)) +
                  eye_aspect_ratio(self._pts(lm, RIGHT_EYE, w, h))) / 2
        st.mar = mouth_aspect_ratio(*[
            (lm[i].x * w, lm[i].y * h)
            for i in (MOUTH_TOP, MOUTH_BOTTOM, MOUTH_LEFT, MOUTH_RIGHT)])
        st.pitch = self._pitch(lm, w, h)

        # Eye closure duration
        closed = st.ear < self.ear_thresh
        if closed:
            self._closed_since = self._closed_since or now
            st.eyes_closed_s = now - self._closed_since
        else:
            self._closed_since = None

        # PERCLOS: share of time eyes were closed in the rolling window
        self._history.append((now, closed))
        while self._history and now - self._history[0][0] > self.window_s:
            self._history.popleft()
        st.perclos = sum(c for _, c in self._history) / len(self._history)

        # Yawn counter (count once per yawn, not per frame)
        if st.mar > self.mar_thresh and not self._yawn_active:
            self._yawn_active = True
            self.yawns += 1
        elif st.mar <= self.mar_thresh:
            self._yawn_active = False
        st.yawns = self.yawns

        # Decision rules
        if st.eyes_closed_s >= self.closed_seconds:
            st.reasons.append("Eyes closed too long")
        if len(self._history) > 100 and st.perclos >= self.perclos_thresh:
            st.reasons.append("High PERCLOS")
        if st.pitch < self.nod_pitch:
            st.reasons.append("Head nodding")
        if self._yawn_active:
            st.reasons.append("Yawning")
        st.drowsy = bool(st.reasons)
        return st
