import ntptime
import time
import text_render
from sh1107 import WIDTH


_synced = False
_last_render_min = -1
_last_sync_ms = 0

_SYNC_MS = 3_600_000   # 1h re-sync cadence after first success (CLOCK-04, D-35)
_RETRY_MS = 60_000     # 60s retry cadence until first success (D-36)


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def should_tick(now_ms):
    # Lazy import — main.TZ_OFFSET is not defined at clock_view module-load time
    # (main.py imports clock_view before assigning TZ_OFFSET). Re-importing per
    # call is cheap and guaranteed available once the poll loop is running.
    from main import TZ_OFFSET
    return time.localtime(time.time() + TZ_OFFSET)[4] != _last_render_min


def should_sync(now_ms):
    interval = _SYNC_MS if _synced else _RETRY_MS
    return time.ticks_diff(now_ms, _last_sync_ms) >= interval


def sync(oled):
    global _synced, _last_sync_ms
    # Stamp at start so a failed sync consumes one full retry window instead
    # of tight-looping the scheduler (D-33 pattern preserved from Phase 2.1).
    _last_sync_ms = time.ticks_ms()
    try:
        ntptime.settime()
        _synced = True
    except Exception:
        pass


def render(oled):
    global _last_render_min
    from main import TZ_OFFSET
    oled.fill(0)
    if _synced:
        t = time.localtime(time.time() + TZ_OFFSET)
        s = "{:02d}:{:02d}".format(t[3], t[4])
        _last_render_min = t[4]
    else:
        s = "--:--"
        _last_render_min = -1
    _center_text(oled, s, WIDTH // 2, 27, scale=3)
