import framebuf


def _render_text(s):
    # Render s into an 8-row temp framebuf and return (buf, width, top, bottom)
    # where top/bottom are the first/last rows that actually contain ink.
    w = 8 * len(s)
    tmp_buf = bytearray(((w + 7) // 8) * 8)
    tmp = framebuf.FrameBuffer(tmp_buf, w, 8, framebuf.MONO_HLSB)
    tmp.fill(0)
    tmp.text(s, 0, 0, 1)
    top, bottom = 8, -1
    for cy in range(8):
        for cx in range(w):
            if tmp.pixel(cx, cy):
                if cy < top:
                    top = cy
                bottom = cy
                break
    if bottom < 0:
        top, bottom = 0, 7
    return tmp, w, top, bottom


def big_text(fb, s, x, y, color, scale):
    # Draw s at (x, y) so that y aligns with the top of the actual ink,
    # not the top of the empty 8-row cell.
    tmp, w, top, _ = _render_text(s)
    for cy in range(8):
        for cx in range(w):
            if tmp.pixel(cx, cy):
                fb.fill_rect(x + cx * scale,
                             y + (cy - top) * scale,
                             scale, scale, color)


def text_height(s, scale):
    _, _, top, bottom = _render_text(s)
    return (bottom - top + 1) * scale


def fit_scale(lines, gap, canvas_w, canvas_h, requested):
    """Largest integer scale <= requested such that the block of lines
    fits within canvas_w x canvas_h. Never returns less than 1."""
    if not lines:
        return max(1, requested)
    max_len = max(len(s) for s in lines) or 1
    w_scale = canvas_w // (8 * max_len)

    unit_h = sum(text_height(s, 1) for s in lines)
    remaining_h = canvas_h - gap * (len(lines) - 1)
    if unit_h <= 0 or remaining_h <= 0:
        h_scale = 1
    else:
        h_scale = remaining_h // unit_h

    return max(1, min(requested, w_scale, h_scale))
