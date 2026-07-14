def pixel(data, rb, x, y):
    return data[y * rb + (x >> 3)] & (0x80 >> (x & 7))


def ink_bounds(w, h, data):
    """First/last rows that contain ink in a MONO_HLSB bitmap.
    Returns (h, -1) when the bitmap is empty."""
    rb = (w + 7) // 8
    top, bottom = h, -1
    for cy in range(h):
        for cx in range(w):
            if pixel(data, rb, cx, cy):
                if cy < top:
                    top = cy
                if cy > bottom:
                    bottom = cy
                break
    return top, bottom
