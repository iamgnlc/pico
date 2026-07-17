---
phase: 02-carousel-+-weather
verified: 2026-07-17
status: passed
human_verified: 2026-07-17
score: 10/10 must-haves verified in code and on-device (5/5 SC + 10/10 requirements + 13/13 decisions)
post_verification_fixes:
  - "376615d fix(02): restore temp y-anchor to vertical center (y=32)"
  - "db94c78 fix(02): suppress spinner during 'connecting...' (pending cache)"
mode: mvp
overrides_applied: 0
gaps: []
deferred:
  - truth: "SC1: KEY0/KEY1 redraw within one frame — user-perceived <150ms latency"
    addressed_in: "End-of-phase human-verify batch (workflow.human_verify_mode=end-of-phase)"
    evidence: "Code path verified — 100ms poll tick + single framebuf pass; physical measurement deferred"
  - truth: "SC2: Wrap at both ends observably works on the physical device"
    addressed_in: "End-of-phase human-verify batch"
    evidence: "Modulo math verified in code; on-device confirmation deferred"
  - truth: "SC3: Every cold boot lands on Weather"
    addressed_in: "End-of-phase human-verify batch"
    evidence: "_current_idx = 0 at module scope with no persistence; on-device confirmation deferred"
  - truth: "SC4: Page dots update visibly on each button press"
    addressed_in: "End-of-phase human-verify batch"
    evidence: "_draw_page_dots called after every render pass; visual confirmation deferred"
  - truth: "SC5 spinner is visibly animating for at least one frame during the fetch phase"
    addressed_in: "End-of-phase human-verify batch (D-23 acceptance criterion)"
    evidence: "_draw_spinner + oled.show() invoked between wifi.connect and urequests.get in refresh(); visual capture deferred"
human_verification:
  - test: "Cold-boot connecting screen"
    expected: "Within 1-2s of power-on, OLED shows 'connecting...' + three page dots (left dot filled), NOT a black screen"
    why_human: "Requires flashing to Pico and observing panel"
  - test: "KEY0/KEY1 responsiveness"
    expected: "Press-to-visible-view-change latency under ~150ms; every physical press advances exactly one view (debounce)"
    why_human: "Requires physical button presses on hardware"
  - test: "Wrap-around navigation"
    expected: "KEY0 on Weather (dot 0) wraps to System (dot 2); KEY1 on System wraps to Weather"
    why_human: "Requires physical button presses"
  - test: "Page-dot visual state"
    expected: "Three dots at bottom-center visible on every view; exactly one is filled (matching current view), the other two are hollow rings"
    why_human: "Requires visual observation of physical panel"
  - test: "Weather cache instant-redraw on view-switch (WEATHER-04)"
    expected: "After first successful fetch, navigating Weather->Clock->System->Weather redraws instantly from cache with no spinner and no perceptible delay"
    why_human: "Requires physical carousel navigation timing"
  - test: "Spinner visible during HTTP fetch (D-23)"
    expected: "During the initial boot after wifi.connect succeeds and before urequests returns, a spinner ring at (88,20) with one indicator pixel is visible for at least one frame"
    why_human: "Requires slow-motion video or camera capture — fetch phase is brief"
  - test: "600s auto-refresh cadence (WEATHER-03)"
    expected: "After boot, the Weather cache updates approximately every 600 seconds regardless of current view; recommended shortcut: temporarily set _REFRESH_MS=30_000 for a fast verification and revert"
    why_human: "Requires wall-clock time waiting; hardware only"
  - test: "Error state graceful degradation (WEATHER-05)"
    expected: "Boot with wrong WIFI_PASSWORD in secrets.py -> 'no wifi' + page dots visible on Weather view; KEY0/KEY1 still cycle to blank Clock/System (dot moves); no crash, no REPL drop"
    why_human: "Requires modifying secrets.py, flashing, and physical button presses"
  - test: "180 rotation still correct (regression sanity)"
    expected: "With ROTATE=True (current default), content renders right-side-up on the physical panel. sh1107.py has zero diff since Phase 2 planning, so no regression expected — but confirm on-device"
    why_human: "Requires physical panel observation"
---

# Phase 2: Carousel + Weather Verification Report

**Phase Goal:** Pressing KEY0/KEY1 cycles through all three views; the Weather view is fully functional
**Mode:** mvp
**Verified:** 2026-07-17
**Status:** human_needed
**Re-verification:** No — initial verification of a goal-backward audit against shipped code

## Summary

All ten Phase 2 requirements (NAV-01..06, WEATHER-02..05) have concrete code paths in the shipped source. All five ROADMAP Success Criteria trace to actual lines. sh1107.py has zero diff since planning commit `aac69f7` — the four SH1107 gotchas are untouched. All 13 locked decisions (D-13..D-25) shipped as designed. No BLOCK-severity findings.

However, the phase goal is a user-story ("Pressing KEY0/KEY1 cycles through all three views; the Weather view is fully functional"), and all five Success Criteria are user-facing behaviors that require physical hardware to observe (button responsiveness, page-dot visual state, spinner visibility, cache-instant redraw, error-state navigability). Per `workflow.human_verify_mode: end-of-phase`, on-device verification is deferred to the end-of-phase batch. This report confirms the code is READY for that batch; PASS versus PARTIAL versus FAIL for the phase as a whole is determined by that hardware pass.

Verdict: `## VERIFICATION PARTIAL` — code is delivered; user-visible acceptance is deferred to hardware.

## User Flow Coverage (MVP Mode)

The phase goal is a User Story (implicit): _As the device user, I want to press KEY0/KEY1 to cycle through the Weather / Clock / System views, so that I can navigate to the currently useful screen without touching a computer._

| Step | Expected | Evidence In Code | Status |
|------|----------|------------------|--------|
| 1. Cold boot | Device powers on -> shows Weather view within seconds | `main.py:77` (`oled = OLED(rotate=ROTATE)`), `main.py:90-92` (pre-fetch connecting render + dots + show), `main.py:97` (boot refresh) | Verified in code (visual deferred) |
| 2. Press KEY1 | View advances forward within one poll tick | `main.py:59-65` (_on_key1 sets _pending_dir=+1), `main.py:101-108` (loop applies) | Verified in code (visual deferred) |
| 3. Press KEY0 | View advances backward within one poll tick | `main.py:50-56` (_on_key0 sets _pending_dir=-1), `main.py:101-108` (loop applies) | Verified in code (visual deferred) |
| 4. Wrap at boundaries | KEY0 on view 0 -> view 2; KEY1 on view 2 -> view 0 | `main.py:104` (`(_current_idx + _pending_dir) % 3` — Python `%` on positive divisor always non-negative: `-1 % 3 = 2`, `3 % 3 = 0`) | Verified in code (visual deferred) |
| 5. Page dots on every view | Three dots at bottom; active is filled, others hollow | `main.py:68-73` (_draw_page_dots), invoked at `main.py:91, 98, 107, 115` | Verified in code (visual deferred) |
| 6. Return to Weather is instant | Cache-based redraw, no fetch | `weather_view.py:43-58` (render draws from cache), `main.py:106` (VIEWS[idx].render on switch) | Verified in code (visual deferred) |
| 7. Weather stays fresh | 600s auto-refresh regardless of current view | `weather_view.py:14, 39-40` (_REFRESH_MS + should_refresh), `main.py:109-116` (scheduler branch) | Verified in code (600s wall-clock deferred) |
| 8. Failures don't lock the carousel | 'no wifi' / 'no data' on Weather; navigation still works | `weather_view.py:47-50` (error copy), `weather_view.py:74-76, 86-88` (status transitions), `main.py:104-108` (nav dispatch unaffected) | Verified in code (visual deferred) |

## Goal Achievement

### Observable Truths — ROADMAP Success Criteria

| # | Truth (Success Criterion) | Status | Evidence |
|---|---------------------------|--------|----------|
| SC1 | Pressing KEY1 advances to next view and the screen redraws within one frame; KEY0 goes back | VERIFIED (code path) | main.py:50-65 (IRQ handlers set _pending_dir), main.py:101-108 (poll loop dispatches within _POLL_MS=100ms). Physical <150ms confirmation deferred. |
| SC2 | KEY0 on Weather wraps to System; KEY1 on System wraps to Weather | VERIFIED (code path) | main.py:104 uses `(_current_idx + _pending_dir) % 3`. `-1 % 3 == 2` (KEY0 from idx 0 -> 2), `3 % 3 == 0` (KEY1 from idx 2 -> 0). Modulo semantics correct in MicroPython. Visual confirmation deferred. |
| SC3 | On every boot the device starts on Weather; Clock and System reachable via navigation | VERIFIED (code path) | main.py:25 `_current_idx = 0` (module scope, no persistence); main.py:28 `VIEWS = (weather_view, clock_view, system_view)`. Weather at index 0 (boot value). Boot sequence at main.py:77-99 renders Weather first. |
| SC4 | Three page dots at the bottom show active position, updating on each button press | VERIFIED (code path) | main.py:68-73 `_draw_page_dots` draws three dots at (52,60), (64,60), (76,60) with r=2; filled=is_active. Called at main.py:91, 98, 107, 115 — after every view render including view-switch. |
| SC5 | Weather view: condition icon + 600s refresh + on-view-switch redraw + no-wifi/no-data without crash | VERIFIED (code path) | Icon: weather_view.py:52 `icons.draw(oled, 16, 16, _cached_code, _cached_is_day)`. 600s: weather_view.py:14 `_REFRESH_MS = 600_000` + weather_view.py:39-40 predicate + main.py:109-116 scheduler branch. On-switch redraw: weather_view.py:43 render() from cache (no fetch). Error paths: weather_view.py:47-50 renders "no wifi"/"no data"; navigation dispatch unaffected. |

**Score:** 5/5 Success Criteria have verified code paths. User-visible acceptance deferred to on-device batch.

## Requirement Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| NAV-01 | KEY0 (GP15) previous; KEY1 (GP17) next | SATISFIED | `main.py:17-18` (`_KEY0_PIN = 15`, `_KEY1_PIN = 17`), `main.py:50-56` (_on_key0 sets -1), `main.py:59-65` (_on_key1 sets +1), `main.py:81-84` (Pin construction + IRQ install with FALLING trigger) |
| NAV-02 | Debounce so one physical press = one view change | SATISFIED | `main.py:16` (`_DEBOUNCE_MS = 50`), `main.py:52-54` and `main.py:61-63` compare `time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS` and early-return on chatter |
| NAV-03 | Carousel wraps at both ends | SATISFIED | `main.py:104` `_current_idx = (_current_idx + _pending_dir) % 3` — Python modulo on positive divisor produces natural wrap for both directions |
| NAV-04 | Device boots to Weather on every startup | SATISFIED | `main.py:25` `_current_idx = 0` (module scope; no persistence layer anywhere). VIEWS tuple at `main.py:28` puts weather_view at index 0. |
| NAV-05 | Page-dot indicator shows carousel position | SATISFIED | `main.py:68-73` `_draw_page_dots(oled, current_idx)` renders three dots at y=60 with r=2, filled active + hollow inactive |
| NAV-06 | View switch triggers immediate redraw | SATISFIED | `main.py:103-108` in poll loop calls `VIEWS[_current_idx].render(oled)` + dots + show() when `_pending_dir != 0`. Worst-case latency ~= _POLL_MS (100ms) + one framebuf pass. For Weather, render reads from cache (no I/O). |
| WEATHER-02 | Condition icon renders | SATISFIED | `weather_view.py:52` `icons.draw(oled, 16, 16, _cached_code, _cached_is_day)` — canonical (16,16) coord preserved from pre-refactor. Fires when `_cache_status == "ok"`. |
| WEATHER-03 | Auto-refresh every 600s | SATISFIED | `weather_view.py:14` `_REFRESH_MS = 600_000`, `weather_view.py:15` `_last_refresh_ms = 0`, `weather_view.py:39-40` `should_refresh(now_ms)` predicate, `main.py:109-116` scheduler branch fires refresh regardless of current view. Timestamp stamped at start of refresh (weather_view.py:65) prevents transient-failure tight-loop. |
| WEATHER-04 | Refresh immediately when navigated to | SATISFIED (per D-22 semantic) | Interpretation per D-22 is "redraw immediately from cache", not "re-fetch API". `main.py:106` `VIEWS[_current_idx].render(oled)` on switch; for Weather, `weather_view.py:43-58` reads module-level cache (no I/O). |
| WEATHER-05 | Error state without crash; carousel remains navigable | SATISFIED | `weather_view.py:47-50` renders "no wifi" / "no data" inside content area (rows 0-53); `main.py:107-108, 115-116` still calls `_draw_page_dots + oled.show()` after every render pass so dots stay visible during errors. Navigation dispatch in `main.py:103-108` is independent of `_cache_status` — pressing keys during error state still switches views. |

**Score:** 10/10 requirements have satisfied code paths. Behavioral verification deferred to hardware.

## Locked-Decision Coverage (D-13 through D-25)

| Decision | Content | Status | Evidence |
|----------|---------|--------|----------|
| D-13 | KEY0/KEY1 use `Pin.irq(FALLING)`; handler stamps `_pending_dir` | SHIPPED | main.py:83-84 IRQ install with FALLING; main.py:56 (KEY0 -> -1), main.py:65 (KEY1 -> +1) |
| D-14 | Software debounce via `time.ticks_ms()` in IRQ; 30-80ms band | SHIPPED | main.py:16 `_DEBOUNCE_MS = 50` (mid-band); main.py:52-54, 61-63 compare with early return |
| D-15 | Poll scheduler via `ticks_ms + ticks_diff`; no asyncio, no Timer | SHIPPED | main.py:102 `now = time.ticks_ms()`; main.py:117 `time.sleep_ms(_POLL_MS)`; grep shows zero asyncio/Timer occurrences |
| D-16 | Three flat files at repo root, no views/ subdir | SHIPPED | `ls /Users/gnlc/Code/pico/display/*.py` shows weather_view.py, clock_view.py, system_view.py all at repo root; no views/ directory |
| D-17 | Each view exposes `render(oled)`; owns module-level state | SHIPPED | weather_view.py:43 `def render(oled):`, clock_view.py:1 same, system_view.py:1 same. weather_view.py:9-16 owns cache tuple + refresh timestamp + spinner frame |
| D-18 | main.py owns VIEWS tuple + `_current_idx` int | SHIPPED | main.py:25 `_current_idx = 0`; main.py:28 `VIEWS = (weather_view, clock_view, system_view)` (order matches: Weather=0, Clock=1, System=2) |
| D-19 | Dots at y=60; rows 54-63 reserved; content in 0-53 | SHIPPED | main.py:73 `oled.ellipse(cx, 60, 2, 2, 1, i == current_idx)` — y=60 as specified. Weather content: temp centered at y=26 (weather_view.py:54); spinner at y=20 (weather_view.py:32); degree ring cy=20 (weather_view.py:57). All content inside rows 0-53. |
| D-20 | Filled active + hollow inactive via `fb.ellipse(...)` | SHIPPED | main.py:73 uses ellipse(cx, 60, 2, 2, 1, is_active) — same idiom as icons.py |
| D-21 | Three dots, r=2, 12px spacing, centers x=52/64/76 | SHIPPED | main.py:72 `cx = 52 + i * 12` -> 52, 64, 76 for i in {0,1,2}; r=2 per D-20 evidence |
| D-22 | On-switch redraws from cache; 600s cadence decoupled | SHIPPED | render() reads cache only (weather_view.py:43-58, zero network calls); scheduler predicate (should_refresh) is called on every poll tick independently of _pending_dir handling (main.py:109) |
| D-23 | Two boot visuals: "connecting..." during wifi.connect; spinner during HTTP | SHIPPED | "connecting...": weather_view.py:12 `_cache_status = "pending"` initial value; weather_view.py:45-46 renders "connecting..."; main.py:90-92 draws it BEFORE the blocking `weather_view.refresh(oled)` at main.py:97. Spinner: weather_view.py:25-36 `_draw_spinner`, invoked at weather_view.py:82 between wifi.connect and weather.current, followed by `oled.show()` at weather_view.py:83 to flush the frame. |
| D-24 | Clock/System stubs are fully blank; only `oled.fill(0)` | SHIPPED | clock_view.py = 2 lines total: `def render(oled):\n    oled.fill(0)`. system_view.py identical. No text_render/icons imports. |
| D-25 | Error copy: 'no wifi' when wifi.connect fails; 'no data' when weather.current returns Nones | SHIPPED | weather_view.py:47-48 renders "no wifi" when `_cache_status == "no_wifi"` (set at :75 after wifi.connect returns falsy); weather_view.py:49-50 renders "no data" for "no_data" state (set at :87 after temp is None). Text position y=26 (within reserved rows 0-53). |

**Score:** 13/13 locked decisions shipped as designed. No deviations.

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `weather_view.py` | Cache + refresh + spinner + render-from-cache + should_refresh | VERIFIED | 95 lines. Defines: `_center_text`, `_draw_spinner`, `should_refresh`, `render`, `refresh`. Module state: `_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status`, `_REFRESH_MS`, `_last_refresh_ms`, `_spinner_frame`. Zero calls to `oled.show()` in render (only one call in refresh, to flush the spinner). |
| `clock_view.py` | Blank stub `render(oled)` | VERIFIED | 2 lines. Only `def render(oled): oled.fill(0)`. No text, no icons. |
| `system_view.py` | Blank stub `render(oled)` | VERIFIED | 2 lines. Identical structure to clock_view.py. |
| `main.py` | Carousel host: VIEWS, IRQ, poll scheduler, page dots, missing-secrets fallback | VERIFIED | 117 lines. All required elements present: VIEWS tuple, `_current_idx=0`, `_pending_dir=0`, `_last_press_ms=0`, `_KEY0_PIN=15`, `_KEY1_PIN=17`, `_POLL_MS=100`, `_DEBOUNCE_MS=50`, `_on_key0/1`, `_draw_page_dots`, missing-secrets `try/except ImportError` block (main.py:38-47). |
| `sh1107.py` | Unchanged (byte-for-byte) since planning commit aac69f7 | VERIFIED | `git log aac69f7..HEAD -- sh1107.py` returns zero commits; `git diff aac69f7..HEAD -- sh1107.py` empty. Four SH1107 gotchas remain intact at documented line ranges. |

## Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| main.py IRQ handlers | module-level flags (`_pending_dir`, `_last_press_ms`) | Pin.irq(FALLING) sets int; loop reads and clears | WIRED | main.py:83-84 install; main.py:50-56, 59-65 handlers assign to globals; main.py:103-105 reads + clears |
| main.py poll loop | VIEWS[_current_idx].render(oled) | tuple lookup + call after _draw_page_dots + oled.show() | WIRED | main.py:106-108 (view-switch), main.py:114-116 (post-refresh redispatch) |
| main.py._draw_page_dots | oled.ellipse at x=52,64,76 y=60 r=2 | for-loop with filled=is_active | WIRED | main.py:71-73 |
| main.py poll loop | weather_view.should_refresh(now) | predicate call each tick | WIRED | main.py:109 |
| main.py boot | weather_view.refresh(oled) | one blocking call at boot | WIRED | main.py:97 |
| main.py scheduler | weather_view.refresh(oled) | 600s cadence pass | WIRED | main.py:110 (count of `weather_view.refresh(oled)` calls in main.py = 2 as specified) |
| weather_view.refresh | spinner frame + show between wifi.connect and weather.current | at least one animated frame drawn before HTTP GET | WIRED | weather_view.py:81-83 (render + _draw_spinner + oled.show sequence between :73 wifi.connect and :85 weather.current) |
| main.py:import weather_view | weather_view module scope | evaluated at boot | WIRED (safe) | weather_view.py module scope no longer imports secrets (fixed by commit b0c8477); main.py:38-47 missing-secrets fallback is now reachable on ImportError of `import secrets` at main.py:39 |

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| weather_view.render | `_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status` | Written by `refresh()` at weather_view.py:91-94 after real API call to `weather.current()` at :85; initial state "pending" produces "connecting..." UI | Yes (via refresh -> weather.current -> ip-api + open-meteo) | FLOWING |
| main._draw_page_dots | `_current_idx` (int) | Written by main.py:104 from `_pending_dir` set in IRQ handlers | Yes (from physical button IRQ) | FLOWING |
| main scheduler branch | return value of `weather_view.should_refresh(now)` | Predicate compares `time.ticks_diff(now, _last_refresh_ms)` to `_REFRESH_MS`; `_last_refresh_ms` stamped inside `refresh()` at weather_view.py:65 | Yes (real time source) | FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| main.py parses as Python 3 | `python3 -c "import ast; ast.parse(open('main.py').read())"` | exit 0 | PASS |
| weather_view.py parses | same | exit 0 | PASS |
| clock_view.py parses | same | exit 0 | PASS |
| system_view.py parses | same | exit 0 | PASS |
| sh1107.py zero diff since aac69f7 | `git log aac69f7..HEAD -- sh1107.py` | empty | PASS |
| wifi.py/weather.py/icons.py/text_render.py zero diff since aac69f7 | `git log aac69f7..HEAD -- wifi.py weather.py icons.py text_render.py` | empty | PASS |
| No debt markers (TBD/FIXME/XXX/TODO/HACK) in any .py file | grep | zero matches | PASS |
| No f-strings anywhere in .py sources | grep | zero matches | PASS |
| No asyncio, no machine.Timer | grep | zero matches | PASS |
| No type hints on function params | grep | zero matches | PASS |
| Runtime boot | Cannot run on host — MicroPython on Pico W required | N/A | SKIP (deferred to hardware) |

## Probe Execution

No `scripts/*/tests/probe-*.sh` conventional probes exist in this project (this is a MicroPython on-device project — everything runs on the Pico, per CLAUDE.md "everything runs on-device; there are no host-side tests"). No probes declared in PLAN/SUMMARY files. Section: SKIPPED (no runnable probes; on-device human-verify batch serves as the equivalent).

## Coordinate-Math Verification (Dimension 10)

All coordinates confirmed within the 128x64 canvas AND within reserved rows 0-53 for view content (per D-19).

| Element | Coordinates | Extent | Canvas fit | D-19 fit (0-53) |
|---------|-------------|--------|------------|-----------------|
| Page dots | (52, 60), (64, 60), (76, 60), r=2 | x=50..78, y=58..62 | inside 0..127 x 0..63 | inside dot strip 54-63 (by design) |
| Temperature | anchor (88, 26), scale=2, "19" = 2 chars | w=8*2*2=32; x=88-16..88+16 = 72..104; h=16, y=18..33 | inside canvas | inside 0-53 |
| Degree ring | cx = 88 + w//2 + 5 = 88+16+5 = 109 (for "19"), cy = 20, r=2 | x=107..111, y=18..22 | inside canvas | inside 0-53 |
| "connecting..." (13 chars) | (64, 26), scale=1 | w=13*8=104; x=64-52..64+52=12..116; h=8, y=22..30 | inside canvas | inside 0-53 |
| "no wifi" (7 chars) / "no data" (7 chars) | (64, 26), scale=1 | w=56; x=36..92, y=22..30 | inside canvas | inside 0-53 |
| Spinner ring | (88, 20), r=4 | x=84..92, y=16..24 | inside canvas | inside 0-53 |
| Spinner indicator pixel | (88 + dx, 20 + dy) where (dx,dy) in ((0,-4),(4,0),(0,4),(-4,0)) | in {(88,16), (92,20), (88,24), (84,20)} | inside canvas | inside 0-53 |
| Weather condition icon | (16, 16), typical glyph size ~24x24 in icons.py | approx x=4..28, y=4..28 | inside canvas | inside 0-53 |

All 8 elements: FIT.

## Anti-Patterns Found

None. All probes:
- Debt markers (TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER): 0 matches
- f-strings: 0 matches
- asyncio / machine.Timer: 0 matches
- Type hints on def signatures: 0 matches
- Docstrings: 0 matches (per CONVENTIONS.md)
- Console.log-only implementations: N/A (MicroPython; no console.log)
- Empty return placeholders in Phase-2 files: 0 (return path clock_view/system_view/render() has no return, correctly implicit None; that is by design per D-24 "blank stubs")
- Per-frame allocations in render loop: 0 in main.py poll loop; `now = time.ticks_ms()` is an int local, no allocation. Framebuf writes reuse the shared 1024-byte buffer.
- Per-frame allocations in IRQ handler: 0. `_on_key0`/`_on_key1` bodies: `time.ticks_ms()` (int return), `time.ticks_diff` (int return), two int assignments to module scope. No `.format`, no f-strings, no `print`, no list/dict/tuple literals.
- Pin objects held as locals for GC pinning: main.py:81-82 (`key0`, `key1`) — YES, per plan requirement.
- Atomic single-int writes from IRQ: `_pending_dir`, `_last_press_ms`, `_current_idx` are all ints. Assignments to module-level ints on Cortex-M0+ are effectively atomic (word-aligned single-store). SAFE.

## SH1107 Invariant

| Gotcha | Enforced? | Evidence |
|--------|-----------|----------|
| 1. 0x21 single-byte command | UNCHANGED | sh1107.py:50 still sends `0x21` alone in the init tuple |
| 2. CS toggle per data byte in show() | UNCHANGED | sh1107.py:86-90 unchanged |
| 3. Framebuf-pixel rotation, not byte-shuffle | UNCHANGED | sh1107.py:65-74 pixel-by-pixel rotation loop unchanged |
| 4. MONO_HMSB framebuf format | UNCHANGED | sh1107.py:30 and :69 both use `framebuf.MONO_HMSB` |
| sh1107.py itself | ZERO DIFF since aac69f7 | `git log aac69f7..HEAD -- sh1107.py` empty; `git diff aac69f7..HEAD -- sh1107.py` empty |
| New Phase-2 code violates any gotcha? | NO | Phase-2 code (main.py, weather_view.py, clock_view.py, system_view.py) contains no raw SPI writes, no `framebuf.MONO_VLSB`, no `self.cs`/`self.dc` manipulation, no `0xA1`/`0xC8` command sends. All display interaction goes through the existing `OLED` class API (`fill`, `ellipse`, `pixel`, `show`, `text`). |

## Anti-Criteria (per-plan)

| Plan | Anti-criterion | Status |
|------|----------------|--------|
| 02-01 | No sh1107.py diff | HOLDS (zero commits touched sh1107.py) |
| 02-01 | No new external deps | HOLDS (no new imports beyond stdlib + existing project files) |
| 02-01 | No f-strings | HOLDS (grep finds none) |
| 02-01 | No type hints | HOLDS (grep finds none) |
| 02-01 | No docstrings | HOLDS (grep finds none) |
| 02-02 | No sh1107.py diff | HOLDS |
| 02-02 | No asyncio, no machine.Timer | HOLDS (grep finds none) |
| 02-02 | No views/ subdirectory or `__init__.py` | HOLDS (ls shows only flat files) |
| 02-02 | Stub views must not render any text | HOLDS (clock_view.py + system_view.py: 2 lines each, only `oled.fill(0)`) |
| 02-02 | No 600s auto-refresh code in Plan 02 | HOLDS by scope; Plan 02-03 added the scheduler, which was the plan-authored progression |
| 02-03 | No sh1107.py diff | HOLDS |
| 02-03 | No retry logic | HOLDS (grep for `for.*range.*retry|while.*retry|retry.*=` finds none) |
| 02-03 | No asyncio, no machine.Timer | HOLDS |
| 02-03 | No new external packages | HOLDS (only stdlib `time` added to weather_view.py) |

All anti-criteria pass.

## Plan 02-02 -> 02-03 Boundary Fix (Dimension 9)

The out-of-band scope fix `b0c8477 fix(02-02): lazy-import secrets in weather_view.refresh` landed between Plan 02-02 and Plan 02-03 to restore missing-secrets fallback reachability.

| Check | Status | Evidence |
|-------|--------|----------|
| Fix is present in weather_view.py as of HEAD | YES | `weather_view.py:71` (`import secrets` inside `refresh()` body). Module-scope `import secrets` at line 3-6 area is absent (grep confirms `import secrets` appears only at line 71 in weather_view.py and only at line 39 inside main.py's try/except). |
| main.py missing-secrets fallback reachable in boot import chain | YES | Boot order in main.py:1-7: `from sh1107 import OLED, WIDTH, HEIGHT`, `from machine import Pin`, `import weather_view`, `import clock_view`, `import system_view`, `import text_render`, `import time`. `import weather_view` at line 3 no longer triggers `import secrets` (since fix). Then main.py:38-47 executes the `try: import secrets / except ImportError:` block; on ImportError it initializes OLED, renders "missing / secrets.py", and enters an infinite sleep loop. |
| Would the fallback fire on ImportError of secrets? | YES | If `secrets.py` is missing, main.py:39 `import secrets` raises ImportError, main.py:40 except branch fires, OLED is initialized, message rendered, `time.sleep(3600)` loop halts execution before `if __name__ == "__main__":` runs. `weather_view.refresh()` is never called in this state (execution halted). D-04 preserved. |

## Cross-Summary Consistency (Dimension 8)

| Summary Claim | Verified? |
|---------------|-----------|
| 02-01 commits: `b669210`, `caea2fe` | YES (both in `git log`) |
| 02-02 commits: `a2b3cf5`, `b0a60d1`, `429a6e9` | YES |
| 02-03 commits: `289f5b2`, `c8271d9` | YES |
| Boundary fix commit: `b0c8477` | YES |
| 02-01 main.py delta -20 lines (57 -> 37) | CONSISTENT (git show caea2fe: `main.py | 23 ++---------------------` and b669210 has weather_view.py +32; math checks out) |
| 02-01 weather_view.py 32 lines | CONSISTENT (`b669210` +32 insertions) |
| 02-02 weather_view.py delta +23 lines | CONSISTENT (`b0a60d1` +51-15 boundary counted approx.; final line count 55 matches summary) |
| 02-02 main.py 100 lines | CONSISTENT (b0c8477 +5-1 = +4 mid-boundary, then plan-03 c8271d9 +17 = 117 final actual) |
| 02-03 weather_view.py 91 lines (55->91 = +36) | CLOSE — actual current is 95 lines. Discrepancy: 91 (summary) vs 95 (actual). Minor, likely trailing whitespace / blank-line counting difference or the boundary-fix +4 was double-counted somewhere. Not a functional issue. Flag as informational. |
| 02-03 main.py 117 lines (100->117 = +17) | CONSISTENT (actual `wc -l` = 117) |

Line-count discrepancy noted (weather_view.py: summary claims 91, actual is 95). Non-load-bearing; the code is behaviorally correct.

## Credential-Leak Regression Check (Dimension 7)

`grep -R "WIFI_SSID|WIFI_PASSWORD"` in the Phase 2 planning artifacts finds only variable-name references — no literal SSID or password values. Same in the git log for all Phase-2 commits (`git log aac69f7..HEAD` shows nothing matching credential-string patterns). Phase 1's redacted-string leak concern does not re-emerge here.

## Gaps Summary

No BLOCK-severity gaps found. The phase goal is a user-facing behavior that requires on-device observation for final acceptance; that acceptance is deferred per `workflow.human_verify_mode: end-of-phase` and is not a gap the executor could have closed here.

FLAG-severity items (informational):
1. **Line-count discrepancy in 02-03-SUMMARY.md:** claims weather_view.py is 91 lines but actual is 95. Non-functional.
2. **Overlap between spinner (y=16..24) and "connecting..." text (y=22..30):** noted in the plan and by the executor as a "planner-permitted interpretation of D-23". Fallback ring coordinate (108, 20) documented in 02-03-PLAN.md line 172 if visually poor on-device. Not a code defect; a visual-design decision requiring on-device judgment.

---

## VERIFICATION PARTIAL

Phase 2 code delivers all 10 required behaviors (NAV-01..06, WEATHER-02..05) and all 5 ROADMAP Success Criteria via verified code paths. All 13 locked decisions (D-13..D-25) shipped as designed. sh1107.py has zero diff since planning (`aac69f7`) — the four SH1107 gotchas remain untouched. No BLOCK-severity findings.

However, the phase goal is a User Story whose success is directly observable only on the physical Pico (button responsiveness, page-dot visual state, spinner visibility, cache-instant redraw, error-state carousel navigability). Per project configuration `workflow.human_verify_mode: end-of-phase`, on-device verification is deferred to the end-of-phase human-verify batch. The code is READY for that batch. Nine specific human-verify items are enumerated in the `human_verification` frontmatter section and inline above.

**Report path:** `/Users/gnlc/Code/pico/display/.planning/phases/02-carousel-+-weather/02-VERIFICATION.md`

**Recommendation to orchestrator:** treat this phase as `human_needed` — code is landed and verified against every locked decision, requirement, and success criterion at the source-code layer; the remaining work is the physical-hardware verification pass that only the operator can perform. If that pass succeeds, upgrade this verdict to PASSED via a follow-up VERIFICATION.md entry (or a "verification confirmed on-device" annotation) and mark Phase 2 complete in ROADMAP.md.

_Verified: 2026-07-17_
_Verifier: Claude (gsd-verifier)_
