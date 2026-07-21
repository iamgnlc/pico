from sh1107 import OLED, WIDTH, HEIGHT
import text_render
import bootstrap
from views import weather
import time

REFRESH_SECONDS = 600
ROTATE = True


def _show_error(oled, msg):
    oled.fill(0)
    text_render.text(oled, "error:", 4, 8, 1)
    chunk = 16
    for i in range(3):
        seg = msg[i * chunk:(i + 1) * chunk]
        if not seg:
            break
        text_render.text(oled, seg, 4, 24 + i * 10, 1)
    oled.show()


def _refresh(oled):
    data = bootstrap.fetch_weather()
    weather.set_data(data["temp"], data["code"], data["is_day"])
    weather.render(oled)


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)
    weather.render(oled)

    try:
        _refresh(oled)
    except Exception as e:
        _show_error(oled, str(e))

    next_refresh = time.ticks_add(time.ticks_ms(), REFRESH_SECONDS * 1000)
    while True:
        if time.ticks_diff(next_refresh, time.ticks_ms()) <= 0:
            try:
                _refresh(oled)
            except Exception as e:
                _show_error(oled, str(e))
            next_refresh = time.ticks_add(time.ticks_ms(), REFRESH_SECONDS * 1000)
        time.sleep_ms(500)
