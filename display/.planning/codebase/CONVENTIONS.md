# Coding Conventions

**Analysis Date:** 2026-07-19

## Naming Patterns

**Files:**
- `snake_case` for all modules: `sh1107.py`, `bootstrap.py`, `text_render.py`, `icons.py`, `main.py`
- View modules grouped in `views/` directory: `weather_view.py`, `clock_view.py`, `system_view.py`
- No file extension except `.py`

**Functions:**
- `snake_case` for all functions
- Public functions: no prefix. Examples: `draw()` in `icons.py:73`, `fetch()` in `bootstrap.py:18`, `text()` in `text_render.py:4`
- Private/internal functions: single underscore prefix. Examples: `_init()` in `sh1107.py:39`, `_center_text()` in `main.py:31`, `_kind()` in `icons.py:1`, `_rssi_to_bars()` in `system_view.py:21`

**Variables:**
- `snake_case` for all variables
- Module-level state: lowercase prefix. Examples: `_cached_temp` in `weather_view.py:7`, `_last_refresh_ms` in `weather_view.py:14`, `_pending_dir` in `main.py:25`
- Local loop variables: single letter or short. Examples: `w`, `h`, `x`, `y`, `cx`, `cy`, `buf`, `col`, `byte` in framebuffer operations

**Constants:**
- `UPPER_SNAKE_CASE` for module-level constants
- Public module constants exported from driver: `WIDTH`, `HEIGHT` in `sh1107.py:13-14`
- User-tunable constants grouped at top of `main.py:8-11`: `REFRESH_SECONDS`, `ROTATE`
- Hardware/private constants prefixed with underscore: `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST` in `sh1107.py:7-11`
- Internal timing constants: `_POLL_MS`, `_DEBOUNCE_MS` in `main.py:14-15`; `_REFRESH_MS`, `_RETRY_MS` in `weather_view.py:12-13`
- Numeric constants with underscores for readability: `20_000_000` (SPI clock) in `sh1107.py:25`, `600_000` (milliseconds) in `weather_view.py:12`

**Classes:**
- `PascalCase` for class names: `OLED` in `sh1107.py:17`
- `OLED` subclasses `framebuf.FrameBuffer` to inherit drawing methods

**Type & Tag Conventions:**
- No type hints anywhere (MicroPython embedded idiom for performance)
- No docstrings (performance-critical embedded code)
- Module constants use `micropython.const()` in `sh1107.py:2` for compile-time optimization of frequently-accessed pin values

## Code Style

**Formatting:**
- 4-space indentation consistently throughout
- No explicit formatter configured; follows idiomatic MicroPython conventions
- String formatting via `.format()` for readability: `"{:.0f}C".format(temp)` in `weather_view.py:38`, `"{:02d}:{:02d}".format(t[3], t[4])` in `clock_view.py:81`
- Inline method chaining used sparingly: `self.rst(1); time.sleep_ms(1)` in `sh1107.py:40-41`

**Linting:**
- No linter configured (MicroPython idiom)
- Code assumes MicroPython interpreter compatibility
- Module organization relies on import correctness rather than static analysis

## Import Organization

**Standard Order (observed across codebase):**
1. Machine/stdlib imports (hardware + low-level): `from machine import Pin, SPI` in `sh1107.py:1`, `import network` in `bootstrap.py:1`
2. MicroPython extensions: `from micropython import const` in `sh1107.py:2`
3. Framebuffer/stdlib abstractions: `import framebuf` in `sh1107.py:3`
4. Timing: `import time` in `sh1107.py:4`
5. Network/HTTP: `import urequests` in `bootstrap.py:3`
6. Local driver imports: `from sh1107 import OLED, WIDTH, HEIGHT` in `main.py:1`
7. Local view modules: `from views import weather_view, clock_view, system_view` in `main.py:3`
8. Other local modules: `import text_render` in `main.py:4`, `import bootstrap` in `main.py:5`

**Path Aliases:**
- No path aliases used; flat module namespace suitable for embedded constraints
- All imports are relative to the Pico's `/` filesystem root

**Lazy Imports:**
- Used strategically to defer errors: `import secrets` inside `bootstrap.fetch()` (line 30) instead of at module level, to allow `main.py` to display the "missing secrets.py" fallback screen before crashing

## Error Handling

**Patterns:**
- Bare `except Exception:` blocks used for graceful API/network degradation
- No exception re-raising; all failures result in fallback values or silent continuation

**Specific Patterns:**

**Network/API Failures (`bootstrap.py:36-54`):**
```python
try:
    r = urequests.get("...")
    loc = r.json()
    ...
except Exception:
    return ip, None, None, None, None, None
```
- Returns tuple with partial state: `(ip, None, None, None, None, None)` when API fails but WiFi succeeded
- Caller distinguishes "no_wifi" (ip=None) from "no_data" (ip!=None, temp=None) via cache state

**NTP Sync Failures (`clock_view.py:69-73`):**
```python
try:
    ntptime.settime()
    _synced = True
except Exception:
    pass
```
- Sets timestamp guard _last_sync_ms at entry (line 68) so failed attempts don't tight-loop
- Boolean _synced remains False; render() displays fallback "--:--"

**File I/O Failures (`clock_view.py:44-48`):**
```python
try:
    with open(_TZ_OFFSET_FILE, "w") as f:
        f.write(str(offset))
except Exception:
    pass
```
- Best-effort persistence; write failures are silent (no repeated attempts)

**WiFi Connection Timeout (`bootstrap.py:6-15`):**
- Explicit loop with `timeout` parameter (default 20 seconds)
- Returns `None` if connection fails; caller handles gracefully

## Logging

**Framework:** Not used; state is communicated via display rendering only

**Debug Approach:**
- Interactive via Thonny IDE or `mpremote run` observation
- No persistent logging due to embedded constraints
- State communicated to user via UI: "connecting...", "no wifi", "no data", "--:--" (when unsynced), "IP: --" (when offline)

## Comments

**When to Comment:**
- Hardware/protocol traps: "SH1107 needs CS toggled around every data byte" in `sh1107.py:83-84`
- Non-obvious control flow: "SPI first, DC after — GP8 is SPI1's default MISO" in `sh1107.py:22-24`
- API quirks: "ip-api's default response omits offset and query; request both explicitly" in `bootstrap.py:37-39`
- Timing/scheduling semantics: "Stamp at start so transient failures don't tight-loop" in `weather_view.py:49-50` and `clock_view.py:66-67`
- Architectural decisions: "Composition-root fan-out" in `main.py:76-79`; "Pure state-setter driven by main._refresh_all" in `weather_view.py:46`

**What NOT to Comment:**
- Implementation details visible in code (e.g., "increment x" before `x += 1`)
- Self-documenting function names and variable names
- Loop mechanics in standard patterns

**JSDoc/TSDoc:**
- Not used (MicroPython embedded idiom)

## Function Design

**Size:** Small, focused functions optimizing for readability and reusability
- Drawing helpers: 2–5 lines of framebuffer calls. Examples: `_sun()` in `icons.py:17-22` (6 lines), `_moon()` in `icons.py:25-28` (4 lines), `_cloud()` in `icons.py:31-35` (5 lines)
- Orchestration: 10–15 lines. Examples: `_refresh_all()` in `main.py:75-85` (11 lines), `render()` in `weather_view.py:28-43` (16 lines)
- Driver methods: 2–30 lines. Example: `show()` in `sh1107.py:65-90` (26 lines)

**Parameters:**
- Positional-only for internal functions (performance, clarity in embedded context)
- Keyword defaults used only for public APIs: `scale=1` in `text_render.py:4` and `_center_text()` implementations
- Example: `text(fb, s, x, y, scale=1, color=1)` in `text_render.py:4`

**Return Values:**
- Implicit None (no return statement) when mutating framebuffer or state: `show()`, `_cmd()`, `draw()`, `set_data()`, `set_tz_offset()`, `sync()`
- Computed single values for query functions: `should_refresh()` returns bool in `weather_view.py:23`, `_rssi_to_bars()` returns int in `system_view.py:21`
- Tuples for bootstrap round-trips: `fetch()` returns 6-tuple in `bootstrap.py:18`, `(ip, temp, code, is_day, tz_offset, wan_ip)`

**Helpers Extracted:**
- `_kind(code, is_day)` in `icons.py:1` maps WMO code to drawable kind before dispatcher lookup
- `_center_text()` duplicated across view modules (intentional; avoids circular imports between views)
- `_draw_bars()` in `system_view.py:9` for RSSI visualization

## Module Design

**Exports:**
- `sh1107.py`: `OLED` class, `WIDTH` const, `HEIGHT` const (imported in `main.py:1`)
- `bootstrap.py`: `fetch()` function (imported and called in `main.py:80`)
- `text_render.py`: `text()` function (imported in all view modules)
- `icons.py`: `draw()` function (imported in `weather_view.py:2`)
- View modules: `render()`, `set_data()` (or equivalent setter), `should_refresh()` (or equivalent guard)
- No barrel files or re-export pattern

**Module-Level State:**
- `sh1107.OLED.__init__` initializes hardware once; instance stored in `main.py:88`
- Each view module owns its private cache: `_cached_temp`, `_cache_status` in `weather_view.py`; `_synced`, `_cached_tz_offset` in `clock_view.py`; `_cached_wan_ip` in `system_view.py`
- No cross-view imports; `main.py` fans out to all views via function calls

**User Configuration:**
- Top of `main.py:8-11`: `REFRESH_SECONDS = 600`, `ROTATE = True`
- Tunable without modifying function bodies
- `secrets.py` (gitignored) contains `WIFI_SSID`, `WIFI_PASSWORD` imported in `bootstrap.fetch()`

**Hardware Configuration:**
- Top of `sh1107.py:6-14`: Pin definitions (`_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`), display size (`WIDTH`, `HEIGHT`)
- Fixed by HAT header; do not attempt to move pins
- Wrapped in `micropython.const()` for performance

---

*Convention analysis: 2026-07-19*
