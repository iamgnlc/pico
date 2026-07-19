<!-- refreshed: 2026-07-19 -->
# Architecture

**Analysis Date:** 2026-07-19

## System Overview

```text
┌────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  `main.py` — carousel orchestration, button IRQ, poll loop     │
│  VIEWS = (weather_view, clock_view, system_view)               │
└─────────┬─────────────────────────┬──────────────────┬─────────┘
          │                         │                  │
          ▼                         ▼                  ▼
┌─────────────────────┐   ┌──────────────────┐  ┌──────────────┐
│  Weather View       │   │   Clock View     │  │ System View  │
│  `views/weather_   │   │ `views/clock_    │  │ `views/      │
│   view.py`          │   │  view.py`        │  │ system_view  │
│                     │   │                  │  │ .py`         │
│ render()            │   │ render()         │  │              │
│ set_data()          │   │ set_tz_offset()  │  │ render()     │
│ should_refresh()    │   │ should_tick()    │  │ set_wan_ip() │
│                     │   │ should_sync()    │  │              │
│                     │   │ sync()           │  │              │
└─────────┬───────────┘   └────────┬─────────┘  └──────┬───────┘
          │                        │                   │
          │    ┌────────────────────┘                   │
          │    │                                        │
          ▼    ▼                                        ▼
┌──────────────────────────┐      ┌──────────────────────────────┐
│   I/O & Helpers          │      │   Persistent Storage         │
│  `bootstrap.py` — WiFi   │      │ `tz_offset.txt` — TZ offset  │
│   + ip-api + open-meteo  │      │ (flash-wear guarded)         │
│  `icons.py` — icon draw  │      │                              │
│  `text_render.py` — font │      └──────────────────────────────┘
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Driver Layer                                 │
│  `sh1107.py` — SPI hardware, GDDRAM push, rotation              │
│  OLED subclass framebuf.FrameBuffer                              │
│  Pinout fixed: DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| OLED Driver | SPI init, register sequence, GDDRAM transfer via `show()`, 180° pixel-level rotation | `sh1107.py` |
| Application Root | Carousel state, button IRQ handlers, poll loop, bootstrap fan-out orchestration | `main.py` |
| Weather View | Weather cache, refresh scheduling, icon + temp rendering, cache-status display | `views/weather_view.py` |
| Clock View | Time display, NTP sync, TZ offset persistence, minute-change detection | `views/clock_view.py` |
| System View | Network status (SSID, WAN IP, RSSI bars), live read from network state | `views/system_view.py` |
| Bootstrap I/O | WiFi connect + IP geolocation (ip-api) + current weather (open-meteo), 6-tuple return | `bootstrap.py` |
| Icons | WMO weather code → icon type mapper, 7 icon drawing functions | `icons.py` |
| Text Render | Scaled font rendering via double-buffer framebuf technique | `text_render.py` |

## Pattern Overview

**Overall:** Layered, decoupled multi-view carousel on a single framebuffer.

**Key Characteristics:**
- Single framebuffer (`OLED` subclass) inherited from `framebuf.FrameBuffer`, enabling free use of `text()`, `fill()`, `pixel()`, `rect()`, `ellipse()`, `line()`, `hline()`, `vline()` methods
- Three independent view modules (`weather_view`, `clock_view`, `system_view`) with stateless rendering, no cross-view imports — composition happens only in `main.py._refresh_all()` fan-out
- Explicit state setters (`set_data()`, `set_tz_offset()`, `set_wan_ip()`) called by orchestrator, not side-effect-driven
- Pure predicates (`should_refresh()`, `should_tick()`, `should_sync()`) enable main loop polling without tight-loops
- Bootstrap as a leaf I/O layer — `fetch()` returns a 6-tuple; failure semantics distinguish WiFi-fail from API-fail so callers can set correct cache status

## Layers

**Driver Layer:**
- Purpose: Abstract Raspberry Pi Pico SPI hardware and SH1107 OLED controller protocol
- Location: `sh1107.py`
- Contains: `OLED` class subclassing `framebuf.FrameBuffer`, SPI pin config, init sequence, `show()` method, power control
- Depends on: `machine.Pin`, `machine.SPI`, `framebuf`, `micropython.const()`, `time` (MicroPython stdlib)
- Used by: `main.py` instantiates `OLED(rotate=ROTATE)` at boot; views call `render(oled)` to paint framebuffer

**View Layer:**
- Purpose: Render view content, manage per-view cache state and refresh scheduling
- Location: `views/weather_view.py`, `views/clock_view.py`, `views/system_view.py`
- Contains: Stateless `render(oled)`, state setters (`set_data()`, `set_tz_offset()`, `set_wan_ip()`), predicates (`should_refresh()`, `should_tick()`, `should_sync()`), sync methods (`clock_view.sync()`)
- Depends on: `sh1107.WIDTH/HEIGHT`, `time`, `ntptime` (clock), `network` (system), `text_render`, `icons` (weather)
- Used by: `main.py` polls predicates and calls render/setters/sync on the current view and during refresh fan-out

**Application Layer:**
- Purpose: Orchestrate carousel navigation, refresh scheduling, WiFi bootstrap, and main poll loop
- Location: `main.py`
- Contains: Carousel state (`_current_idx`, `_pending_dir`), button IRQ handlers (`_on_key0()`, `_on_key1()`), debounce logic, refresh orchestrator (`_refresh_all()`), page-dot UI, boot sequence, main event loop
- Depends on: `sh1107.OLED`, `views.*`, `bootstrap`, `text_render`, `time`, `machine.Pin`
- Used by: MicroPython runtime; this is the entry point

**I/O Layer (Bootstrap):**
- Purpose: Fetch network data (WiFi IP, geolocation, weather, WAN IP) in a single round-trip
- Location: `bootstrap.py`
- Contains: `_wifi_connect()` internal helper, `fetch()` public function returning 6-tuple
- Depends on: `network.WLAN`, `urequests` (HTTP client), `time`, lazy-imported `secrets`
- Used by: `main.py._refresh_all()` calls `bootstrap.fetch()` and fans out results to all three view setters

**Helper Layer:**
- Purpose: Weather icon rendering, scaled font rendering
- Location: `icons.py`, `text_render.py`
- Contains: WMO code → kind mapper, 7 icon drawing primitives, double-buffer text scaler
- Depends on: `framebuf` (reader-supplied), passed as arguments
- Used by: `weather_view.render()` calls `icons.draw()` for weather icon; views call `text_render.text()` for text output

## Data Flow

### Primary Render Cycle

1. **Boot sequence (`main.__main__`, lines 87–114):**
   - `OLED(rotate=ROTATE)` instantiated (`sh1107.py:17`)
   - Button pins (`KEY0=GP15`, `KEY1=GP17`) configured with `irq()` handlers (`main:92-95`)
   - Pre-fetch render: `weather_view.render(oled)` draws "connecting..." from cache-status "pending" (`weather_view:30-31`)
   - Page dots drawn via `_draw_page_dots(oled, _current_idx)` (`main:67-72`)
   - `oled.show()` pushed to GDDRAM (`sh1107.py:65-90`)
   - Blocking `_refresh_all(oled)` call: `bootstrap.fetch()` (~20s timeout) → view state setters fan-out → `weather_view.render(oled)` painted with real data
   - Page dots + `oled.show()` again
   - Best-effort `clock_view.sync()` for NTP (non-blocking failure)

2. **Main poll loop (`main:116–138`):**
   - Every 100ms (`_POLL_MS`):
     a. Check `_pending_dir != 0` → carousel advance: `VIEWS[_current_idx].render(oled)` → dots → `show()`
     b. Check `weather_view.should_refresh(now)` → `_refresh_all(oled)` (blocking ~2s typical, ~20s on timeout) → overpaint with current view if not Weather → dots → `show()`
     c. Check `_current_idx == 1 and clock_view.should_tick(now)` → `clock_view.render(oled)` → dots → `show()`
     d. Check `clock_view.should_sync(now)` → `clock_view.sync(oled)` (NTP call, non-blocking)
     e. Sleep 100ms

### Refresh Fan-Out (from `_refresh_all()`, `main:75–84`)

```
bootstrap.fetch() returns (ip, temp, code, is_day, tz_offset, wan_ip) 6-tuple
    │
    ├─→ weather_view.set_data(ip, temp, code, is_day)
    │   - Sets cache status: "ok" | "no_data" | "no_wifi"
    │   - Stamps _last_refresh_ms for interval scheduling
    │
    ├─→ clock_view.set_tz_offset(tz_offset)
    │   - Updates _cached_tz_offset
    │   - Writes to tz_offset.txt (flash-wear guard: only if changed)
    │
    ├─→ system_view.set_wan_ip(wan_ip)
    │   - Updates _cached_wan_ip RAM-only (no persistence)
    │
    └─→ weather_view.render(oled)
        - Paints the now-populated cache to GDDRAM
```

### Button Press Flow

```
Key press (GP15 or GP17 falling edge)
    │
    └─→ _on_key0(pin) or _on_key1(pin) IRQ handler (`main:49-64`)
        - Debounce check: `time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS` → early return
        - Set `_pending_dir = -1` (previous) or `+1` (next)
        - Stamp _last_press_ms
    │
    └─→ Main loop detects `_pending_dir != 0` (`main:118-123`)
        - Carousel advance: `_current_idx = (_current_idx + _pending_dir) % 3`
        - Clear _pending_dir
        - `VIEWS[_current_idx].render(oled)` — render the new view's cache
        - Draw page dots
        - `oled.show()` — GDDRAM push
```

### State Management

**Per-module caches:**
- `weather_view`: `_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status`
- `clock_view`: `_cached_tz_offset` (persisted to flash), `_synced` flag, `_last_render_min`
- `system_view`: `_cached_wan_ip` (RAM-only)

**Main-module state:**
- `_current_idx` — active view in carousel (0=weather, 1=clock, 2=system)
- `_pending_dir` — IRQ-set direction; loop reads and clears
- `_last_press_ms` — debounce timestamp, shared across KEY0 and KEY1

**Scheduling timestamps:**
- `weather_view._last_refresh_ms` — when last full refresh happened
- `clock_view._last_sync_ms` — when last NTP sync was attempted
- `clock_view._last_render_min` — minute of last clock render (for change detection)

## Key Abstractions

**View Abstraction (3 implementations):**
- Purpose: Decouple view rendering and state from orchestration
- Pattern: Each view exports `render(oled)` (stateless painter), state setters (`set_*`), and predicates (`should_*`)
- Examples: `weather_view`, `clock_view`, `system_view`
- Constraint: Views do NOT import each other; composition is `main.py`'s responsibility

**Framebuffer-first Design:**
- Purpose: All drawing to in-memory `FrameBuffer`, then single `show()` push to hardware
- Pattern: Subclass `framebuf.FrameBuffer` in driver; views paint via inherited methods
- Benefit: No screen tearing, atomic refresh, trivial 180° rotation via pixel-level reads/writes

**Bootstrap 6-tuple:**
- Purpose: Separate network I/O from view logic; encode failure semantics in return value
- Pattern: `(ip, temp, code, is_day, tz_offset, wan_ip)` where `None` values indicate failure class
- Semantics: `ip=None` → no WiFi; `ip≠None, temp=None` → WiFi ok but API failed
- Benefit: Views can set correct cache status without exception handling

**Cache-Status State Machine (weather_view):**
- States: "pending" (initial), "connecting..." (boot pre-fetch), "ok" (valid data), "no_wifi", "no_data"
- Transitions: Driven by `set_data()` called from `main._refresh_all()` after each fetch
- Refresh intervals: 10 min if "ok", 60s if not (WEATHER-03, WEATHER-09)

## Entry Points

**Main Entry Point:**
- Location: `main.py:87–138` (`if __name__ == "__main__"` block)
- Triggers: Pico boots or user runs `main.py` via `mpremote run` or Thonny IDE
- Responsibilities:
  - `OLED` instantiation with rotation config
  - Button IRQ setup (debounce, direction)
  - Pre-fetch render (user feedback during bootstrap)
  - Blocking boot fetch + view state fan-out
  - Clock NTP sync attempt
  - Main poll loop: carousel nav, refresh scheduling, clock ticks, sync retries

**Deployment:**
- Files copied to Pico flash: `sh1107.py`, `main.py`, `bootstrap.py`, `icons.py`, `text_render.py`, `views/` package, `secrets.py`
- Execution: MicroPython runtime loads and runs `main.py`

## Architectural Constraints

- **Threading:** Single-threaded event loop. `bootstrap.fetch()` is blocking (20s WiFi timeout + <2s API round-trip). No async/await, no coroutines. Refresh blocks the poll loop; if visible delay is unacceptable, refactor to async via `asyncio` module (MicroPython 1.20+).
- **Global state:** All state is module-level in views or `main.py`. No singletons outside these files. Each view is a module, not a class, so caches are file-local. `OLED` is a class instance held in `main`'s scope.
- **Circular imports:** None. Dependency graph is strictly acyclic: `main.py` → {`sh1107`, `views.*`, `bootstrap`, `text_render`, `icons`}. Views do NOT import each other.
- **Memory model:** Framebuffer is 1024 bytes fixed (128×64 ÷ 8 bits/byte). Rotation creates a second 1024-byte buffer. Total ~2KB display memory + MicroPython heap for locals, imports, and cached API responses.
- **Hardware pinout:** Fixed by Waveshare HAT header — not user-configurable: DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1, KEY0=GP15, KEY1=GP17. Do not move pins without hardware redesign.
- **Network blocking:** `bootstrap.fetch()` blocks the main loop for up to 20s on a cold boot with no WiFi. Button presses during this window are still captured by IRQ handlers and dispatched after fetch returns. No timeout configuration per call; 20s hardcoded in `bootstrap._wifi_connect()`.

## Error Handling

**Strategy:** Graceful degradation via state machine. Failures update cache-status or `_synced` flag; views render appropriate fallback UI.

**Patterns:**
- **WiFi fail:** `bootstrap.fetch()` returns `(None, ...)` → `weather_view.set_data()` sets `_cache_status = "no_wifi"` → `weather_view.render()` displays "no wifi"
- **API fail (WiFi ok):** `bootstrap.fetch()` returns `(ip, None, ...)` → `weather_view.set_data()` sets `_cache_status = "no_data"` → `weather_view.render()` displays "no data"
- **NTP fail:** `clock_view.sync()` catches all exceptions, leaves `_synced = False` → `clock_view.render()` displays "--:--" with retry in 60s
- **File I/O fail (TZ offset persistence):** `clock_view.set_tz_offset()` wraps file write in try/except; silently fails, next boot retries
- **No exception bubbling:** All failures are trapped and converted to UI state. The main loop never crashes; it sleeps and retries.

## Cross-Cutting Concerns

**Refresh Scheduling:**
- `weather_view.should_refresh()` returns True every 10 min if cache is "ok", every 60s if not
- Implemented via `time.ticks_ms()` deltas; allows testing without real time passage
- Decoupled from view rendering

**NTP Sync Scheduling:**
- `clock_view.should_sync()` returns True after 6h if synced, every 60s if not
- First success sets `_synced = True` and starts the 6h timer
- Decoupled from clock rendering; can proceed in background

**Button Debounce:**
- Single `_last_press_ms` timestamp shared by both buttons (physical buttons won't fire within 50ms)
- Debounce threshold `_DEBOUNCE_MS = 50` tunable in `main.py:15`

**TZ Offset Persistence:**
- `clock_view` reads `tz_offset.txt` at module load (before `main.py` imports it)
- Writes only on change (flash-wear guard); stationary device writes once ever (first boot)
- Fallback: if file missing/malformed, `_cached_tz_offset = None`, next fetch populates it

---

*Architecture analysis: 2026-07-19*
