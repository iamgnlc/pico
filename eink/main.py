from epd_2in13 import EPD_2in13_V4_Landscape
from layout import render_block

# -------------------------------------------------------
# User config for the eink display.

# Lines of text to display (one entry per line).
# ":name:" tokens draw the corresponding clipart from clipart.py.
LINES       = ["Gianluca", ":heart: :heart: :heart:", "Gintare"]

# Font module under fonts/ — e.g. "arial", "dreambaser". Required.
FONT        = "dreambaser"

# Character size multiplier. Glyphs render at the font's designed height
# at scale=1 and are pixel-expanded from there. Clipart sprites are 32x32
# and internally use half this scale.
TEXT_SCALE  = 2

# Extra vertical pixels between lines.
LINE_GAP    = 10

# Horizontal pixels between adjacent clipart tokens on the same line.
CLIPART_GAP = 12

# False = black text on white background.
# True  = white text on black background.
INVERT      = False

# -------------------------------------------------------

# Visible drawing area for the landscape framebuffer.
# The Waveshare driver pads the short axis from 122 -> 128 to align on 8-bit
# byte boundaries, and the 6 padded rows sit at y = 0..5 (off-glass).
CANVAS_W    = 250
CANVAS_H    = 122
Y_OFFSET    = 128 - CANVAS_H   # = 6


if __name__ == '__main__':
    font = getattr(__import__("fonts." + FONT), FONT)

    epd = EPD_2in13_V4_Landscape()
    # Skip epd.Clear() — it would do an extra white-flash refresh before
    # the content refresh. The single display() below is enough.

    bg, fg = (0x00, 0xFF) if INVERT else (0xFF, 0x00)
    epd.set_border(bg)
    epd.fill(bg)

    render_block(epd, LINES, font, TEXT_SCALE, fg,
                 0, Y_OFFSET, CANVAS_W, CANVAS_H,
                 LINE_GAP, CLIPART_GAP)

    epd.display(epd.buffer)

