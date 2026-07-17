# Phase 2: Carousel + Weather - Context

**Gathered:** 2026-07-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current single-view, `time.sleep(REFRESH_SECONDS)` main loop with a `time.ticks_ms()`-driven poll scheduler that services button interrupts and per-view refresh cadence at the same time. Ship three views — Weather (fully implemented), Clock (stub), System (stub) — reachable via KEY0 (prev) / KEY1 (next), wrapping at both ends, always booting to Weather, with a three-dot position indicator at the bottom edge. The Weather view keeps its existing icon + degree-ring temperature render (Phase 1 output) and adds an on-view-switch redraw of cached data plus a boot-time "connecting..." / spinner sequence.

**Covers:** NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06, WEATHER-02, WEATHER-03, WEATHER-04, WEATHER-05 (10 requirements)

**Not in this phase:** Real Clock rendering (Phase 3), real System diagnostics (Phase 4), long-press semantics (v2), view persistence across reboots (out of scope by design).

</domain>

<decisions>
## Implementation Decisions

### Button input + debounce
- **D-13:** KEY0 and KEY1 use `machine.Pin.irq(trigger=Pin.IRQ_FALLING)` handlers. Each handler stamps a module-level `_pending_dir` variable (-1 for KEY0 / +1 for KEY1) which the main loop reads and clears. Presses are never missed even while the loop is blocked in `wifi.connect()` or `weather.current()`.
- **D-14:** Debounce is software, via `time.ticks_ms()` inside the IRQ handler: compare the current tick to a stored last-fire timestamp, ignore anything under a ~50 ms threshold. The exact threshold constant is planner/executor discretion — 30–80 ms is the acceptable band; final value tuned during on-device verification.
- **D-15:** Main loop is a `time.ticks_ms()`-based poll scheduler. Each iteration: (1) read + clear the direction flag, dispatch view-change if set; (2) check each view's `next_refresh_at` timestamp via `time.ticks_diff` and call its `render()` if due; (3) sleep ~50–100 ms and repeat. Single-threaded. No `machine.Timer`, no `asyncio` — the codebase stays fully synchronous.

### View module layout
- **D-16:** Three flat files at the repo root — `weather_view.py`, `clock_view.py`, `system_view.py`. No `views/` subdirectory (CLAUDE.md flat-namespace convention). No package `__init__.py`.
- **D-17:** Each view module exposes a single public `render(oled)` function. Modules own their private state as module-level variables (e.g. `weather_view` holds `_cached_temp`, `_cached_code`, `_cached_is_day`, `_last_refresh_ms`). No state is passed in by the caller. Weather view additionally exposes whatever helpers it needs to service `main.py`'s scheduler ticks — signature and count are planner discretion.
- **D-18:** `main.py` owns the carousel state: a `VIEWS = (weather_view, clock_view, system_view)` tuple and a `_current_idx` module-level int. The IRQ handler bumps `_current_idx` with wrap-around; the loop dispatches via `VIEWS[_current_idx].render(oled)` followed by a page-dot draw pass. Boot value is `_current_idx = 0` (Weather).

### Page-dot indicator
- **D-19:** Three dots render at `y = 60` (near the bottom edge, ~4 px above the physical bottom). Rows 54–63 are reserved for the dot strip; all view drawing MUST stay within rows 0–53. Existing Weather layout (icon at (16, 16), scale-2 temp centered at y=32) fits inside this budget without shifting; if the temp visually feels too high given the reserved strip, the temp anchor may drop to y=26 during implementation (planner discretion — visual verify on-device).
- **D-20:** Style = filled active + hollow inactive. Both render via `fb.ellipse(cx, cy, 2, 2, 1, is_active)` — the same idiom already established in `icons.py:22, 27, 32` and re-used for the Phase 1 degree ring. No new draw primitive needed.
- **D-21:** Dot geometry: `r = 2` for all three, center-to-center spacing = 12 px, dots centered horizontally on the 128 px width. This puts the three dot centers at `x = 52, 64, 76`. Draw order does not matter (no overlap).

### Refresh policy + boot visuals
- **D-22:** On view-switch: the target view's `render(oled)` redraws from its module-level cache in <1 poll tick (no network I/O). The 600 s Weather refresh cadence (WEATHER-03) is driven independently by the main-loop scheduler comparing `now - _last_refresh_ms` to the interval — completely decoupled from view-switch events. Interpretation of WEATHER-04 "refreshes immediately when navigated to" = "the view redraws immediately", not "re-fetches the API".
- **D-23:** Pre-first-fetch boot sequence has two visual states:
  1. **During `wifi.connect()`:** static text `connecting...` centered in the Weather view content area (rows 0–53). Loop is genuinely blocked here — no animation possible. This is the case on cold boot and after WiFi drops.
  2. **During the actual weather HTTP fetch (after WiFi is up):** a small animated spinner (e.g. a rotating single-pixel dot on a small ellipse ring) drawn near the temperature anchor. Requires the fetch to be either split into non-blocking chunks OR the spinner is animated by the scheduler between fetch attempts, not during the single blocking `urequests.get()` call. Planner picks the mechanism; the acceptance criterion is: the spinner is visibly animating for at least one frame during the fetch phase.
- **D-24:** Clock and System stubs render fully blank in Phase 2 — only the page dot strip is drawn (via the `main.py` post-render pass). No "Clock" / "System" title text, no "coming soon" copy. The stub `render(oled)` bodies do `oled.fill(0)` and nothing else; page dots draw on top. Rationale: no dead copy to delete when Phases 3/4 land, and the page dots plus button responsiveness are sufficient signal that the carousel is working.

### Error state (WEATHER-05)
- **D-25:** When `wifi.connect()` fails, the Weather view renders `no wifi` centered in rows 0–53 (existing pattern). When `weather.current()` returns `(None, None, None)`, it renders `no data`. Page dots continue to render on top; navigation continues to work — the error state is visual only, never blocks the carousel. Error text position and typography stay identical to today's `_center_text(oled, "no wifi", WIDTH // 2, HEIGHT // 2)` call site (planner may adjust y-center to account for the reserved bottom strip).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core Value, Constraints, Key Decisions (esp. "Carousel navigation, not menu", "Boot to Weather, no view persistence", "Show page dots as position indicator")
- `.planning/REQUIREMENTS.md` — NAV-01..06 and WEATHER-02..05 exact wording
- `.planning/ROADMAP.md` §"Phase 2: Carousel + Weather" — Success Criteria, requirement mapping
- `.planning/phases/01-secure-foundation/01-CONTEXT.md` — Phase 1 locked decisions (secrets contract, fb.ellipse degree-ring idiom, missing-secrets fallback) that carry forward into the render pipeline

### Hardware and driver constraints (must NOT be violated by any phase-2 code)
- `CLAUDE.md` §"Non-obvious SH1107 gotchas" — Four hardware traps. Any render code interacts with the framebuf; `sh1107.py` itself MUST NOT be modified in Phase 2.
- `CLAUDE.md` §"Hardware Pinout" — Fixed HAT pinout (DC/CS/SCK/MOSI/RST/SPI). Note: the KEY0 and KEY1 pinout (GP15, GP17) is documented in `.planning/PROJECT.md` §Context, not in CLAUDE.md's pinout table — planner should treat GP15/GP17 as the authoritative KEY0/KEY1 assignment (standard Waveshare Pico-OLED-1.3 HAT layout).
- `.planning/codebase/CONCERNS.md` — Duplicates the four SH1107 gotchas plus the "No error handling for WiFi/API failures" concern that Phase 2 partially addresses via WEATHER-05.
- `.planning/codebase/ARCHITECTURE.md` — Existing layer model + data flow; Phase 2 preserves the layer separation.
- `.planning/codebase/CONVENTIONS.md` — Naming (snake_case, `_`-prefixed privates), `.format()` not f-strings, no type hints, no docstrings — all binding for new view modules.

### Source files to read (Phase 2 will modify a subset — see Integration Points below)
- `main.py` — Currently the entire application layer. Phase 2 refactors this into carousel/scheduler orchestration; the existing `_render(oled)` body moves into `weather_view.render()`.
- `wifi.py` — `connect(ssid, password, timeout=20)`. Signature unchanged; view code calls it via `main.py`'s pre-render sequence.
- `weather.py` — `current()` returning `(temp, code, is_day)`. Signature unchanged; `weather_view` calls it directly.
- `icons.py` — `draw(fb, x, y, code, is_day)`. Unchanged; used by `weather_view.render()`.
- `text_render.py` — `text(fb, s, x, y, scale, color)`. Unchanged; used for `connecting...`, `no wifi`, `no data`, and the temperature digits.
- `sh1107.py` — Do NOT modify. Read only for the OLED interface Phase 2 draws against. Framebuf format is `MONO_HMSB`, coordinates are (x=0..127, y=0..63), origin top-left.
- `secrets.py` (gitignored) — Imported at boot for `WIFI_SSID` / `WIFI_PASSWORD`. Missing-secrets fallback (Phase 1 D-04) stays in `main.py` and fires before any view rendering.

### External
- Waveshare Pico_code SPI demo (link in `CLAUDE.md` §Reference) — Reference only if the panel misbehaves; not otherwise touched. Waveshare demo also shows the standard KEY0=GP15 / KEY1=GP17 assignment.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`fb.ellipse(cx, cy, rx, ry, color, fill)`** — `icons.py:22, 27, 32` and Phase 1's degree ring (`main.py:48`). Directly reusable for page dots (`fb.ellipse(x, 60, 2, 2, 1, active)`) and for a spinner (`fb.ellipse` with `fill=False` + a moving indicator pixel).
- **`_center_text(oled, s, x_center, y_center, scale=1)`** — `main.py:14-17`. Used today for `no wifi`, `no data`, and the temperature. Directly reusable for `connecting...`, stub-view name text (if the stub decision ever reverses), and all view error copy. Note: the current version assumes the full 64-row canvas; Phase 2 callers may pass `y_center` in the 0–53 range instead of `HEIGHT // 2 = 32`.
- **`icons.draw(fb, x, y, code, is_day)`** — `icons.py`. Preserves WEATHER-02 automatically since the current `main.py:_render` already calls it at `(16, 16)`. `weather_view.render()` inherits this call site unchanged.
- **`weather.current()`** — `weather.py`. Returns `(temp, code, is_day)` or `(None, None, None)`. `weather_view` module owns the call plus caches the last successful result and its timestamp.
- **`wifi.connect(ssid, password, timeout=20)`** — `wifi.py`. Called from `main.py` at boot and on reconnect attempts. Blocking, up to 20 s.
- **Missing-secrets fallback (Phase 1 D-04/05)** — `main.py:20-29`. Fires before any view code loads. No Phase 2 changes here.

### Established Patterns
- **Module-level UPPER_SNAKE_CASE constants at file top** (`main.py:9-10`, `sh1107.py:6-13`). New view modules follow this for any tunables (e.g. `_REFRESH_MS = 600_000` in `weather_view.py`).
- **Private/internal identifiers prefixed with `_`** (`_center_text`, `_render`, `_cmd`, `_kind`, all `icons.py` drawer functions). New helpers keep this convention.
- **`.format()` string formatting, no f-strings** (`main.py:43-44`, `weather.py:9-11`). Binding.
- **No type hints, no docstrings** — MicroPython idiom, binding for new modules.
- **Draw cycle: `oled.fill(0)` → framebuf draws → `oled.show()`** (`main.py:33-49`). Each `render(oled)` call fills, draws, and either returns before or invokes the page-dot pass — planner decides whether views call `oled.show()` themselves or the main loop calls it after the page-dot pass. Recommendation from context: main loop owns `show()` so page dots always render on top, but this is not a locked decision.
- **All-static allocation in the render path** — Phase 2 must not allocate per-frame in the poll loop; state buffers (cached weather values, spinner frame counter, IRQ direction flag) live at module level.

### Integration Points
- **`main.py` becomes the scheduler+carousel host.** Existing `_render(oled)` body moves into `weather_view.render()`. `main.py` retains: user config constants (`REFRESH_SECONDS`, `ROTATE`), the missing-secrets fallback, WiFi connect on boot (or lazy), IRQ handler installation, the `while True:` poll loop, and the page-dot draw pass.
- **`weather_view.py`** imports `wifi`, `weather`, `icons`, `text_render`, `secrets` (for `WIFI_SSID`, `WIFI_PASSWORD`). Owns the cached last-good weather tuple, the `_last_refresh_ms` timestamp, and the connecting/spinner state machine for the first fetch. Exposes `render(oled)` and whatever scheduler-facing helpers the planner determines are needed (e.g. a `should_refresh(now_ms)` predicate, or a `tick(oled, now_ms)` shape — planner's call).
- **`clock_view.py`** and **`system_view.py`** are minimal stubs: each defines `render(oled)` that does `oled.fill(0)` and nothing else. Placeholder for Phase 3 / Phase 4 real implementations.
- **Button pins** — GP15 (KEY0) and GP17 (KEY1) declared as `Pin.IN, Pin.PULL_UP` (Waveshare HAT ties the button to GND on press → falling edge). IRQ registered with `trigger=Pin.IRQ_FALLING`. Both handlers share the debounce timestamp variable or each has its own — planner discretion (recommend one shared timestamp since two buttons on the same HAT will not physically fire within the debounce window).
- **Page dots draw pass** — `main.py` calls a small helper (`_draw_page_dots(oled, current_idx)`) after each view's `render()` returns, then calls `oled.show()`. This centralizes the "dots always visible" invariant across the three views.

</code_context>

<specifics>
## Specific Ideas

- **Poll tick interval** — the descriptions used ~50–100 ms as the recommended band. 100 ms feels responsive from the user side (10 Hz UI refresh) and is cheap on the Pico. Concrete value = planner discretion; visually verify on-device that button-press-to-view-change perceived latency is <150 ms.
- **Spinner shape** — no specific shape locked. The user picked "spinner during weather fetch" but the exact geometry is planner discretion. Reference `fb.ellipse(cx, cy, r, r, 1, False)` for the ring and rotate a single-pixel indicator around it. Position: somewhere in the temperature region (right half of screen, y around 32) to signal "temperature is loading" rather than in the icon region.
- **Blank stub note** — Clock and System stubs are BLANK in Phase 2. Do not add debug text, view names, or "Phase 3/4 pending" copy. The page dots plus successful button-response are the entire user-visible signal that navigation works.
- **`connecting...` copy** — exact string `connecting...` (lowercase, three dots). Centered horizontally, y=26 (roughly center of the reserved rows 0–53 area).

</specifics>

<deferred>
## Deferred Ideas

- **Long-press semantics** (NAV-07 v2). Not in v1.
- **Persisting last view across reboots** (NAV-08 v2 + explicit Out of Scope). Not in v1.
- **Weather retry logic on transient failures** (concern in `codebase/CONCERNS.md` "No Error Handling for WiFi/API Failures" §Improvement Path). The current phase satisfies WEATHER-05 with the existing `no wifi` / `no data` fallbacks. Retry with distinguished error reasons is a future improvement, not required for Phase 2 completion.
- **Response caching with age indicator** ("2 hrs old" stale-data display) — future improvement, not in v1.
- **Battery monitoring / power-down mode** (concern in `codebase/CONCERNS.md`). Only relevant for battery deployment, out of scope for v1.
- **Splitting weather fetch into non-blocking chunks** for a smoother spinner — potential Phase 2 sub-decision if the planner determines the naive approach (single blocking `urequests.get()`) makes the spinner visibly janky. If chunking proves painful, downgrade the spinner to a two-frame animation between fetch attempts rather than during a single fetch call.

</deferred>

---

*Phase: 2-Carousel + Weather*
*Context gathered: 2026-07-17*
