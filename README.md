# Driver Fatigue Detection

Real-time drowsiness detection from a webcam or video stream using Python, OpenCV and MediaPipe. It watches the driver's eyes, mouth and head, and raises an alarm when the signs of fatigue appear.

> **Status:** prototype. Thresholds are fixed defaults and not validated on a large dataset. Do not use as a safety system in a real vehicle.

## Demo

<!-- Replace with your own files in docs/screenshots/ -->
![Normal state](docs/screenshots/normal.png)
![Drowsy alert](docs/screenshots/alert.png)

## What it detects

| Signal | How | Triggers alert when |
|---|---|---|
| Eyes closed | Eye Aspect Ratio (EAR) | EAR below 0.21 for 1.5 s or more |
| Slow blinking / heavy eyelids | PERCLOS (share of time eyes are closed in last 60 s) | 30% or more |
| Yawning | Mouth Aspect Ratio (MAR) | MAR above 0.65 (counted once per yawn) |
| Head nodding | Head pitch from `solvePnP` | Pitch below -20 degrees |

## Architecture

```
 Camera / video file / RTSP stream
              |
              v
      OpenCV frame capture            (main.py)
              |
              v
   MediaPipe Face Mesh (468 points)   (detector.py)
              |
     +--------+---------+----------------+
     v        v         v                v
    EAR      MAR     Head pitch      Closure timer
 (metrics.py) (metrics.py) (solvePnP)   + PERCLOS window
     +--------+---------+----------------+
              |
              v
     Rule-based decision -> FatigueState   (detector.py)
              |
      +-------+--------+
      v                v
 On-screen overlay   Alarm (beep, with cooldown)
   (main.py)           (alarm.py)
```

### Project layout

```
driver-fatigue-detection/
├── main.py                      # CLI app: capture, overlay, alarm
├── src/fatigue_detector/
│   ├── metrics.py               # EAR and MAR math (pure functions)
│   ├── detector.py              # Face Mesh + decision rules
│   └── alarm.py                 # Alarm with cooldown
├── tests/test_metrics.py        # Unit tests for the math
├── docs/screenshots/            # Demo images
└── requirements.txt
```

### Design choices

- **Math is separate from the camera code.** `metrics.py` has no OpenCV or MediaPipe dependency, so it is unit tested without a camera.
- **Several signals, not one.** EAR alone fails when the driver blinks normally or wears glasses. Combining closure time, PERCLOS, yawns and head pitch reduces false alarms.
- **Time-based, not frame-based.** Thresholds use seconds, so behaviour does not change with camera FPS.
- **Any video source.** `--source` accepts a webcam index, a video file, or an RTSP URL.

## How to run

Requires Python 3.9 to 3.11 and a webcam.

```bash
git clone https://github.com/<your-username>/driver-fatigue-detection.git
cd driver-fatigue-detection

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py                   # default webcam
```

Options:

```bash
python main.py --source 1                          # second camera
python main.py --source drive.mp4                  # video file
python main.py --source rtsp://user:pass@ip/stream # RTSP camera
python main.py --ear 0.23 --closed-seconds 1.0     # tune thresholds
python main.py --no-alarm                          # silence beep
```

Press `s` to save a screenshot into `docs/screenshots/` (`normal.png` when alert is off, `alert.png` when it is on). Press `q` to quit.

Run tests:

```bash
pytest
```

## Tuning

The defaults will not suit everyone. Face shape, camera angle and glasses change EAR. If you get false alarms, lower `--ear`. If it misses closed eyes, raise it.

## Known limitations

- Fixed thresholds, no per-driver calibration.
- Weak in very low light, with sunglasses, or with the face turned far from the camera.
- Tested on a webcam, not in a moving vehicle.
- Rule-based. No learned model, so no accuracy metric yet.

## My technical contributions

- Built the full pipeline: video capture (webcam, file or RTSP) -> MediaPipe Face Mesh -> fatigue decision -> on-screen alert and alarm.
- Implemented Eye Aspect Ratio and Mouth Aspect Ratio from Face Mesh landmarks as pure, unit-tested functions.
- Combined four signals (eye closure time, PERCLOS, yawn count, head pitch via `solvePnP`) to reduce false alarms from normal blinking.
- Made all thresholds time-based and adjustable from the command line, so behaviour does not depend on camera FPS.
- Added an alarm cooldown and a one-key screenshot tool for documentation.

## Future work

- Per-driver calibration on the first 30 seconds
- Collect labelled data and report precision/recall
- Run on Raspberry Pi / edge device
- Log events to a CSV for analysis

## References

- Soukupova and Cech, "Real-Time Eye Blink Detection using Facial Landmarks", 2016
- MediaPipe Face Mesh

## License

MIT
