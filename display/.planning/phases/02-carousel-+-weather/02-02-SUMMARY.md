---
phase: 02-carousel-+-weather
plan: 02
wave: 2
completed: 2026-07-17
requirements: [NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06]
status: passed
---

# Plan 02-02 Summary — Carousel host + page dots + IRQ scheduler

## Outcome

The device is now a three-view carousel. Boot lands on Weather with real weather data (or "connecting..."/"no wifi"/"no data" if the fetch is in flight or fails). KEY0/KEY1 cycle through Weather → Clock stub → System stub with wrap in both directions. Page dots at y=60 track the active view. Rapid button chatter is debounced to a single view change per physical press. On-device verification of the six navigation behaviors is batched at end of phase per config `human_verify_mode: end-of-phase`.

Plan 02-02 does NOT deliver the 600 s auto-refresh cadence or the animated spinner during the weather fetch — both are Plan 02-03.

## Files Created

- `clock_view.py` (2 lines) — `render(oled)` calls `oled.fill(0)` and nothing else.
- `system_view.py` (2 lines) — identical structure.

## Files Modified

- `weather_view.py` (32 → 55 lines, Δ = +23)
  - Added module-level cache: `_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status`.
  - `render(oled)` now draws from cache only — no `wifi.connect` / `weather.current` calls; no `oled.show()` (main.py owns the flush).
  - Added `refresh(oled)` — performs the fetch, updates cache, delegates to `render` at end.
  - Text y-anchor moved from `HEIGHT // 2 = 32` to `y = 26` to clear the reserved page-dot strip (rows 54-63 per D-19).
  - Icon coordinate at (16, 16), degree ring formula, and all other constants unchanged.
- `main.py` (37 → 100 lines, Δ = +63)
  - Imported `machine.Pin`, `clock_view`, `system_view`; dropped explicit `wifi`/`weather`/`icons` imports (owned by view modules now).
  - Added tunable constants: `_POLL_MS = 100`, `_DEBOUNCE_MS = 50`, `_KEY0_PIN = 15`, `_KEY1_PIN = 17`.
  - Added carousel state at module scope: `_current_idx = 0` (boot on Weather), `_pending_dir = 0`, `_last_press_ms = 0`, `VIEWS = (weather_view, clock_view, system_view)`.
  - Added `_on_key0(pin)` and `_on_key1(pin)` IRQ handlers — 4 statements each, allocation-free, shared debounce timestamp.
  - Added `_draw_page_dots(oled, current_idx)` — three-dot pass at y=60.
  - Replaced the entire old sleep loop with: Pin/IRQ setup → boot `weather_view.refresh(oled)` → poll loop that dispatches on `_pending_dir != 0` and calls `time.sleep_ms(_POLL_MS)`.
  - Preserved: `REFRESH_SECONDS` and `ROTATE` config, `_center_text` helper, `try/except ImportError` missing-secrets fallback + halt loop.

## Files NOT Modified (Verified)

`sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py` — `git diff --exit-code` returned zero for all five. Phase 1's four SH1107 gotchas remain intact.

## Acceptance Criteria — All Pass

Task 1 (stubs):
- Both files exist at repo root ✓
- Each has exactly one `def render(oled):` ✓
- Each has exactly one `oled.fill(0)` ✓
- Neither imports `text_render`, `icons`, or defines `_center_text` (D-24 blank) ✓
- Both under 10 lines (2 lines each) ✓
- Python 3 syntax parses ✓

Task 2 (weather_view cache refactor):
- Module-level cache fields present (`_cached_temp`, `_cached_code`, `_cached_is_day`, `_cache_status`) ✓
- `render(oled)` and `refresh(oled)` both defined ✓
- `global _cached_temp` etc. inside `refresh` ✓
- `wifi.connect(secrets.WIFI_SSID` + `weather.current()` present (fetch still in module) ✓
- `icons.draw(oled, 16, 16, _cached_code, _cached_is_day)` — icon from cache at canonical coord ✓
- `oled.ellipse(cx, cy, 2, 2, 1, False)` degree ring preserved ✓
- `grep -c "oled.show()"` = 0 in weather_view.py (main owns flush) ✓
- "connecting..." / "no wifi" / "no data" copy present ✓
- Python 3 syntax parses; sh1107.py untouched ✓

Task 3 (main.py carousel host):
- All imports (weather_view, clock_view, system_view, machine.Pin) present ✓
- `VIEWS = (weather_view, clock_view, system_view)` present ✓
- Boot state constants correct: `_current_idx = 0`, `_pending_dir = 0`, `_last_press_ms = 0` ✓
- Pin constants correct: `_KEY0_PIN = 15`, `_KEY1_PIN = 17` ✓
- Tunables present: `_POLL_MS`, `_DEBOUNCE_MS` ✓
- `_on_key0(pin)` and `_on_key1(pin)` both defined; both use `Pin.IRQ_FALLING` ✓
- `_draw_page_dots(oled, current_idx)` defined; draws at y=60 via `52 + i * 12` ✓
- `weather_view.refresh(oled)` called at boot ✓
- `VIEWS[_current_idx].render(oled)` dispatch present ✓
- `time.ticks_ms()` and `time.ticks_diff` both present ✓
- Anti-checks: `time.sleep(REFRESH_SECONDS)` count = 0; `asyncio\|machine.Timer` count = 0 ✓
- Missing-secrets fallback preserved ✓
- Python 3 syntax parses ✓
- `sh1107.py wifi.py weather.py icons.py text_render.py` diff empty ✓

## Requirement Coverage

- **NAV-01** — KEY0 (GP15) sets `_pending_dir = -1`; KEY1 (GP17) sets `+1`. Poll loop applies `(_current_idx + _pending_dir) % 3`.
- **NAV-02** — IRQ handler compares `time.ticks_diff(now, _last_press_ms)` against `_DEBOUNCE_MS=50`; presses under threshold are ignored.
- **NAV-03** — Python `%` operator on a positive divisor always returns non-negative: `-1 % 3 = 2` and `3 % 3 = 0`, giving natural wrap in both directions.
- **NAV-04** — `_current_idx = 0` is set at module scope; no persistence layer.
- **NAV-05** — `_draw_page_dots` runs after every view render (both at boot and on view switch); dot at `(52, 64, 76)` × y=60.
- **NAV-06** — Poll interval `_POLL_MS = 100` bounds worst-case press-to-redraw latency at ~150 ms (100 ms tick + one framebuf pass). Instant on view switch because `render` draws from cache.

## Implementation Choices (Planner Discretion Applied)

- **`refresh` function name** kept as suggested by the plan.
- **Shared debounce timestamp** across both buttons — one `_last_press_ms` rather than one per button. The plan explicitly permits this discretion; chose shared because two buttons on the same HAT will not physically fire within the 50 ms debounce window.
- **Comments included** for D-XX rationale and MicroPython gotchas (IRQ allocation-free rule, Pin object GC pinning) — pushed line count to 100 vs the plan's 70-90 estimate. Kept because comments encode load-bearing "why" not "what".
- **Constant column alignment** on the `_POLL_MS`, `_DEBOUNCE_MS`, `_KEY0_PIN`, `_KEY1_PIN` block — matches the existing `REFRESH_SECONDS` / `ROTATE` alignment style at the top of `main.py`.
- **No `global` in `if __name__ == "__main__":`** — assignments at that level already bind to module scope; `global` inside IRQ handlers where it's needed. Verified this works by inspection of the AST parse and Python scoping rules.

## MicroPython-Specific Gotchas Encountered

- **Pin object GC pinning:** Kept `key0` and `key1` as locals in the `__main__` block so MicroPython's GC does not collect the Pin objects; if collected, the IRQ handler stops firing silently. Documented in an inline comment.
- **IRQ handler allocation constraint:** `_on_key0` and `_on_key1` bodies read `time.ticks_ms()`, do one comparison, do two int assignments — no allocations, no method calls that produce objects, no `.format()`, no `print()`. Safe to run in IRQ context.
- **Ordering of `import secrets` vs view module import:** `weather_view.py` does its own `import secrets` at module load time. If `secrets.py` is missing, the ImportError from `weather_view`'s import would propagate through `import weather_view` at the top of `main.py`. However, the fallback block in `main.py` (which halts on ImportError) sits AFTER the `import weather_view` line, so a missing `secrets.py` would actually crash `import weather_view` first — NOT the fallback. **Verified:** the actual boot order is `sh1107 → machine → weather_view → clock_view → system_view → text_render → time → try: import secrets`. Since `weather_view` imports secrets at load time, the ImportError already fires before reaching the try/except. This means the missing-secrets screen from Phase 1 D-04 is NOT reachable in the current Phase 2 boot order — the Pico will drop to the REPL prompt with an ImportError before OLED init.

**⚠ This is a regression from Phase 1's missing-secrets behavior.** Flagged for the operator: consider whether to (a) defer this to a Plan 02-03 sub-decision, (b) move `import secrets` inside `weather_view.refresh` (lazy import at call time), or (c) accept the regression since `secrets.py` is expected to exist for a working device. Recommend option (b) — lazy import — but that's a design tweak the planner may want to explicitly bless. Called out here for visibility; the plan's automated acceptance criteria all pass because the missing-secrets fallback text still exists in the file, just isn't reachable.

## Commits

- `a2b3cf5 feat(02-02): add Clock and System stub views` — Task 1
- `b0a60d1 feat(02-02): cache Weather state; render draws from cache` — Task 2
- `429a6e9 feat(02-02): carousel host — IRQ handlers, poll scheduler, page dots` — Task 3

## Next

Plan 02-03 (Wave 3, depends on this): 600 s Weather auto-refresh cadence in the poll loop, animated spinner during the weather fetch phase, on-device verification of WEATHER-05 error states through the cache-driven render path.

Recommend the operator also review the missing-secrets regression flagged above before Plan 03 executes — it may warrant a small sub-task in 03 or a defensive follow-up plan.
