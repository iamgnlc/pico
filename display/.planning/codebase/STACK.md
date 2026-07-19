# Technology Stack

**Analysis Date:** 2026-07-19

## Languages

**Primary:**
- MicroPython 1.x - Embedded Python dialect for microcontrollers; runs on Raspberry Pi Pico W firmware

## Runtime

**Environment:**
- Raspberry Pi Pico W (RP2040 dual-core ARM Cortex-M0+) with MicroPython firmware
- MicroPython firmware (latest stable recommended)

**Package Manager:**
- None - MicroPython uses direct file copying via `mpremote` or IDE integration (Thonny)
- Deployment: `mpremote cp sh1107.py main.py bootstrap.py icons.py text_render.py views/ :` copies files to Pico's `/` filesystem
- Lockfile: Not applicable — single `.py` files, no dependency manifest

## Frameworks

**Core:**
- `framebuf` (MicroPython stdlib) - Frame buffer abstraction; `OLED` class (`sh1107.py:17`) subclasses `framebuf.FrameBuffer` to inherit `text()`, `fill()`, `pixel()`, `rect()`, `ellipse()`, `line()`, `vline()`, `hline()`, `fill_rect()` methods
- `machine` (MicroPython stdlib) - GPIO and SPI control; `Pin()` for digital I/O (`main.py:92-95`), `SPI()` for serial peripheral interface (`sh1107.py:25`)
- `network` (MicroPython stdlib) - WiFi stack for connecting to 2.4GHz networks via `WLAN` class (`bootstrap.py:7`, `system_view.py:1`)
- `ntptime` (MicroPython stdlib) - NTP time synchronization (`clock_view.py:1`, `clock_view.py:70`)
- `time` (MicroPython stdlib) - Sleep, timing, tick-based scheduling (`sh1107.py:4`, `bootstrap.py:2`, throughout `main.py`)

**API/HTTP:**
- `urequests` (MicroPython HTTP client) - HTTP requests for remote APIs (`bootstrap.py:3`, `bootstrap.py:40`, `bootstrap.py:49`)

**Display/Graphics:**
- `micropython` (stdlib) - `const()` for compile-time constants on performance-critical values (`sh1107.py:2`, `sh1107.py:7-14`)

## Key Dependencies

**Critical:**
- `framebuf` - OLED rendering depends on `MONO_HMSB` format (`sh1107.py:30`); format switch to `MONO_VLSB` will scramble pixel layout and render incorrectly
- `machine.SPI` - SPI bus 1 at 20 MHz (`sh1107.py:25`); hardware constraint requires CS toggling per-byte for correct GDDRAM latching (`sh1107.py:86-90`)
- `urequests` - HTTP client for two external APIs: `ip-api.com/json/` and `api.open-meteo.com/v1/forecast` (`bootstrap.py:40`, `bootstrap.py:49`)

**Infrastructure:**
- `network.WLAN` - Maintains WiFi connection state; `bootstrap.py:6-15` polls connection status with 1s retry loop (up to 20s timeout), `system_view.py:45-46` queries SSID and signal strength (RSSI)
- `ntptime` - Requires active network connection to set system time; `clock_view.py:70` called on 60s retry cadence until success, then 6h re-sync (see `_SYNC_MS` and `_RETRY_MS` in `clock_view.py:12-13`)

## Configuration

**Environment:**
- WiFi credentials: `secrets.py` (gitignored; user must create with `WIFI_SSID` and `WIFI_PASSWORD`)
- Fallback: `main.py:37-46` catches `ImportError` if `secrets.py` is missing and displays "missing secrets.py" on the OLED

**Runtime Tuning:**
- `REFRESH_SECONDS = 600` - Weather data fetch cadence in seconds (converted to 600,000ms in `weather_view.py:12`)
- `ROTATE = True/False` - Whether to flip display 180° via pixel-level rotation (`main.py:10`, `sh1107.py:66-76`)
- `_POLL_MS = 100` - Main event loop tick interval (`main.py:14`)
- `_DEBOUNCE_MS = 50` - Button press debounce threshold (`main.py:15`)
- `_REFRESH_MS = 600_000` - Weather refresh window (normal case) (`weather_view.py:12`)
- `_RETRY_MS = 60_000` - Weather refresh window (when cache status is not "ok") (`weather_view.py:13`)
- NTP sync: `_SYNC_MS = 21_600_000` (6 hours) after first success, `_RETRY_MS = 60_000` (60s) until first success (`clock_view.py:12-13`)

**Storage:**
- `tz_offset.txt` - Single-file cache for timezone offset persisted after first successful `ip-api.com` fetch (`clock_view.py:14`, `clock_view.py:20-24`); reduces flash wear by only writing on offset changes (`clock_view.py:33-48`)

## Hardware Configuration

**Display Controller:**
- SH1107 OLED (128×64, SPI)
- Fixed pinout (Waveshare HAT): DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1
- SPI clock: 20 MHz, polarity 0, phase 0
- Framebuffer: 1024 bytes (128 × 64 ÷ 8 bits/byte), `MONO_HMSB` format
- Display offset: 0x60 (96) — causes wrap in GDDRAM region where physical rows 0-31 show GDDRAM 96-127, and physical rows 32-63 show GDDRAM 0-31

**HAT Buttons:**
- KEY0 (GPIO 15): Previous view carousel button (`main.py:16`)
- KEY1 (GPIO 17): Next view carousel button (`main.py:17`)
- Both: Active-low with pull-up, debounced in software via shared 50ms window

## Platform Requirements

**Development:**
- Raspberry Pi Pico W with MicroPython firmware installed
- USB cable for `mpremote` access or Thonny IDE
- Waveshare Pico-OLED-1.3 HAT (128×64 SH1107 SPI)
- WiFi network (2.4GHz) with SSID and password for weather/time features
- `secrets.py` containing `WIFI_SSID` and `WIFI_PASSWORD` (created by developer)

**Production:**
- Raspberry Pi Pico W + Pico-OLED-1.3 HAT running MicroPython
- WiFi connectivity for weather and clock; system view operational offline

## External Integrations (Summary)

- `ip-api.com/json/?fields=lat,lon,offset,query` — Geolocation and timezone offset (anonymous, no auth)
- `api.open-meteo.com/v1/forecast` — Weather forecast data (anonymous, no auth, no rate-limiting)
- NTP time sync (requires active WiFi)

---

*Stack analysis: 2026-07-19*
