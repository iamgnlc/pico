from sh1107 import WIDTH, HEIGHT
import wifi
import weather
import icons
import text_render


_cached_temp = None
_cached_code = None
_cached_is_day = None
_cache_status = "pending"


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def render(oled):
    oled.fill(0)
    if _cache_status == "pending":
        _center_text(oled, "connecting...", WIDTH // 2, 26)
    elif _cache_status == "no_wifi":
        _center_text(oled, "no wifi", WIDTH // 2, 26)
    elif _cache_status == "no_data":
        _center_text(oled, "no data", WIDTH // 2, 26)
    else:
        icons.draw(oled, 16, 16, _cached_code, _cached_is_day)
        t = "{:.0f}".format(_cached_temp)
        _center_text(oled, t, 88, 26, scale=2)
        w = 8 * len(t) * 2
        cx = 88 + w // 2 + 5
        cy = 26 - 8 + 2
        oled.ellipse(cx, cy, 2, 2, 1, False)


def refresh(oled):
    global _cached_temp, _cached_code, _cached_is_day, _cache_status
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
