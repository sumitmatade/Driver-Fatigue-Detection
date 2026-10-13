"""Run the live driver fatigue detector.  Press s to save a screenshot, q to quit."""
import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).parent / "src"))
from fatigue_detector import FatigueDetector  # noqa: E402
from fatigue_detector.alarm import Alarm  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Driver fatigue detection")
    ap.add_argument("--source", default="0",
                    help="Webcam index (0), video file path, or RTSP URL")
    ap.add_argument("--ear", type=float, default=0.21, help="Eye closed threshold")
    ap.add_argument("--mar", type=float, default=0.65, help="Yawn threshold")
    ap.add_argument("--closed-seconds", type=float, default=1.5)
    ap.add_argument("--no-alarm", action="store_true")
    args = ap.parse_args()

    src = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        sys.exit(f"Cannot open video source: {args.source}")

    det = FatigueDetector(ear_thresh=args.ear, mar_thresh=args.mar,
                          closed_seconds=args.closed_seconds)
    alarm = Alarm()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        st = det.process(frame)

        color = (0, 0, 255) if st.drowsy else (0, 200, 0)
        lines = [f"EAR {st.ear:.2f}  MAR {st.mar:.2f}  Pitch {st.pitch:.0f}",
                 f"PERCLOS {st.perclos:.0%}  Yawns {st.yawns}"]
        if not st.face_found:
            lines = ["No face detected"]
        for i, t in enumerate(lines):
            cv2.putText(frame, t, (10, 28 + 26 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        if st.drowsy:
            cv2.putText(frame, "DROWSY: " + ", ".join(st.reasons), (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            if not args.no_alarm:
                alarm.trigger()

        cv2.imshow("Driver Fatigue Detection", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("s"):  # save a screenshot for the README
            out = Path(__file__).parent / "docs" / "screenshots"
            out.mkdir(parents=True, exist_ok=True)
            name = "alert.png" if st.drowsy else "normal.png"
            cv2.imwrite(str(out / name), frame)
            print("Saved", out / name)
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
