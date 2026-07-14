import framebuf


def text(fb, s, x, y, scale=1, color=1):
    if scale == 1:
        fb.text(s, x, y, color)
        return
    tw = 8 * len(s)
    buf = bytearray(((tw + 7) // 8) * 8)
    tmp = framebuf.FrameBuffer(buf, tw, 8, framebuf.MONO_HMSB)
    tmp.text(s, 0, 0, 1)
    for py in range(8):
        for px in range(tw):
            if tmp.pixel(px, py):
                fb.fill_rect(x + px * scale, y + py * scale, scale, scale, color)
