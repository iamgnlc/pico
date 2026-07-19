# Testing Patterns

**Analysis Date:** 2026-07-19

## Test Framework

**Status:** No host-side test framework configured

**Why:** This is a hardware-driven MicroPython project running directly on embedded hardware (Raspberry Pi Pico W). The codebase has no test runner, no mocking framework, and no unit test infrastructure. This is a deliberate design choice for embedded systems where:
- All verification happens on-device via interactive testing
- There are no host-side tests to run
- Hardware interaction (GPIO, SPI, WiFi, NTP) cannot be mocked in a meaningful way
- The cost of setting up a test harness exceeds the benefit for a small, single-file-per-module codebase

## Verification Approach

### Deployment & Runtime Verification

**Standard Workflow:**
```bash
mpremote cp sh1107.py main.py bootstrap.py icons.py text_render.py secrets.py :
mpremote cp -r views/ :
mpremote run main.py
```

**Or via Thonny IDE:**
1. Open project directory with Pico W selected as interpreter
2. Open `main.py` and press Run
3. Observe display and console output

### Manual Test Criteria

**On-Device Verification:**
The following are verified by human observation after deployment:

**Display & Rendering:**
- [ ] OLED display illuminates after boot (not blank/corrupted)
- [ ] Text renders correctly (correct font size, no pixel scrambling)
- [ ] Icons render for each weather code (sun, moon, cloud, rain, snow, thunder, fog) with correct visuals
- [ ] Temperature displays with proper scale (2x) and degree symbol (small circle)
- [ ] Page dots appear at y=60, correct number shown (3 dots for 3 views)
- [ ] Page dots highlight active view (filled) and inactive views (hollow)

**Navigation (Button Carousel):**
- [ ] KEY0 (GP15) moves to previous view (wraps from Weather to System)
- [ ] KEY1 (GP17) moves to next view (wraps from System to Weather)
- [ ] Transitions are immediate (no lag or debounce delay visible to user)
- [ ] Rapid presses do not skip views (debounce working)
- [ ] Page dots update to match visible view

**Weather View:**
- [ ] On first boot: displays "connecting..." while WiFi/API fetch in progress (~5-20 seconds)
- [ ] After successful fetch: displays icon + temperature in Celsius
- [ ] After WiFi failure: displays "no wifi"
- [ ] After API failure (network ok but endpoint unavailable): displays "no data"
- [ ] Auto-refreshes every 600 seconds (10 minutes) when online
- [ ] Retries every 60 seconds if fetch fails
- [ ] Time between refresh is measured via `time.ticks_diff()` (timing accurate to tick granularity)

**Clock View:**
- [ ] Displays "--:--" until NTP sync succeeds
- [ ] After first successful sync: displays HH:MM in 24-hour format
- [ ] Ticks every minute (updates when minute changes)
- [ ] Does not tick if unsynced or if timezone offset is not yet loaded
- [ ] Syncs from NTP at boot; retries every 60s until first success; then every 6 hours

**System View:**
- [ ] Displays SSID (truncated to 15 chars if necessary)
- [ ] Displays "SSID: --" when offline
- [ ] Displays WAN IP (from ip-api) only when WiFi connected AND IP fetch succeeded
- [ ] Displays "IP: --" when offline or before first fetch
- [ ] Shows signal strength as 4 bars (filled if level 1-4, hollow if level 0)
- [ ] Bar calculation matches RSSI thresholds: -55 dBm→4 bars, -65→3, -75→2, <-75→1

**Rotation:**
- [ ] `ROTATE = True` at top of `main.py:10` flips display 180°
- [ ] Change setting and reboot; display inverts correctly (all text/icons readable but upside-down)
- [ ] Rotation implemented via pixel-level transforms in `show()`, not byte manipulation

**Offline Degradation:**
- [ ] Disconnect WiFi (power off router or change ssid)
- [ ] Weather view shows "no wifi" and retries every 60s
- [ ] Clock view continues ticking if synced (time is local, not internet-dependent)
- [ ] System view shows "SSID: --", "IP: --", 0 bars
- [ ] Reconnect WiFi; fetch resumes and displays update

**Memory & Stability:**
- [ ] No crashes or REPL drops during normal operation
- [ ] Carousel cycles through all 3 views repeatedly without degradation
- [ ] Long-running test (>1 hour of cycling views + waiting for auto-refresh) remains stable

### Architecture Verification (Code Review)

**Module Isolation:**
- [ ] Each view module (`weather_view`, `clock_view`, `system_view`) has no imports of sibling views (verified: only `main.py` calls across views)
- [ ] Circular dependencies do not exist (verified by tracing `from`/`import` statements)

**State Guard Patterns:**
- [ ] `weather_view.set_data()` (line 47) guards against `None` and only stamps `_last_refresh_ms` once per setter call
- [ ] `clock_view.set_tz_offset()` (line 33) guards against `None` and unchanged values (idempotence, flash-wear protection)
- [ ] `system_view.set_wan_ip()` (line 31) guards against `None` and unchanged values

**Error Resilience:**
- [ ] `bootstrap.fetch()` (line 18) returns partial 6-tuple on API failure: `(ip, None, None, None, None, None)` if WiFi succeeded but API failed
- [ ] `bootstrap.fetch()` returns all-None tuple if WiFi fails: `(None, None, None, None, None, None)`
- [ ] Caller (`weather_view.set_data()`) distinguishes "no_wifi" from "no_data" via presence of `ip`
- [ ] `clock_view.sync()` (line 64) catches NTP errors silently; `_synced` remains False and render displays "--:--"
- [ ] File I/O errors in `clock_view.set_tz_offset()` (line 44) are silently caught; timezone offset remains loaded from previous boot or None

**Hardware Pin Configuration:**
- [ ] `sh1107.py:22-27` initializes SPI before DC pin to avoid GP8 floating (documented in CLAUDE.md gotcha #1)
- [ ] Pin objects kept in scope (`main.py:92-95`) so MicroPython does not garbage-collect them mid-IRQ

## Test Data

**No formal fixtures or test data generators used.** Verification uses real-world data:

**Real API Responses:**
- `ip-api.com` returns actual geolocation (latitude, longitude, timezone offset, public IP)
- `open-meteo.com` returns current weather (temperature, WMO code, is_day boolean)
- NTP servers return actual time via `ntptime.settime()`

**Fallback Test Scenarios:**
- Disconnect WiFi to trigger "no wifi" and "no data" states
- Edit `bootstrap.py` to point to invalid endpoint to trigger API error handling
- Remove `tz_offset.txt` to test persistence layer recovery
- Change `ROTATE = False` to test pixel-level rotation codepath

## Coverage

**Requirements:** No explicit coverage target enforced

**Tool:** Not applicable (no test framework)

**Known Coverage Gaps (require on-device observation):**
- `system_view._draw_bars()` (line 9) — tested visually by observing signal strength bars in System view
- `icons._sun()`, `._moon()`, `._cloud()`, `._rain()`, `._snow()`, `._thunder()`, `._fog()` — tested by fetching weather in each condition and observing icon render
- `text_render.text()` scale>1 codepath — tested by observing temperature display (scale=2) in Weather view
- `bootstrap._wifi_connect()` timeout path — tested by powering off WiFi and observing 20s timeout
- Rotation pixel-flip logic in `sh1107.show()` (line 66-76) — tested with `ROTATE=True` boot

## Test Structure

**No formal structure** due to on-device nature.

**Informal Checklist Approach:**
Each code change is verified against the manual test criteria above. Test criteria are documented in this file and in design documents (CLAUDE.md, PROJECT.md, STATE.md, design journal D-*.md files).

**Design Document References:**
- `D-11`, `D-12`: Button debounce timing
- `D-14`, `D-15`: Main loop timing (poll frequency, debounce window)
- `D-19`, `D-20`, `D-21`: Page dot rendering
- `D-31`: Refresh timestamp semantics (stamp at start for graceful degradation)
- `D-33`: NTP retry semantics
- `D-35`: NTP re-sync cadence (6h after first success)
- `D-36`: NTP retry cadence (60s until first success)
- `D-43-bis`: System view IP persistence (RAM-only, no file write)
- Design journal entries document rationale for timing constants, error handling, and UI feedback

## Mocking

**Not applicable.** No mocking framework used.

**Why:** 
- GPIO, SPI, framebuffer, WiFi, NTP, HTTP are MicroPython built-ins with no reasonable way to mock on host
- Testing these requires hardware interaction, which happens on-device only
- Small codebase and simple logic make unit mocking less valuable than integration testing

**Alternative Pattern Used Instead:**
- State guards in public setters (e.g., `set_data()` checks `if not ip:`) allow testing fallback paths via `bootstrap.fetch()` return tuples
- Graceful degradation pattern: all failures result in fallback cache state (e.g., "no_wifi", "no_data", "--:--") visible in render output
- Error handlers are minimal (bare `except Exception: pass` or return partial tuple) and testable via input observation

## Async Testing

**Not applicable.** No async/await in MicroPython (this firmware version does not support async syntax).

**Concurrency Model:**
- Single-threaded event loop in `main.py:116-138`
- Blocking WiFi/API calls during `_refresh_all()` call (lines 80-83)
- Button interrupts (IRQ handlers `_on_key0()`, `_on_key1()`) execute synchronously and set `_pending_dir` flag
- Main loop polls `_pending_dir` and processes navigation on next tick

**How to Test Timing:**
- Press buttons during blocking WiFi fetch (~5-20s window); verify pending direction is captured and executed after fetch completes
- Observe that view switch happens immediately after weather fetch (no lag), meaning button IRQ is not blocked by framebuffer operations

## Common Patterns

**Scheduling Pattern (`should_refresh()` in views):**
```python
def should_refresh(now_ms):
    interval = _REFRESH_MS if _cache_status == "ok" else _RETRY_MS
    return time.ticks_diff(now_ms, _last_refresh_ms) >= interval
```
Tested by:
1. Observing that weather updates every 600s (10 min) when online
2. Observing that weather retries every 60s when offline
3. Measuring timestamp via `mpremote` or Thonny console output

**Timestamp Guard Pattern (`set_data()` in `weather_view.py:51`):**
```python
_last_refresh_ms = time.ticks_ms()
```
Stamped at entry so transient failures (e.g., API timeout) don't tight-loop the scheduler.

Tested by:
1. Triggering API error (break internet or invalid endpoint)
2. Observing single "no data" message for 60 seconds (no repeat requests)
3. Waiting for 60s retry window to complete

**Idempotence Guard Pattern (`set_tz_offset()` in `clock_view.py:39-42`):**
```python
if offset is None:
    return
if offset == _cached_tz_offset:
    return
```
Prevents unnecessary file writes (flash wear) when timezone does not change.

Tested by:
1. Powering device on multiple times in same location
2. Observing that `tz_offset.txt` file size does not grow (only written once on first boot)

**Debounce Pattern (`_on_key0()` in `main.py:49-55`):**
```python
now = time.ticks_ms()
if time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS:
    return
_last_press_ms = now
_pending_dir = -1
```
Tested by:
1. Rapidly pressing button multiple times
2. Observing that view advances only once per debounce window (50ms)

---

*Testing analysis: 2026-07-19*
