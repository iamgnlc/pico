from sh1107 import WIDTH, HEIGHT
import wifi
import weather
import icons
import text_render
import secrets


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


def render(oled):
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
