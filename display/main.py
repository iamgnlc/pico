from sh1107 import OLED, WIDTH, HEIGHT
import wifi
import weather
import icons
import text_render
import time

# ---- user config -----------------------------------------------------------
REFRESH_SECONDS = 600      # how often to refresh the weather
ROTATE          = True     # True = flip display 180°
# ---------------------------------------------------------------------------


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


try:
    import secrets
except ImportError:
    oled = OLED(rotate=ROTATE)
    oled.fill(0)
    _center_text(oled, "missing", WIDTH // 2, HEIGHT // 3)
    _center_text(oled, "secrets.py", WIDTH // 2, 2 * HEIGHT // 3)
    oled.show()
    while True:
        time.sleep(3600)


def _render(oled):
    oled.fill(0)
    ip = wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    if not ip:
        _center_text(oled, "no wifi", WIDTH // 2, HEIGHT // 2)
    else:
        temp, code, is_day = weather.current()
        if temp is None:
            _center_text(oled, "no data", WIDTH // 2, HEIGHT // 2)
        else:
            icons.draw(oled, 16, 16, code, is_day)
            t = "{:.0f}".format(temp)
            _center_text(oled, t, 88, HEIGHT // 2, scale=2)
            w = 8 * len(t) * 2
            cx = 88 + w // 2 + 5
            cy = HEIGHT // 2 - 8 + 2
            oled.ellipse(cx, cy, 2, 2, 1, False)
    oled.show()


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)
    while True:
        _render(oled)
        time.sleep(REFRESH_SECONDS)
