from clipart import CLIPART, clipart_size, draw_clipart
from text_render import big_text, text_height, text_width


def _tokenize(s, clipart_gap):
    # Tokens are one of:
    #   ("text", str)         literal text
    #   ("clipart", name)     a matched :name: sprite
    #   ("gap", pixels)       fixed gap between two clipart tokens
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
    # Whitespace-only text sandwiched between two cliparts collapses to a
    # fixed-width gap. Without this, ":heart: :heart:" would insert a full
    # space-glyph's worth of blank between the sprites.
    for k in range(1, len(tokens) - 1):
        kind, value = tokens[k]
        if (kind == "text" and not value.strip()
                and tokens[k - 1][0] == "clipart"
                and tokens[k + 1][0] == "clipart"):
            tokens[k] = ("gap", clipart_gap)
    return tokens


def _token_size(tok, scale, font):
    kind, value = tok
    if kind == "clipart":
        return clipart_size(value, scale)
    if kind == "gap":
        return value, 0
    if not value.strip():
        # Whitespace-only text contributes its natural width but no height,
        # so it doesn't inflate line heights next to shorter sprites.
        return text_width(value, scale, font), 0
    return text_width(value, scale, font), text_height(value, scale, font)


def render_block(fb, lines, font, scale, color,
                 x, y, w, h, line_gap, clipart_gap):
    """Vertically centre a stack of lines within the (x, y, w, h) box and
    horizontally centre each line. `lines` is a list of strings that may
    contain :clipart_name: tokens."""
    laid = []
    for s in lines:
        tokens = _tokenize(s, clipart_gap)
        sizes = [_token_size(t, scale, font) for t in tokens]
        lw = sum(sw for sw, _ in sizes)
        lh = max((sh for _, sh in sizes), default=0)
        laid.append((tokens, sizes, lw, lh))

    block_h = sum(lh for _, _, _, lh in laid) + line_gap * (len(lines) - 1)
    yy = y + (h - block_h) // 2
    for tokens, sizes, lw, lh in laid:
        xx = x + (w - lw) // 2
        for tok, (sw, _) in zip(tokens, sizes):
            kind, value = tok
            if kind == "clipart":
                draw_clipart(fb, value, xx, yy, color, scale)
            elif kind == "text":
                big_text(fb, value, xx, yy, color, scale, font)
            # "gap" draws nothing
            xx += sw
        yy += lh + line_gap
