from epd_2in13 import EPD_2in13_V4_Landscape
from text_render import big_text, text_height, fit_scale
from clipart import draw_clipart, clipart_size, CLIPART

# -------------------------------------------------------
# User config for the eink display.

# Lines of text to display (one entry per line).
# ":name:" tokens draw the corresponding clipart from clipart.py.
LINES       = ["GIANLUCA", ":heart: :heart: :heart:", "GINTARE"]

# Character size multiplier. Each character is 8x8 at scale=1.
TEXT_SCALE  = 4

# Extra vertical pixels between lines.
LINE_GAP    = 10

# Horizontal pixels between adjacent clipart tokens on the same line.
# Overrides the natural width of whitespace-only text sitting between two
# clipart tokens (which would otherwise be 8*scale — a full char).
CLIPART_GAP = 8

# False = black text on white background.
# True  = white text on black background.
INVERT      = False

# -------------------------------------------------------

# Visible drawing area for the landscape framebuffer.
# The Waveshare driver pads the short axis from 122 -> 128 to align on 8-bit
# byte boundaries, and the 6 padded rows sit at y = 0..5 (off-glass).
# Visible pixels are y = Y_OFFSET .. Y_OFFSET + CANVAS_H - 1.
CANVAS_W    = 250
CANVAS_H    = 122
Y_OFFSET    = 128 - CANVAS_H   # = 6


if __name__=='__main__':
    epd = EPD_2in13_V4_Landscape()
    # Skip epd.Clear() — it would do an extra white-flash refresh before
    # the content refresh. The single display() below is enough to draw
    # the final frame from whatever RAM state the panel powered up in.

    bg = 0x00 if INVERT else 0xFF
    fg = 0xFF if INVERT else 0x00

    # Panel border (physical inactive area around the glass) is controlled
    # by the SSD1680 Border Waveform register (0x3C). init() sets it to
    # 0x05 = white; override so the border always matches the background.
    epd.send_command(0x3C)
    epd.send_data(0x00 if INVERT else 0x05)   # 0x00 = black, 0x05 = white

    epd.fill(bg)

    # Auto-shrink TEXT_SCALE so the widest line fits horizontally AND the
    # full block fits vertically. Only shrinks — never grows past TEXT_SCALE.
    # scale = fit_scale(LINES, LINE_GAP, CANVAS_W, CANVAS_H, TEXT_SCALE)

    # Manual scale.
    scale = TEXT_SCALE

    def tokenize(s):
        # Split s into a list of ("text", str) / ("clipart", name) tokens.
        # ":name:" becomes a clipart token only if name is in CLIPART; any
        # other colon is treated as literal text.
        tokens = []
        i, n = 0, len(s)
        while i < n:
            if s[i] == ":":
                j = s.find(":", i + 1)
                if j != -1 and s[i + 1:j] in CLIPART:
                    tokens.append(("clipart", s[i + 1:j]))
                    i = j + 1
                    continue
            start = i
            i += 1
            while i < n:
                if s[i] == ":":
                    j = s.find(":", i + 1)
                    if j != -1 and s[i + 1:j] in CLIPART:
                        break
                i += 1
            tokens.append(("text", s[start:i]))
        return tokens

    def is_clipart_gap(tokens, i):
        # Whitespace-only text sandwiched between two clipart tokens.
        kind, value = tokens[i]
        if kind != "text" or value.strip():
            return False
        return (0 < i < len(tokens) - 1
                and tokens[i - 1][0] == "clipart"
                and tokens[i + 1][0] == "clipart")

    def token_width(tokens, i):
        kind, value = tokens[i]
        if kind == "clipart":
            return clipart_size(value, scale)[0]
        if is_clipart_gap(tokens, i):
            return CLIPART_GAP
        return 8 * len(value) * scale

    def token_height(kind, value):
        if kind == "clipart":
            return clipart_size(value, scale)[1]
        # Whitespace-only text contributes no ink height.
        return text_height(value, scale) if value.strip() else 0

    def line_dims(s):
        tokens = tokenize(s)
        w = sum(token_width(tokens, i) for i in range(len(tokens)))
        h = max((token_height(k, v) for k, v in tokens), default=0)
        return w, h

    def draw_line(fb, s, x, y, color):
        tokens = tokenize(s)
        cx = x
        for i, (kind, value) in enumerate(tokens):
            if kind == "clipart":
                draw_clipart(fb, value, cx, y, color, scale)
            elif not is_clipart_gap(tokens, i):
                big_text(fb, value, cx, y, color, scale)
            cx += token_width(tokens, i)

    dims    = [line_dims(s) for s in LINES]
    block_h = sum(h for _, h in dims) + LINE_GAP * (len(LINES) - 1)
    y       = Y_OFFSET + (CANVAS_H - block_h) // 2

    for s, (w, h) in zip(LINES, dims):
        x = (CANVAS_W - w) // 2
        draw_line(epd, s, x, y, fg)
        y += h + LINE_GAP

    epd.display(epd.buffer)
