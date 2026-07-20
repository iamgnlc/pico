from sh1107 import WIDTH, HEIGHT
import icons
import text_render
import time


_cached_temp = None
_cached_code = None
_cached_is_day = None
_cache_status = "pending"

_REFRESH_MS = 600_000   # WEATHER-03 cadence (matches REFRESH_SECONDS = 600)
_RETRY_MS = 60_000      # WEATHER-09 fast-retry cadence when _cache_status != "ok"
_last_refresh_ms = 0


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def should_refresh(now_ms):
    interval = _REFRESH_MS if _cache_status == "ok" else _RETRY_MS
    return time.ticks_diff(now_ms, _last_refresh_ms) >= interval


def render(oled):
    oled.fill(0)
    if _cache_status == "pending":
        _center_text(oled, "connecting...", WIDTH // 2, 32)
    elif _cache_status == "no_wifi":
        _center_text(oled, "no wifi", WIDTH // 2, 32)
    elif _cache_status == "no_data":
        _center_text(oled, "no data", WIDTH // 2, 32)
    elif _cache_status == "ok" or _cache_status == "stale":
        icons.draw(oled, 16, 16, _cached_code, _cached_is_day)
        t = "{:.0f}".format(_cached_temp)
        _center_text(oled, t, 88, 32, scale=2)
        w = 8 * len(t) * 2
        cx = 88 + w // 2 + 5
        cy = 32 - 8 + 2
        oled.ellipse(cx, cy, 2, 2, 1, False)


# Pure state-setter driven by main._refresh_all; no render, no cross-view calls.
def set_data(ip, temp, code, is_day):
    global _cached_temp, _cached_code, _cached_is_day, _cache_status, _last_refresh_ms
    # Stamp at start so transient failures don't tight-loop the scheduler —
    # a failed fetch still consumes one _REFRESH_MS window before the next try.
    _last_refresh_ms = time.ticks_ms()

    if not ip:
        _cache_status = "no_wifi"
        return
    # Preserve last-good cache on transient fetch failure — flip to "stale"
    # only if we have something to fall back on; "no_data" if the cache is cold.
    if temp is None:
        _cache_status = "no_data" if _cached_temp is None else "stale"
        return

    _cached_temp = temp
    _cached_code = code
    _cached_is_day = is_day
    _cache_status = "ok"
