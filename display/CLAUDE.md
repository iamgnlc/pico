# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MicroPython for a **Raspberry Pi Pico W** driving a **Waveshare Pico-OLED-1.3** HAT (128×64, SH1107 controller, SPI). The HAT plugs directly onto the Pico header, so the pinout is fixed and not user-configurable — DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1.

## Running

There is no build step. Copy `sh1107.py` and `main.py` to the Pico's filesystem and run `main.py`. Typical workflows:

- `mpremote cp sh1107.py main.py :` then `mpremote run main.py`
- Or open the files in Thonny with the Pico selected and press Run

Everything runs on-device; there are no host-side tests to run.

## Architecture

Two-file split matching the pattern used by the sibling `../eink/` project:

- `sh1107.py` — driver. `OLED` subclasses `framebuf.FrameBuffer`, so callers get `text()`, `fill()`, `pixel()`, `rect()`, etc. for free. Owns SPI setup, the init sequence, and `show()` which pushes the buffer to the panel.
- `main.py` — user config at the top (`LINES`, `LINE_GAP`, `ROTATE`), then a `__main__` block that centers text and calls `show()`.

## Non-obvious SH1107 gotchas (all learned the hard way)

These are the traps that will burn any future modification to `sh1107.py`. All are documented in code, but the reasoning lives here:

1. **`0x21` is a single-byte command, not command+arg.** On SH1107, `0x20`/`0x21` each encode a full addressing-mode selection (page / vertical). Do not send a value after them — it will be interpreted as the next command and silently break addressing.

2. **CS must toggle around every data byte in `show()`.** A single continuous CS-low burst across the 16-byte column write does not latch correctly into GDDRAM on this panel. This violates typical SPI convention but is required — see Waveshare's reference `write_data()` which does the same.

3. **Rotation must be done at the framebuf-pixel level, not by shuffling buffer bytes.** The init sets a display offset of `0x60` (96), which produces a wrap in the visible GDDRAM region (physical rows 0–31 show GDDRAM 96–127; physical rows 32–63 show GDDRAM 0–31). Because of this wrap, the framebuf-to-panel mapping is not a straightforward linear transform over all 1024 bytes, so a byte-reverse + bit-reverse (which mathematically produces a 180° pixel flip) can move active pixels into the invisible half of the buffer and blank the screen. Rotating via `framebuf.pixel()` reads/writes stays inside coordinates that are guaranteed to display. Hardware rotation (segment remap `0xA1` + COM scan `0xC8`) is also broken because it fights the display-offset wrap; do not re-enable it.

4. **Framebuffer format must be `MONO_HMSB`.** `show()` walks the buffer as 128-wide rows of 16 bytes; `MONO_VLSB` scrambles the bit layout. This matches Waveshare's reference.

## Reference

When debugging the driver, the authoritative comparison is Waveshare's official SPI demo: [`waveshare/Pico_code Pico-OLED-1.3(spi).py`](https://github.com/waveshare/Pico_code/blob/main/Python/Pico-OLED-1.3/Pico-OLED-1.3(spi).py). Drop it in as a self-contained test file to isolate whether a bug is in the local driver or the hardware/config (jumpers, HAT seating, firmware).
