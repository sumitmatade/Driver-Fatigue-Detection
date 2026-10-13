import sys
import time


class Alarm:
    """Plays a beep with a cooldown so it does not spam."""

    def __init__(self, cooldown_s: float = 2.0):
        self.cooldown_s = cooldown_s
        self._last = 0.0

    def trigger(self) -> None:
        now = time.time()
        if now - self._last < self.cooldown_s:
            return
        self._last = now
        try:
            import winsound  # Windows only
            winsound.Beep(1800, 400)
        except ImportError:
            sys.stdout.write("\a")  # terminal bell on Linux/macOS
            sys.stdout.flush()
