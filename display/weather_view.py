from sh1107 import WIDTH, HEIGHT
import wifi
import weather
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
_spinner_frame = 0


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def _draw_spinner(oled):
    # Small hollow ring near the temperature anchor with a rotating single-pixel
    # indicator. Ring center (88, 20). 4-frame rotation via _spinner_frame % 4.
    # Note: this draws over the "connecting..." text region briefly during fetch —
    # planner-permitted interpretation of D-23. If visual overlap looks bad on-device,
    # move the ring center to (108, 20).
    global _spinner_frame
    oled.ellipse(88, 20, 4, 4, 1, False)
    offsets = ((0, -4), (4, 0), (0, 4), (-4, 0))
    dx, dy = offsets[_spinner_frame % 4]
    oled.pixel(88 + dx, 20 + dy, 1)
    _spinner_frame += 1


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
    else:
        icons.draw(oled, 16, 16, _cached_code, _cached_is_day)
        t = "{:.0f}".format(_cached_temp)
        _center_text(oled, t, 88, 32, scale=2)
        w = 8 * len(t) * 2
        cx = 88 + w // 2 + 5
        cy = 32 - 8 + 2
        oled.ellipse(cx, cy, 2, 2, 1, False)


def refresh(oled):
    global _cached_temp, _cached_code, _cached_is_day, _cache_status, _last_refresh_ms
    # Stamp at start so transient failures don't tight-loop the scheduler —
    # a failed fetch still consumes one _REFRESH_MS window before the next try.
    _last_refresh_ms = time.ticks_ms()

    # Lazy import: secrets.py absence is caught by main.py's fallback block,
    # which halts before refresh() is ever called. Importing at module load
    # would fire ImportError during `import weather_view` in main.py — before
    # the fallback screen renders — and drop to REPL instead.
    import secrets

    ip = wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    if not ip:
        _cache_status = "no_wifi"
        render(oled)
        return

    # Draw a spinner frame BEFORE the blocking urequests.get() so the user sees
    # fetch progress — but ONLY when we already have weather data to update
    # (cache is "ok"). During the initial boot fetch, cache_status is "pending"
    # and the panel is showing "connecting..." — overlaying a spinner there is
    # visual noise the operator explicitly opted out of. D-23's "at least one
    # frame during the fetch phase" is preserved for the 600s background refresh
    # path, which is where spinner-as-activity-indicator carries useful signal.
    if _cache_status == "ok":
        render(oled)
        _draw_spinner(oled)
        oled.show()

    temp, code, is_day = weather.current()
    if temp is None:
        _cache_status = "no_data"
        render(oled)
        return

    _cached_temp = temp
    _cached_code = code
    _cached_is_day = is_day
    _cache_status = "ok"
    render(oled)
