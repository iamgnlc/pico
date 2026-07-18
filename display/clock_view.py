import ntptime
import time
import text_render
from sh1107 import WIDTH


_synced = False
_last_render_min = -1
_last_sync_ms = 0
_cached_tz_offset = None

_SYNC_MS = 21_600_000  # 6h re-sync cadence after first success (CLOCK-04, D-35 updated 2026-07-18)
_RETRY_MS = 60_000     # 60s retry cadence until first success (D-36)
_TZ_OFFSET_FILE = "tz_offset.txt"

# Load persisted TZ offset at module import so subsequent boots have a good
# offset before the first weather fetch of the new session completes.
# Failure (missing, malformed) leaves _cached_tz_offset as None; the next
# weather fetch's ip-api offset will populate + persist it.
try:
    with open(_TZ_OFFSET_FILE) as f:
        _cached_tz_offset = int(f.read().strip())
except Exception:
    _cached_tz_offset = None


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def set_tz_offset(offset):
    # Public setter called by weather_view.refresh after each successful
    # weather fetch. Flash-wear guard: only writes when the fetched offset
    # differs from the cached value. Stationary device with no DST writes
    # the file once ever (first fetch of first-ever boot).
    global _cached_tz_offset
    if offset is None:
        return
    if offset == _cached_tz_offset:
        return
    _cached_tz_offset = offset
    try:
        with open(_TZ_OFFSET_FILE, "w") as f:
            f.write(str(offset))
    except Exception:
        pass


def should_tick(now_ms):
    if _synced and _cached_tz_offset is not None:
        return time.localtime(time.time() + _cached_tz_offset)[4] != _last_render_min
    # Degraded state: repaint --:-- exactly once (sentinel _last_render_min == -1
    # means "we already rendered --:--", so no repeat repaints).
    return _last_render_min != -1


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
    oled.fill(0)
    if _synced and _cached_tz_offset is not None:
        t = time.localtime(time.time() + _cached_tz_offset)
        s = "{:02d}:{:02d}".format(t[3], t[4])
        _last_render_min = t[4]
    else:
        s = "--:--"
        _last_render_min = -1
    _center_text(oled, s, WIDTH // 2, 27, scale=3)
