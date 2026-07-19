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

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Pico OLED Multi-View**

A MicroPython app for a Raspberry Pi Pico W driving a Waveshare Pico-OLED-1.3 HAT (128×64, SH1107). Two physical buttons on the HAT cycle through a small set of always-on info views — weather, clock, system status — with a page-dot indicator showing position in the carousel.

**Core Value:** Pressing a button changes the view instantly and reliably; each view stays accurate on its own refresh cadence without user intervention.

### Constraints

- **Tech stack**: MicroPython on Pico W — no host-side tooling, no external Python packages beyond what the firmware ships with (`urequests`, `network`, `framebuf`, `machine`, `time`, `ntptime`).
- **Hardware**: Waveshare Pico-OLED-1.3 HAT — pinout fixed; only 128×64 monochrome.
- **Memory**: Pico W has ~264 KB SRAM; the framebuffer is 1024 bytes and must stay reusable — no per-frame allocations in the render loop.
- **Rendering**: SH1107 driver quirks documented in `CLAUDE.md` — any changes to `sh1107.py` must preserve the four gotchas.
- **Networking**: Weather/clock views assume WiFi; System view must remain usable when offline.
- **Security**: `secrets.py` must be gitignored; example file (`secrets.py.example`) may be committed.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- MicroPython 1.x - Embedded Python dialect for microcontrollers, runs on Raspberry Pi Pico W firmware

## Runtime

- Raspberry Pi Pico W (RP2040 dual-core ARM Cortex-M0+)
- MicroPython firmware (latest stable recommended)
- None - MicroPython uses direct file copying via `mpremote` or IDE integration (Thonny)
- Lockfile: Not applicable
- `mpremote cp sh1107.py main.py :` copies files to Pico's `/` filesystem
- Files execute directly on-device; no build process required

## Frameworks

- `framebuf` (MicroPython stdlib) - Frame buffer abstraction; `OLED` class subclasses `framebuf.FrameBuffer` to inherit `text()`, `fill()`, `pixel()`, `rect()`, `ellipse()`, `line()`, `vline()`, `hline()` methods (`sh1107.py:17`)
- `network` (MicroPython stdlib) - WiFi stack for connecting to 2.4GHz networks via `WLAN` class (`bootstrap.py:1`)
- `machine` (MicroPython stdlib) - GPIO and SPI control; `Pin()` for digital I/O, `SPI()` for serial peripheral interface (`sh1107.py:1`)
- `urequests` (MicroPython stdlib equivalent) - HTTP client for API calls (`bootstrap.py:3`)
- `time` (MicroPython stdlib) - Sleep and timing (`sh1107.py:4`, `bootstrap.py:2`, `main.py:6`)
- `micropython` (stdlib) - `const()` for compile-time constants (`sh1107.py:2`)

## Key Dependencies

- `framebuf` module - OLED rendering depends on `MONO_HMSB` format (`sh1107.py:30`); format switch to `MONO_VLSB` will scramble pixel layout
- `machine.SPI` - SPI bus 1 at 20 MHz (`sh1107.py:25`); hardware constraint requires CS toggling per-byte for correct GDDRAM latching (`sh1107.py:83-90`)
- `urequests` - HTTP requests to `ip-api.com` and `api.open-meteo.com` (`bootstrap.py`, inside `fetch()`)

## Hardware Pinout (Fixed by HAT)

| Signal | GPIO | Purpose |
|--------|------|---------|
| DC (Data/Command) | GP8 | SPI command vs. data mode selector |
| CS (Chip Select) | GP9 | SPI chip select (toggled per-byte in `show()`) |
| SCK (Clock) | GP10 | SPI clock line |
| MOSI (Data Out) | GP11 | SPI data to panel |
| RST (Reset) | GP12 | Panel reset (active low) |
| SPI Bus | 1 | Primary SPI bus |

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

- `WIFI_SSID` - Network name to connect to (in gitignored `secrets.py`)
- `WIFI_PASSWORD` - Network password (in gitignored `secrets.py`)
- `REFRESH_SECONDS` - Weather update interval (default 600s = 10 min)
- `ROTATE` - Boolean; `True` flips display 180° via pixel-level rotation in `show()` (`sh1107.py:66-76`)
- Display offset `0x60` (96): causes wrap in GDDRAM region; physical rows 0-31 show GDDRAM 96-127; physical rows 32-63 show GDDRAM 0-31
- Contrast: `0x6F` (hardcoded)
- Memory addressing mode: vertical (`0x21` — single-byte command, no argument follows)
- Pre-charge period: `0x22`
- DC-DC converter: enabled (`0x8A`)

## Development Workflow

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Module names use `snake_case`: `sh1107.py`, `text_render.py`, `bootstrap.py`, `icons.py`, `main.py`, plus the view modules `views/weather_view.py`, `views/clock_view.py`, `views/system_view.py`
- No file extensions beyond `.py`
- Use `snake_case` for all functions: `_center_text()`, `_render()`, `connect()`, `current()`
- Private/internal functions prefixed with single underscore: `_init()`, `_cmd()`, `_kind()`, `_sun()`, `_moon()`, `_cloud()`, `_rain()`, `_snow()`, `_thunder()`, `_fog()`, `_center_text()`, `_render()`
- Public functions have no prefix: `draw()`, `text()`, `connect()`, `current()`
- Use `snake_case` for all variables: `WIFI_SSID`, `REFRESH_SECONDS`, `x_center`, `y_center`, `temp`, `code`, `is_day`
- Lowercase for local variables: `w`, `h`, `buf`, `rot_buf`, `col`, `byte`, `dx`, `dy`, `cx`, `cy`
- Use `PascalCase` for class names: `OLED` (subclasses `framebuf.FrameBuffer`)
- Module-level constants use `UPPER_SNAKE_CASE`: `WIDTH`, `HEIGHT`, `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`
- Private module constants prefixed with underscore: `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`

## Code Style

- No explicit formatter configured (typical MicroPython idiom)
- 4-space indentation (observed throughout)
- Line breaks used sparingly; some method calls chained inline: `self.rst(1); time.sleep_ms(1)`
- String concatenation via `.format()` for readability: `"{:.0f}C".format(temp)`
- No linter detected; code assumes MicroPython interpreter compatibility
- MicroPython idiom: no type hints anywhere in codebase
- Uses `micropython.const()` for compile-time constants on performance-critical values: `_DC = const(8)`

## Import Organization

- `sh1107.py`: `from machine import Pin, SPI` → `from micropython import const` → `import framebuf` → `import time`
- `main.py`: `from sh1107 import OLED, WIDTH, HEIGHT` → `from machine import Pin` → `from views import weather_view, clock_view, system_view` → `import text_render` → `import bootstrap` → `import time`
- `text_render.py`: `import framebuf`
- `bootstrap.py`: `import network` → `import time` → `import urequests`
- `views/weather_view.py`: `from sh1107 import WIDTH, HEIGHT` → `import icons` → `import text_render` → `import time`

## Error Handling

- Bare `except Exception:` blocks for network/API calls where graceful degradation is needed
- Example in `bootstrap.py`: `except Exception: return ip, None, None, None, None, None` (WiFi-ok-but-API-fail; the `ip` argument preserves the ability to distinguish `no_wifi` from `no_data` in the caller)
- Example in `main.py`: checks for `None` return values to display fallback UI ("no wifi", "no data")
- No explicit error logging; failures are silent with UI fallback

## Logging

- Console output via print not used; state communicated via UI display
- Debug happens via Thonny or `mpremote` execution observation

## Comments

- Inline comments placed near hardware/protocol traps: "SH1107 needs CS toggled around every data byte" in `sh1107.py:83-84`
- Comments for non-obvious control flow: "SPI first, DC after — GP8 is SPI1's default MISO" in `sh1107.py:22-24`
- Comments for register initialization explaining bit semantics: "display off", "column addr", "page addr" inline in init sequence in `sh1107.py:45-61`
- No docstrings anywhere (MicroPython idiom for embedded/performance-critical code)
- Comments summarize intent, not implementation
- Not used; MicroPython does not use type annotations or docstring generation

## Function Design

- Small, focused functions: `_center_text()` is 3 lines, `_render()` is 13 lines
- Drawing functions are typically 2–5 lines of ellipse/line/rect calls
- Private helper functions extracted: `_kind()` maps weather code to icon type before lookup
- Positional parameters used; no keyword defaults except in public APIs
- Example: `text(fb, s, x, y, scale=1, color=1)` in `text_render.py:4`
- Internal helpers use positional-only: `_center_text(oled, s, x_center, y_center, scale=1)`
- Functions return None implicitly (no return statement) when mutating state: `show()`, `_cmd()`, `draw()`
- Functions return computed values: `current()` returns tuple `(temp, code, is_day)` or `(None, None, None)`
- Single-purpose functions return a single value or None

## Module Design

- `sh1107.py` exports: `OLED` class, `WIDTH` const, `HEIGHT` const
- `main.py` exports: `__main__` block (entry point)
- `text_render.py` exports: `text()` function (imported in main)
- `weather.py` exports: `current()` function (imported in main)
- `wifi.py` exports: `connect()` function (imported in main)
- `icons.py` exports: `draw()` function (imported in main)
- Not used; each module has a single purpose and no re-export pattern
- User config constants placed at top of `main.py` (lines 8–12): `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`
- Hardware pins defined at top of `sh1107.py` (lines 6–14): `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`, `WIDTH`, `HEIGHT`
- Hardware constants use `const()` for MicroPython optimization
- This placement allows editing without modifying function bodies
- `OLED` subclasses `framebuf.FrameBuffer` (line 17 in `sh1107.py`) to inherit `text()`, `fill()`, `pixel()`, `rect()`, `line()`, `ellipse()`, `fill_rect()`, `hline()`, `vline()` methods
- Callers in `main.py` and `icons.py` use these methods directly on the `OLED` instance or temporary `FrameBuffer` objects
- Example: `text_render.py` creates a temporary `FrameBuffer` to render text at scale, then reads pixels and renders them scaled on the target framebuffer

## Code Patterns

- Rotation implemented via pixel-level read/write (framebuf method calls) not buffer-byte manipulation
- Explained in `sh1107.py:66-73`: iterate over all pixels, if set, write to rotated coordinates in new buffer
- This avoids the GDDRAM wrap issue documented in CLAUDE.md
- Register sequence in `sh1107.py:44-63` grouped by function (display control, addressing, contrast, etc.)
- Single-byte commands like `0x21` are not followed by data bytes (hardware limitation documented in CLAUDE.md)
- Reset toggle with explicit timing: `rst(1)` → sleep 1ms → `rst(0)` → sleep 10ms → `rst(1)` → sleep 10ms
- `icons.py` uses a dictionary `_DRAWERS` mapping kind names to drawing functions (lines 62–70)
- `draw()` function maps weather code to kind via `_kind()`, then looks up function and calls it
- Clean separation: code-to-kind logic separate from rendering

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| OLED Driver | Hardware initialization, SPI comms, framebuffer→GDDRAM transfer, power management | `sh1107.py` |
| Application | User configuration, UI rendering loop, composition-root fetch fan-out (`_refresh_all`) | `main.py` |
| Bootstrap | WiFi connect + ip-api geolocation (lat/lon/offset/query) + Open-Meteo weather, JSON parsing, unified 6-tuple return | `bootstrap.py` |
| Icons | Weather condition → visual rendering (sun/moon/cloud/rain/snow/thunder/fog) | `icons.py` |
| Text Render | Font scaling via double-buffer framebuf technique | `text_render.py` |

## Pattern Overview

- Single-file driver (`sh1107.py`) decoupled from app logic via `framebuf.FrameBuffer` subclassing
- Framebuffer-first design — all drawing operations happen in-memory first, then pushed to hardware via `show()`
- No state persistence or complex inter-module dependencies
- Flat namespace (no packages) suitable for embedded constraint

## Layers

- Purpose: Abstract Raspberry Pi Pico SPI hardware and SH1107 OLED controller protocol
- Location: `sh1107.py`
- Contains: OLED class, SPI pin configuration, init sequence, `show()` method, power control
- Depends on: `machine.Pin`, `machine.SPI`, `framebuf`, `time` (MicroPython stdlib)
- Used by: `main.py` and any user code needing display output
- Purpose: User-facing configuration, rendering orchestration, refresh loop
- Location: `main.py`
- Contains: User config constants (`WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`), `_render()` orchestrator, `__main__` entry point
- Depends on: `sh1107.OLED`, `wifi`, `weather`, `icons`, `text_render`
- Used by: MicroPython runtime (executed as main entry point)
- Purpose: Network connection and IP acquisition
- Location: `wifi.py`
- Contains: `connect(ssid, password, timeout)` function
- Depends on: `network`, `time` (MicroPython stdlib)
- Used by: `main.py._render()`
- Purpose: Fetch current weather data from remote APIs
- Location: `weather.py`
- Contains: `current()` function that queries IP geolocation then weather forecast
- Depends on: `urequests` (MicroPython HTTP library)
- Used by: `main.py._render()`
- Purpose: Draw weather condition icons using framebuffer primitives
- Location: `icons.py`
- Contains: WMO weather code → icon type mapping, 7 rendering functions (sun/moon/cloud/rain/snow/thunder/fog), dispatcher
- Depends on: `framebuf` (via caller-supplied framebuffer)
- Used by: `main.py._render()` for icon drawing at screen coordinates
- Purpose: Scaled font rendering (native 1x only available in framebuf)
- Location: `text_render.py`
- Contains: `text(fb, s, x, y, scale, color)` function using double-buffer technique
- Depends on: `framebuf` (via caller-supplied framebuffer)
- Used by: `main.py._center_text()` for temperature display

## Data Flow

### Primary Render Cycle

### SPI Buffer Transfer (`show()` flow, `sh1107.py:65–90`)

## SH1107 Hardware Constraints

### Gotcha #1: 0x21 Single-Byte Command

### Gotcha #2: CS Must Toggle Per Byte in `show()`

### Gotcha #3: Rotation via Pixel Operations, Not Byte Shuffling

### Gotcha #4: MONO_HMSB Framebuffer Format Required

## Entry Points

- Location: `main.py:37–41` (`if __name__ == "__main__"` block)
- Triggers: Pico boots or user runs `main.py` via `mpremote run`/Thonny
- Responsibilities:

```bash

```

## Architectural Constraints

- **Threading:** Single-threaded event loop. `bootstrap.fetch()` is blocking (~20s wifi timeout + <2s API round-trip). No async/await. Refresh cycle is synchronous.
- **Global state:** None — all state is local or instance variables within `OLED` class.
- **Circular imports:** None. Dependency graph is acyclic: `main.py` → {`sh1107`, `wifi`, `weather`, `icons`, `text_render`}, no feedback.
- **Memory model:** Framebuffer is 1024 bytes fixed. Rotation creates additional 1024-byte temporary buffer. Total ~2KB active + MicroPython runtime heap.
- **Hardware pinout:** Fixed by HAT header — no configuration possible (DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1). Do not attempt to move pins.

## Error Handling

- WiFi connection timeout → `bootstrap.fetch()` returns `(None, None, None, None, None, None)` after 20s, `weather_view` sets `_cache_status = "no_wifi"` and displays "no wifi"
- Weather API failure (network, JSON parse, HTTP error) → `weather.current()` catches all exceptions, returns `(None, None, None)`, `main.py` displays "no data"
- No exception bubbling; all failures result in fallback UI display

## Cross-Cutting Concerns

- `WIFI_SSID`, `WIFI_PASSWORD` — network credentials
- `REFRESH_SECONDS` — render cycle interval
- `ROTATE` — 180° display flip (boolean passed to `OLED()`)

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
