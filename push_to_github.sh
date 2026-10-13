#!/usr/bin/env bash
# Run this on YOUR machine. Needs git. GitHub CLI (gh) is optional but easiest.
set -e
git init -b main
git add .
git commit -m "Initial commit: driver fatigue detection system"
if command -v gh >/dev/null; then
  gh repo create driver-fatigue-detection --public --source=. --remote=origin --push \
    --description "Real-time driver drowsiness detection with OpenCV and MediaPipe"
else
  echo "Create an empty repo named driver-fatigue-detection on github.com, then run:"
  echo "  git remote add origin https://github.com/<your-username>/driver-fatigue-detection.git"
  echo "  git push -u origin main"
fi
