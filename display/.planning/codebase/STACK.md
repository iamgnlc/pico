# Technology Stack

**Analysis Date:** 2026-07-15

## Languages

**Primary:**
- MicroPython 1.x - Embedded Python dialect for microcontrollers, runs on Raspberry Pi Pico W firmware

## Runtime

**Environment:**
- Raspberry Pi Pico W (RP2040 dual-core ARM Cortex-M0+)
- MicroPython firmware (latest stable recommended)

**Package Manager:**
- None - MicroPython uses direct file copying via `mpremote` or IDE integration (Thonny)
- Lockfile: Not applicable

**Deployment:**
- `mpremote cp sh1107.py main.py :` copies files to Pico's `/` filesystem
- Files execute directly on-device; no build process required

## Frameworks

**Core Display:**
- `framebuf` (MicroPython stdlib) - Frame buffer abstraction; `OLED` class subclasses `framebuf.FrameBuffer` to inherit `text()`, `fill()`, `pixel()`, `rect()`, `ellipse()`, `line()`, `vline()`, `hline()` methods (`sh1107.py:17`)

**Networking:**
- `network` (MicroPython stdlib) - WiFi stack for connecting to 2.4GHz networks via `WLAN` class (`wifi.py:2`)

**Hardware Control:**
- `machine` (MicroPython stdlib) - GPIO and SPI control; `Pin()` for digital I/O, `SPI()` for serial peripheral interface (`sh1107.py:1`)

**HTTP Client:**
- `urequests` (MicroPython stdlib equivalent) - HTTP client for API calls (`weather.py:1`)

**Utilities:**
- `time` (MicroPython stdlib) - Sleep and timing (`sh1107.py:4`, `wifi.py:2`, `main.py:6`)
- `micropython` (stdlib) - `const()` for compile-time constants (`sh1107.py:2`)

## Key Dependencies

**Critical (Firmware-level):**
- `framebuf` module - OLED rendering depends on `MONO_HMSB` format (`sh1107.py:30`); format switch to `MONO_VLSB` will scramble pixel layout
- `machine.SPI` - SPI bus 1 at 20 MHz (`sh1107.py:25`); hardware constraint requires CS toggling per-byte for correct GDDRAM latching (`sh1107.py:83-90`)

**Utilities:**
- `urequests` - HTTP requests to `ip-api.com` and `api.open-meteo.com` (`weather.py:6, 13`)

## Hardware Pinout (Fixed by HAT)

The Waveshare Pico-OLED-1.3 HAT plugs directly onto the Pico header. Pinout is non-configurable:

| Signal | GPIO | Purpose |
|--------|------|---------|
| DC (Data/Command) | GP8 | SPI command vs. data mode selector |
| CS (Chip Select) | GP9 | SPI chip select (toggled per-byte in `show()`) |
| SCK (Clock) | GP10 | SPI clock line |
| MOSI (Data Out) | GP11 | SPI data to panel |
| RST (Reset) | GP12 | Panel reset (active low) |
| SPI Bus | 1 | Primary SPI bus |

Constants defined in `sh1107.py:7-11`.

## Display Specifications

| Property | Value |
|----------|-------|
| Controller | SH1107 (128×64 OLED) |
| Resolution | 128 pixels wide × 64 pixels tall |
| Interface | SPI (not I2C) |
| Framebuffer Size | 1024 bytes (128 × 64 ÷ 8 bits/byte) |
| Buffer Format | MONO_HMSB (horizontal byte packing, MSB first) |
| SPI Clock | 20 MHz |
| SPI Mode | Polarity 0, Phase 0 |

## Configuration

**User Configuration (main.py:8-12):**
- `WIFI_SSID` - Network name to connect to
- `WIFI_PASSWORD` - Network password (WARNING: hardcoded in main.py)
- `REFRESH_SECONDS` - Weather update interval (default 600s = 10 min)
- `ROTATE` - Boolean; `True` flips display 180° via pixel-level rotation in `show()` (`sh1107.py:66-76`)

**Panel Initialization Sequence (sh1107.py:44-62):**
- Display offset `0x60` (96): causes wrap in GDDRAM region; physical rows 0-31 show GDDRAM 96-127; physical rows 32-63 show GDDRAM 0-31
- Contrast: `0x6F` (hardcoded)
- Memory addressing mode: vertical (`0x21` — single-byte command, no argument follows)
- Pre-charge period: `0x22`
- DC-DC converter: enabled (`0x8A`)

**Rotation Constraint:**
Rotation must be done at framebuffer-pixel level (`sh1107.py:70-73`), not by byte-shuffling, because the display offset wrap breaks byte-level transforms. Hardware rotation (segment remap `0xA1`, COM scan `0xC8`) is disabled and will break the display if re-enabled.

## Development Workflow

**Deploy & Run:**
1. Connect Pico via USB
2. `mpremote cp sh1107.py main.py icons.py text_render.py weather.py wifi.py :`
3. `mpremote run main.py` (or use Thonny: select Pico, open file, press Run)

**Debug Reference:**
Compare to Waveshare's official reference: [`waveshare/Pico_code Pico-OLED-1.3(spi).py`](https://github.com/waveshare/Pico_code/blob/main/Python/Pico-OLED-1.3/Pico-OLED-1.3(spi).py) to isolate driver bugs from hardware issues.

---

*Stack analysis: 2026-07-15*
