from sh1107 import WIDTH, HEIGHT
import text_render
import icons

_data = None


_CODE_LABELS = (
    ((0, 1), "Clear"),
    ((2), "Partly Cloudy"),
    ((3,), "Overcast"),
    ((45, 48), "Fog"),
    ((51, 53, 55, 56, 57), "Drizzle"),
    ((61, 63, 65, 66, 67), "Rain"),
    ((71, 73, 75, 77, 85, 86), "Snow"),
    ((80, 81, 82), "Showers"),
    ((95, 96, 99), "Storm"),
)


def _label(code):
    for codes, name in _CODE_LABELS:
        if code in codes:
            return name
    return "code {}".format(code)


def set_data(temp, code, is_day):
    global _data
    _data = (temp, code, is_day)


def _center(oled, s, y, scale=1):
    w = 8 * len(s) * scale
    text_render.text(oled, s, (WIDTH - w) // 2, y, scale)


def render(oled):
    oled.fill(0)
    if _data is None:
        _center(oled, "connecting...", HEIGHT // 2 - 4)
        oled.show()
        return
    temp, code, is_day = _data
    icons.draw(oled, 4, 4, code, is_day)

    num_s = "{:.0f}".format(temp)
    scale = 2
    num_w = 8 * len(num_s) * scale
    deg_r = 3
    gap = 2
    total_w = num_w + gap + (deg_r * 2 + 1)

    x = WIDTH - total_w - 4
    y = 12
    text_render.text(oled, num_s, x, y, scale)
    oled.ellipse(x + num_w + gap + deg_r, y + deg_r, deg_r, deg_r, 1, False)

    _center(oled, _label(code), HEIGHT - 12)
    oled.show()
