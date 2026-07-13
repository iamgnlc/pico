from epd_2in13 import EPD_2in13_V4_Landscape
from text_render import big_text, text_height, fit_scale


# ---- user config -----------------------------------------------------------
# Lines of text to display (one entry per line).
LINES       = ["GIANLUCA", "&", "GINTARE"]

# Character size multiplier. Each character is 8x8 at scale=1.
TEXT_SCALE  = 4

# Extra vertical pixels between lines.
LINE_GAP    = 10

# False = black text on white background.
# True  = white text on black background.
INVERT      = False
# ---------------------------------------------------------------------------

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

    heights = [text_height(s, scale) for s in LINES]
    block_h = sum(heights) + LINE_GAP * (len(LINES) - 1)
    y       = Y_OFFSET + (CANVAS_H - block_h) // 2

    for s, h in zip(LINES, heights):
        text_w = 8 * len(s) * scale
        x = (CANVAS_W - text_w) // 2
        big_text(epd, s, x, y, fg, scale)
        y += h + LINE_GAP

    epd.display(epd.buffer)
