from sh1107 import OLED, WIDTH, HEIGHT
import wifi
import weather
import icons
import text_render
import weather_view
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


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)
    while True:
        weather_view.render(oled)
        time.sleep(REFRESH_SECONDS)
