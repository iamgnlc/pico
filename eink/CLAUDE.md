# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MicroPython for a **Raspberry Pi Pico** driving a **Waveshare 2.13" e-ink** panel (250×122, SSD1680 controller, SPI). Landscape orientation. Pinout is fixed by the HAT: RST=GP12, DC=GP8, CS=GP9, BUSY=GP13, SPI bus 1.

## Running

No build step. Copy the `.py` files to the Pico and run `main.py`:

- `mpremote cp *.py :` then `mpremote run main.py`
- Or open in Thonny with the Pico selected and press Run

There are no host-side tests. The one useful host-side check is running the tokenizer against sample inputs with regular `python3` (framebuf is MicroPython-only, so the drawing code can't be exercised off-device).

## Architecture

Five modules, layered:

1. `epd_2in13.py` — Waveshare vendor driver. Contains both `EPD_2in13_V4_Portrait` and `EPD_2in13_V4_Landscape`; the app uses **Landscape**. Both subclass `framebuf.FrameBuffer`, so callers inherit `text()`, `fill()`, `fill_rect()`, `pixel()`, etc. `display(buffer)` pushes to the panel with a full refresh; `displayPartial()` is available but unused.
2. `text_render.py` — scales the built-in 8×8 framebuf font by pixel expansion (`fill_rect(scale, scale)` per source pixel). Key detail: `text_height()` and `big_text()` measure and draw against the **top of the actual ink**, not the top of the 8-row cell. This is what makes multi-line layouts have consistent gaps regardless of which letters are used.
3. `clipart.py` — MONO_HLSB sprite bitmaps in a `CLIPART` dict keyed by name. Sprites can be any `(w, h)` — heart is 16×12, others are 8×8. Same ink-top alignment semantics as `text_render.big_text` (see `_BOUNDS`, computed once at import). Adding a sprite is a pure data change to `CLIPART`; no other module edits required.
4. `config.py` — user tunables (`LINES`, `TEXT_SCALE`, `LINE_GAP`, `CLIPART_GAP`, `INVERT`). `main.py` imports these names directly.
5. `main.py` — glue. Contains the `:name:` tokenizer, per-line width/height math, and the vertical-centering loop that drives one `epd.display()`.

### Line rendering pipeline (in `main.py`)

Each string in `LINES` is tokenized into `("text", str)` / `("clipart", name)` tokens. A `:name:` becomes a clipart token **only if** `name in CLIPART`; unmatched colons are treated as literal text. This is why the tokenizer imports `CLIPART` from `clipart.py`.

Whitespace-only text sandwiched between two clipart tokens is treated as a `CLIPART_GAP`-pixel spacer instead of its natural `8 * len * scale` width, so `":heart: :heart:"` renders tight. This adjustment lives in `is_clipart_gap()` in `main.py`.

Line height = max ink height across tokens. Whitespace-only text contributes 0 to height so it doesn't inflate lines beside shorter sprites.

## Non-obvious gotchas

- **Visible framebuffer y-range is `6..127`, not `0..121`.** The panel is 122 rows physically but Waveshare's driver pads the short axis to 128 for byte-alignment. The 6 padded rows sit at the top (`y = 0..5`) and are off-glass. Layout code in `main.py` accounts for this via `Y_OFFSET = 128 - CANVAS_H = 6`. If you compute new y coordinates, use `Y_OFFSET + …`, never a bare offset from 0.
- **`main.py` intentionally skips `epd.Clear()`.** Clear does an extra white-flash refresh before content. A single `epd.display(epd.buffer)` after `epd.fill(bg)` is enough. Do not add `Clear()` back "for safety" — it's slower and uglier.
- **Border Waveform register `0x3C` is set at runtime.** `epd.init()` sets it to `0x05` (white), but `main.py` overrides it right after init so the physical inactive border around the glass matches `INVERT`. Don't move this write to before `init()`.
- **Text scaling is not general.** `big_text` only handles the 8×8 framebuf font at integer scale via pixel expansion. There is no anti-aliasing and no font metadata beyond ink-bounds detection.
- **`clipart_size` returns *trimmed* height** (matches `text_height` semantics). Full-cell height is `w * scale, h * scale`; the trimmed height is what's used for line-gap math.
