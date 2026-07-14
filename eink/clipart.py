import framebuf


# MONO_HLSB bitmaps as (width, height, bytes). Each row is ceil(width/8)
# bytes, MSB = leftmost pixel. Sizes can differ per sprite; the text font
# is 8x8, so 8x8 clipart aligns naturally with it.
CLIPART = {
    "heart": (16, 12, bytes((
        0b01100110,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00011000,
        0b00000000,
        0b00000000,
    ))),
    "star": (8, 8, bytes((
        0b00010000,
        0b00111000,
        0b11111110,
        0b01111100,
        0b00111000,
        0b01101100,
        0b01000100,
        0b00000000,
    ))),
    "smiley": (8, 8, bytes((
        0b00111100,
        0b01000010,
        0b10100101,
        0b10000001,
        0b10100101,
        0b10011001,
        0b01000010,
        0b00111100,
    ))),
    "flower": (8, 8, bytes((
        0b00011000,
        0b00111100,
        0b11011011,
        0b11111111,
        0b11011011,
        0b00111100,
        0b00011000,
        0b00000000,
    ))),
}


def _ink_bounds(w, h, data):
    src = framebuf.FrameBuffer(bytearray(data), w, h, framebuf.MONO_HLSB)
    top, bottom = h, -1
    for cy in range(h):
        for cx in range(w):
            if src.pixel(cx, cy):
                if cy < top:
                    top = cy
                bottom = cy
                break
    if bottom < 0:
        top, bottom = 0, h - 1
    return top, bottom


_BOUNDS = {name: _ink_bounds(w, h, d) for name, (w, h, d) in CLIPART.items()}


def draw_clipart(fb, name, x, y, color, scale):
    # Draw CLIPART[name] so (x, y) aligns with the top of the actual ink,
    # matching text_render.big_text semantics.
    w, h, data = CLIPART[name]
    top, _ = _BOUNDS[name]
    src = framebuf.FrameBuffer(bytearray(data), w, h, framebuf.MONO_HLSB)
    for cy in range(h):
        for cx in range(w):
            if src.pixel(cx, cy):
                fb.fill_rect(x + cx * scale,
                             y + (cy - top) * scale,
                             scale, scale, color)


def clipart_size(name, scale):
    # (width, trimmed height) — height matches text_render.text_height.
    w, h, _ = CLIPART[name]
    top, bottom = _BOUNDS[name]
    return w * scale, (bottom - top + 1) * scale
