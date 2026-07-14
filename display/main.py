from sh1107 import OLED, WIDTH, HEIGHT

# ---- user config -----------------------------------------------------------
LINES    = ["Hello", "", "GNLC"]
LINE_GAP = 4      # extra pixels between lines
ROTATE   = True  # True = flip display 180°
# ---------------------------------------------------------------------------

CHAR_W = 8
CHAR_H = 8


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)
    oled.fill(0)

    block_h = CHAR_H * len(LINES) + LINE_GAP * (len(LINES) - 1)
    y = (HEIGHT - block_h) // 2

    for line in LINES:
        x = (WIDTH - CHAR_W * len(line)) // 2
        oled.text(line, x, y, 1)
        y += CHAR_H + LINE_GAP

    oled.show()
