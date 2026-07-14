from bitmap import pixel, ink_bounds


def _string_bounds(s, font):
    # Ink top/bottom across all glyphs used in s so multi-line layouts
    # align on ink, not on the glyph cell.
    H = font.HEIGHT
    top, bottom = H, -1
    for ch in s:
        w, data = font.get_ch(ch)
        if not w:
            continue
        t, b = ink_bounds(w, H, data)
        if b < 0:
            continue
        if t < top:
            top = t
        if b > bottom:
            bottom = b
    if bottom < 0:
        top, bottom = 0, H - 1
    return top, bottom


def big_text(fb, s, x, y, color, scale, font):
    # Draw s at (x, y) so that y aligns with the top of the actual ink,
    # not the top of the empty glyph cell.
    top, _ = _string_bounds(s, font)
    H = font.HEIGHT
    cx0 = x
    for ch in s:
        w, data = font.get_ch(ch)
        rb = (w + 7) // 8
        for cy in range(H):
            for cx in range(w):
                if pixel(data, rb, cx, cy):
                    fb.fill_rect(cx0 + cx * scale,
                                 y + (cy - top) * scale,
                                 scale, scale, color)
        cx0 += w * scale


def text_width(s, scale, font):
    return sum(font.get_ch(c)[0] for c in s) * scale


def text_height(s, scale, font):
    top, bottom = _string_bounds(s, font)
    return (bottom - top + 1) * scale


def fit_scale(lines, gap, canvas_w, canvas_h, requested, font):
    """Largest integer scale <= requested such that the block of lines
    fits within canvas_w x canvas_h. Never returns less than 1."""
    if not lines:
        return max(1, requested)
    max_w = max((text_width(s, 1, font) for s in lines), default=1) or 1
    w_scale = canvas_w // max_w

    unit_h = sum(text_height(s, 1, font) for s in lines)
    remaining_h = canvas_h - gap * (len(lines) - 1)
    if unit_h <= 0 or remaining_h <= 0:
        h_scale = 1
    else:
        h_scale = remaining_h // unit_h

    return max(1, min(requested, w_scale, h_scale))
