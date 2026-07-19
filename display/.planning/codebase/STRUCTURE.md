# Codebase Structure

**Analysis Date:** 2026-07-19

## Directory Layout

```
display/
├── main.py              # Application orchestration: carousel, IRQ, poll loop, bootstrap fan-out
├── sh1107.py            # Driver: SPI init, GDDRAM push, rotation
├── bootstrap.py         # I/O: WiFi + ip-api + open-meteo fetch, 6-tuple return
├── icons.py             # Icons: WMO code → icon type, 7 drawing functions
├── text_render.py       # Helper: scaled font via double-buffer framebuf
├── secrets.py           # Configuration: WIFI_SSID, WIFI_PASSWORD (gitignored)
├── secrets.py.example   # Template for secrets.py (committed)
├── CLAUDE.md            # Project context, constraints, gotchas, development notes
├── views/               # View package: three independent carousel views
│   ├── __init__.py      # Empty package marker
│   ├── weather_view.py  # Weather: icon + temp, cache + refresh scheduling
│   ├── clock_view.py    # Clock: HH:MM display, NTP sync, TZ persistence
│   └── system_view.py   # System: SSID, WAN IP, RSSI bars, live reads
├── Plans/               # GSD phase documentation (non-code artifact)
├── .planning/codebase/  # Codebase analysis documents (this location)
│   ├── ARCHITECTURE.md  # Layers, data flow, abstractions, constraints
│   └── STRUCTURE.md     # File organization, naming, placement guidance
└── tz_offset.txt        # Transient: TZ offset persisted by clock_view (gitignored, created at runtime)
```

## Directory Purposes

**Root level (`display/`):**
- Purpose: MicroPython entry point and composition layer
- Contains: Driver, app orchestration, I/O bootstrap, view package, config
- Key execution order: `secrets.py` must exist before importing `bootstrap`, which imports `secrets` lazily inside `fetch()`

**`views/` package:**
- Purpose: Three independent carousel view implementations
- Contains: Stateless render functions, state setters, refresh/sync predicates, module-level caches
- Key invariant: Views do NOT import each other; `main.py` is the only caller and orchestrator
- Exports: `weather_view`, `clock_view`, `system_view` modules with public API

**`.planning/codebase/` (this directory):**
- Purpose: GSD codebase analysis documents
- Contains: `ARCHITECTURE.md`, `STRUCTURE.md` (this file), and potentially `CONVENTIONS.md`, `TESTING.md`, `STACK.md`, `INTEGRATIONS.md`, `CONCERNS.md` from other focus areas
- Committed: Yes (part of `.planning/` which is tracked)
- Generated: By `/gsd:map-codebase` agent

**`Plans/` directory:**
- Purpose: GSD phase planning documents
- Contains: `PLAN.md`, `SUMMARY.md`, `STATE.md` and phase-specific phase documents
- Committed: Yes
- Generated: By `/gsd:plan-phase` command

## Key File Locations

**Entry Points:**
- `main.py:87` — Boot: OLED init, button IRQ setup, pre-fetch render, blocking bootstrap, NTP sync, main loop

**Configuration:**
- `secrets.py` — User credentials: `WIFI_SSID`, `WIFI_PASSWORD` (gitignored; must exist before `bootstrap.fetch()` is called)
- `secrets.py.example` — Template (committed)
- `main.py:8–10` — User config: `REFRESH_SECONDS`, `ROTATE`
- `main.py:13–18` — Tunables: `_POLL_MS`, `_DEBOUNCE_MS`, `_KEY0_PIN`, `_KEY1_PIN`
- `views/weather_view.py:12–14` — Refresh intervals: `_REFRESH_MS`, `_RETRY_MS`
- `views/clock_view.py:12–14` — Sync intervals: `_SYNC_MS`, `_RETRY_MS`

**Core Logic:**
- `sh1107.py:17–96` — `OLED` class: init, register sequence, SPI `show()`, power control
- `main.py:75–84` — `_refresh_all()` orchestrator: bootstrap fan-out to all view setters
- `main.py:116–138` — Main poll loop: carousel nav, refresh scheduling, clock ticks, sync retries
- `bootstrap.py:18–54` — `fetch()` function: WiFi + geolocation + weather, 6-tuple return
- `views/weather_view.py:28–43` — Weather rendering: cache status display, icon + temp
- `views/clock_view.py:64–86` — Clock rendering: HH:MM or --:-- (NTP status)
- `views/system_view.py:43–73` — System rendering: SSID, WAN IP, RSSI bars

**Testing:**
- Not applicable — MicroPython runs directly on Pico; no host-side test framework

**Runtime Artifacts:**
- `tz_offset.txt` — Persisted TZ offset (created by `clock_view.set_tz_offset()`, read at module load, gitignored)

## Naming Conventions

**Files:**
- `snake_case.py` — All module names: `sh1107.py`, `bootstrap.py`, `main.py`, `icons.py`, `text_render.py`, view modules
- No file extensions beyond `.py`
- No multi-dot naming (e.g., `foo.test.py` not used)

**Directories:**
- `snake_case/` — `views/` is the only package; contains only modules (no nested packages)
- No multi-level nesting (flat or single-level only)

**Functions:**
- `snake_case` for all functions: `_center_text()`, `_render()`, `_wifi_connect()`, `fetch()`, `draw()`, `text()`, `sync()`, `render()`, `set_data()`
- Private/internal functions prefixed with single underscore: `_init()`, `_cmd()`, `_kind()`, `_draw_bars()`, `_rssi_to_bars()`, `_sun()`, `_moon()`, `_cloud()`, `_rain()`, `_snow()`, `_thunder()`, `_fog()`, `_center_text()`
- Public functions have no prefix: `draw()`, `text()`, `fetch()`, `render()`, `set_data()`, `set_tz_offset()`, `set_wan_ip()`, `sync()`, `should_refresh()`, `should_tick()`, `should_sync()`

**Variables:**
- `UPPER_SNAKE_CASE` for module-level constants: `WIDTH`, `HEIGHT`, `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`, `VIEWS`
- `_UPPER_SNAKE_CASE` for private module constants: `_DC`, `_CS`, `_SCK`, `_MOSI`, `_RST`, `_POLL_MS`, `_DEBOUNCE_MS`, `_KEY0_PIN`, `_KEY1_PIN`, `_REFRESH_MS`, `_RETRY_MS`, `_SYNC_MS`, `_TZ_OFFSET_FILE`, `_DRAWERS`
- `snake_case` for module-level cache state: `_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status`, `_cached_tz_offset`, `_cached_wan_ip`, `_synced`
- `snake_case` for locals: `w`, `h`, `buf`, `rot_buf`, `col`, `byte`, `dx`, `dy`, `cx`, `cy`, `now`, `ip`, `temp`, `code`, `is_day`, `offset`, `wan_ip`, `t`, `s`, `ssid`, `connected`, `wlan`, `rssi`, `level`

**Types/Classes:**
- `PascalCase` for class names: `OLED` (subclasses `framebuf.FrameBuffer`)
- No other classes in codebase; all helpers are functions or modules (no OOP pattern)

**Imports & Module Names:**
- Absolute imports only: `from sh1107 import OLED, WIDTH, HEIGHT`; `import bootstrap`; `from views import weather_view`
- No relative imports (avoid `from . import`)
- No star imports (never `from module import *`)

## Where to Add New Code

**New Feature (e.g., new refresh parameter, new cache field):**
- Add to target module's top-level constants or cache state
- Example: Add weather code bounds → `icons._kind()` mapping
- File: `icons.py:1–14`

**New View:**
- Create `views/new_view.py` with public API: `render(oled)`, state setters, scheduling predicates
- Add to `main.VIEWS` tuple after `system_view` (line 27)
- Add case to main loop if view needs specialized scheduling (lines 124–137)
- Ensure NO cross-view imports; compose in `main.py` only

**New Helper (text, icons, rendering):**
- Add function to existing helper module (`text_render.py`, `icons.py`) or create new `helper_name.py`
- Export public functions with no prefix; private helpers prefixed `_`
- Import into relevant view or `main.py` as needed

**New Persistent Data (like TZ offset):**
- Add cache state to the view that owns the data
- Implement `set_*()` setter in that view
- Implement file I/O with try/except (flash may fail)
- Load at module import time if needed before `main.py` runs
- Call setter from `main._refresh_all()` fan-out

**New Button / Navigation:**
- Add `Pin()` setup in `main.__main__` block (lines 92–95)
- Add IRQ handler function similar to `_on_key0()` / `_on_key1()`
- Set `_pending_dir` or other action flag in handler
- Check flag in main loop and dispatch action (lines 118–123 pattern)

**Config Constants (user-facing):**
- Place at top of `main.py` (lines 8–10) for refresh interval, rotation
- Place at top of view module for view-specific intervals (e.g., `weather_view:12–14`)
- Document with inline comments explaining constraints

**Tunable Constants (internal):**
- Place in `main.py` lines 13–18 for timing/debounce/pins
- Prefix with `_` (private)
- Add comment explaining valid range if applicable

## Special Directories

**`views/` package:**
- Purpose: Carousel view implementations
- Generated: No (hand-written)
- Committed: Yes
- Invariant: Must have `__init__.py` (even if empty) to be a package; `main.py` imports `from views import weather_view, clock_view, system_view`
- Updating: Never import views into other views; only `main.py` composes

**`.planning/codebase/` documentation directory:**
- Purpose: GSD codebase analysis output
- Generated: Yes (by `/gsd:map-codebase`)
- Committed: Yes (`.planning/` is tracked)
- Updating: Regenerated when codebase structure significantly changes; safe to regenerate without data loss

**`Plans/` directory:**
- Purpose: GSD phase planning and execution logs
- Generated: Yes (by `/gsd:plan-phase` and `/gsd:execute-phase`)
- Committed: Yes
- Updating: Accumulates phase documents; older phases kept as reference; never delete, only append new phases

**`tz_offset.txt` transient:**
- Purpose: Runtime-persisted TZ offset (Pico flash)
- Generated: Yes (by `clock_view.set_tz_offset()`)
- Committed: No (gitignored)
- Lifecycle: Created once per unique TZ; rewritten only on TZ change (flash-wear guard)

## Dependency Tree (for context on file placement)

```
main.py (entry point, orchestrator)
  ├─→ sh1107.py (OLED driver)
  ├─→ views/weather_view.py
  │   ├─→ icons.py (weather icon drawing)
  │   └─→ text_render.py (scaled font)
  ├─→ views/clock_view.py
  │   └─→ text_render.py (scaled font)
  ├─→ views/system_view.py
  │   └─→ text_render.py (scaled font)
  ├─→ bootstrap.py (WiFi + ip-api + open-meteo)
  │   └─→ secrets.py (lazy import inside fetch())
  └─→ text_render.py (text scaling helper)

icons.py (no dependencies except framebuf stdlib)
text_render.py (no dependencies except framebuf stdlib)
bootstrap.py (no dependencies on main, views, driver)
```

## File Sizes & Complexity Indicators

| File | Lines | Purpose | Complexity |
|------|-------|---------|------------|
| `main.py` | 139 | Orchestration, carousel, poll loop | Medium (state machine) |
| `sh1107.py` | 97 | SPI driver, GDDRAM transfer | Medium (hardware protocol) |
| `bootstrap.py` | 55 | WiFi + API fetch | Low (sequential I/O) |
| `views/weather_view.py` | 64 | Weather cache, render, scheduling | Low (caches + predicates) |
| `views/clock_view.py` | 87 | Clock + NTP sync + persistence | Medium (scheduling + file I/O) |
| `views/system_view.py` | 74 | Network status, live reads | Low (live queries, no cache) |
| `icons.py` | 75 | Icon drawing dispatcher | Low (drawing primitives) |
| `text_render.py` | 16 | Font scaling | Low (double-buffer technique) |

---

*Structure analysis: 2026-07-19*
