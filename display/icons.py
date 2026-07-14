def _kind(code, is_day):
    if code in (0, 1):
        return "sun" if is_day else "moon"
    if code in (2, 3):
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (95, 96, 99):
        return "thunder"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    return "cloud"


def _sun(fb, x, y):
    cx, cy = x + 16, y + 16
    for dx, dy in ((0, -14), (0, 14), (-14, 0), (14, 0),
                   (-10, -10), (10, -10), (-10, 10), (10, 10)):
        fb.line(cx + dx * 2 // 3, cy + dy * 2 // 3, cx + dx, cy + dy, 1)
    fb.ellipse(cx, cy, 5, 5, 1, True)


def _moon(fb, x, y):
    cx, cy = x + 16, y + 16
    fb.ellipse(cx, cy, 10, 10, 1, True)
    fb.ellipse(cx + 5, cy - 2, 9, 9, 0, True)


def _cloud(fb, x, y):
    fb.ellipse(x + 10, y + 18, 6, 5, 1, True)
    fb.ellipse(x + 16, y + 14, 8, 7, 1, True)
    fb.ellipse(x + 22, y + 18, 6, 5, 1, True)
    fb.fill_rect(x + 8, y + 18, 16, 5, 1)


def _rain(fb, x, y):
    _cloud(fb, x, y - 4)
    for dx in (10, 16, 22):
        fb.vline(x + dx, y + 22, 5, 1)


def _snow(fb, x, y):
    _cloud(fb, x, y - 4)
    for dx in (10, 16, 22):
        fb.fill_rect(x + dx - 1, y + 24, 3, 3, 1)


def _thunder(fb, x, y):
    _cloud(fb, x, y - 4)
    fb.line(x + 18, y + 21, x + 13, y + 27, 1)
    fb.line(x + 13, y + 27, x + 19, y + 27, 1)
    fb.line(x + 19, y + 27, x + 14, y + 31, 1)


def _fog(fb, x, y):
    for dy in (10, 16, 22, 28):
        fb.hline(x + 4, y + dy, 24, 1)


_DRAWERS = {
    "sun": _sun,
    "moon": _moon,
    "cloud": _cloud,
    "rain": _rain,
    "snow": _snow,
    "thunder": _thunder,
    "fog": _fog,
}


def draw(fb, x, y, code, is_day):
    _DRAWERS[_kind(code, is_day)](fb, x, y)
