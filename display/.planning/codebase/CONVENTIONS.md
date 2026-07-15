# Coding Conventions

**Analysis Date:** 2026-07-15

## Naming Patterns

**Files:**
- Module names use `snake_case`: `sh1107.py`, `text_render.py`, `weather.py`, `wifi.py`, `icons.py`, `main.py`
- No file extensions beyond `.py`

**Functions:**
- Use `snake_case` for all functions: `_center_text()`, `_render()`, `connect()`, `current()`
- Private/internal functions prefixed with single underscore: `_init()`, `_cmd()`, `_kind()`, `_sun()`, `_moon()`, `_cloud()`, `_rain()`, `_snow()`, `_thunder()`, `_fog()`, `_center_text()`, `_render()`
- Public functions have no prefix: `draw()`, `text()`, `connect()`, `current()`

**Variables:**
- Use `snake_case` for all variables: `WIFI_SSID`, `REFRESH_SECONDS`, `x_center`, `y_center`, `temp`, `code`, `is_day`
- Lowercase for local variables: `w`, `h`, `buf`, `rot_buf`, `col`, `byte`, `dx`, `dy`, `cx`, `cy`

**Types/Classes:**
- Use `PascalCase` for class names: `OLED` (subclasses `framebuf.FrameBuffer`)
- Module-level constants use `UPPER_SNAKE_CASE`: `WIDTH`, `HEIGHT`, `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`
- Private module constants prefixed with underscore: `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`

## Code Style

**Formatting:**
- No explicit formatter configured (typical MicroPython idiom)
- 4-space indentation (observed throughout)
- Line breaks used sparingly; some method calls chained inline: `self.rst(1); time.sleep_ms(1)`
- String concatenation via `.format()` for readability: `"{:.0f}C".format(temp)`

**Linting:**
- No linter detected; code assumes MicroPython interpreter compatibility
- MicroPython idiom: no type hints anywhere in codebase
- Uses `micropython.const()` for compile-time constants on performance-critical values: `_DC = const(8)`

## Import Organization

**Order:**
1. Standard library imports (machine, network, framebuf, time)
2. Third-party imports (urequests, micropython)
3. Local imports (relative imports of project modules)

**Examples:**
- `sh1107.py`: `from machine import Pin, SPI` → `from micropython import const` → `import framebuf` → `import time`
- `main.py`: `from sh1107 import OLED, WIDTH, HEIGHT` → `import wifi` → `import weather` → `import icons` → `import text_render` → `import time`
- `text_render.py`: `import framebuf`
- `weather.py`: `import urequests`
- `wifi.py`: `import network` → `import time`

**No path aliases used** — imports are direct module names or explicit from-imports.

## Error Handling

**Pattern:**
- Bare `except Exception:` blocks for network/API calls where graceful degradation is needed
- Example in `weather.py`: `except Exception: return None, None, None`
- Example in `main.py`: checks for `None` return values to display fallback UI ("no wifi", "no data")
- No explicit error logging; failures are silent with UI fallback

## Logging

**Framework:** `None` — no logging framework used

**Patterns:**
- Console output via print not used; state communicated via UI display
- Debug happens via Thonny or `mpremote` execution observation

## Comments

**When to Comment:**
- Inline comments placed near hardware/protocol traps: "SH1107 needs CS toggled around every data byte" in `sh1107.py:83-84`
- Comments for non-obvious control flow: "SPI first, DC after — GP8 is SPI1's default MISO" in `sh1107.py:22-24`
- Comments for register initialization explaining bit semantics: "display off", "column addr", "page addr" inline in init sequence in `sh1107.py:45-61`
- No docstrings anywhere (MicroPython idiom for embedded/performance-critical code)
- Comments summarize intent, not implementation

**JSDoc/TSDoc:**
- Not used; MicroPython does not use type annotations or docstring generation

## Function Design

**Size:**
- Small, focused functions: `_center_text()` is 3 lines, `_render()` is 13 lines
- Drawing functions are typically 2–5 lines of ellipse/line/rect calls
- Private helper functions extracted: `_kind()` maps weather code to icon type before lookup

**Parameters:**
- Positional parameters used; no keyword defaults except in public APIs
- Example: `text(fb, s, x, y, scale=1, color=1)` in `text_render.py:4`
- Internal helpers use positional-only: `_center_text(oled, s, x_center, y_center, scale=1)`

**Return Values:**
- Functions return None implicitly (no return statement) when mutating state: `show()`, `_cmd()`, `draw()`
- Functions return computed values: `current()` returns tuple `(temp, code, is_day)` or `(None, None, None)`
- Single-purpose functions return a single value or None

## Module Design

**Exports:**
- `sh1107.py` exports: `OLED` class, `WIDTH` const, `HEIGHT` const
- `main.py` exports: `__main__` block (entry point)
- `text_render.py` exports: `text()` function (imported in main)
- `weather.py` exports: `current()` function (imported in main)
- `wifi.py` exports: `connect()` function (imported in main)
- `icons.py` exports: `draw()` function (imported in main)

**Barrel Files:**
- Not used; each module has a single purpose and no re-export pattern

**Module-Level Constants Placement:**
- User config constants placed at top of `main.py` (lines 8–12): `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`
- Hardware pins defined at top of `sh1107.py` (lines 6–14): `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`, `WIDTH`, `HEIGHT`
- Hardware constants use `const()` for MicroPython optimization
- This placement allows editing without modifying function bodies

**Framebuf Method Reuse:**
- `OLED` subclasses `framebuf.FrameBuffer` (line 17 in `sh1107.py`) to inherit `text()`, `fill()`, `pixel()`, `rect()`, `line()`, `ellipse()`, `fill_rect()`, `hline()`, `vline()` methods
- Callers in `main.py` and `icons.py` use these methods directly on the `OLED` instance or temporary `FrameBuffer` objects
- Example: `text_render.py` creates a temporary `FrameBuffer` to render text at scale, then reads pixels and renders them scaled on the target framebuffer

## Code Patterns

**Rotation Handling:**
- Rotation implemented via pixel-level read/write (framebuf method calls) not buffer-byte manipulation
- Explained in `sh1107.py:66-73`: iterate over all pixels, if set, write to rotated coordinates in new buffer
- This avoids the GDDRAM wrap issue documented in CLAUDE.md

**Display Initialization:**
- Register sequence in `sh1107.py:44-63` grouped by function (display control, addressing, contrast, etc.)
- Single-byte commands like `0x21` are not followed by data bytes (hardware limitation documented in CLAUDE.md)
- Reset toggle with explicit timing: `rst(1)` → sleep 1ms → `rst(0)` → sleep 10ms → `rst(1)` → sleep 10ms

**Weather Icon Dispatch:**
- `icons.py` uses a dictionary `_DRAWERS` mapping kind names to drawing functions (lines 62–70)
- `draw()` function maps weather code to kind via `_kind()`, then looks up function and calls it
- Clean separation: code-to-kind logic separate from rendering

---

*Convention analysis: 2026-07-15*
