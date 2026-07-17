---
phase: 02-carousel-+-weather
plan: 01
wave: 1
completed: 2026-07-17
requirements: [WEATHER-02]
status: passed
---

# Plan 02-01 Summary — Extract Weather render into weather_view.py

## Outcome

Behavior-preserving refactor. The Weather rendering (icon + degree-ring temperature + no-wifi/no-data fallback) now lives in a new flat-namespace module `weather_view.py` at the repo root, exposing a single public `render(oled)` function. `main.py` imports and delegates to it. On-device behavior is identical to pre-Plan-01 (deferred to end-of-phase batch per `workflow.human_verify_mode=end-of-phase`).

## Files Created

- `weather_view.py` (32 lines) — imports `WIDTH, HEIGHT` from `sh1107`, plus `wifi`, `weather`, `icons`, `text_render`, and `secrets` (last, per import discipline). Defines `_center_text(oled, s, x_center, y_center, scale=1)` and `render(oled)`. Byte-for-byte extraction of the original `main.py:_render()` body — same coordinates (icon at (16, 16), temp centered at (88, HEIGHT//2), ring at `cx = 88 + w//2 + 5, cy = HEIGHT//2 - 6`), same format string (`"{:.0f}".format(temp)`), same error fallbacks.

## Files Modified

- `main.py` (57 → 37 lines, Δ = −20)
  - Added `import weather_view` after other local module imports
  - Removed the `_render(oled)` function body (lines 32-49 of the pre-plan file)
  - Replaced `_render(oled)` call in the `__main__` block with `weather_view.render(oled)`
  - Kept: `REFRESH_SECONDS`/`ROTATE` config, `_center_text` helper, `try/except ImportError` missing-secrets fallback + halt loop, `while True: … time.sleep(REFRESH_SECONDS)` shape

## Files NOT Modified (Verified)

`sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py` — `git diff --exit-code` returned zero for all five. Phase 1's four SH1107 gotchas remain intact.

## Acceptance Criteria — All Pass

Task 1 (weather_view.py creation):
- File exists at repo root ✓
- `def render(oled)` present (count: 1) ✓
- `def _center_text(` present (count: 1) ✓
- `icons.draw(oled, 16, 16, code, is_day)` preserved ✓ (WEATHER-02)
- `oled.ellipse(cx, cy, 2, 2, 1, False)` degree ring preserved ✓ (D-06 Phase 1)
- `oled.show()` final flush preserved ✓
- `import secrets` present ✓
- Zero f-strings ✓
- Zero type hints on function params ✓
- `python3 -c "import ast; ast.parse(...)"` exits 0 ✓
- `sh1107.py` diff: empty ✓

Task 2 (main.py rewire):
- `import weather_view` present (count: 1) ✓
- `weather_view.render(oled)` call present ✓
- Old `_render(` function removed (count: 0) ✓
- No leftover `_render(oled)` calls ✓
- `_center_text` helper preserved ✓
- `try:`/`import secrets`/`except ImportError:` all preserved ✓
- `REFRESH_SECONDS` and `ROTATE` preserved ✓
- `time.sleep(REFRESH_SECONDS)` preserved (Plan 02-02 replaces this) ✓
- Python 3 syntax parses ✓
- `sh1107.py wifi.py weather.py icons.py text_render.py` diff: empty ✓

## Requirement Coverage

- **WEATHER-02** (condition icon rendering) — the `icons.draw(oled, 16, 16, code, is_day)` call moved into `weather_view.render()` at the identical (16, 16) coordinate. Verification is behavioral: end-of-phase on-device check will confirm the icon still renders correctly for each weather code.

## Implementation Choices (Planner Discretion Applied)

None material. The plan specified exact import order, exact function signatures, and exact coordinate values; all were followed verbatim. Only micro-choice: preserved a single blank line between `_center_text` and `render` in `weather_view.py` matching the existing `main.py` cadence.

## Deferred (per plan)

- On-device verification. Batched at end-of-phase per `workflow.human_verify_mode=end-of-phase`. Human check: flash all files to Pico, boot, confirm the OLED shows the same weather screen as before Plan 01.

## Commits

- `b669210 feat(02-01): extract Weather render into weather_view.py` — Task 1
- `caea2fe feat(02-01): main.py delegates render to weather_view` — Task 2

## Next

Plan 02-02 (Wave 2, depends on this): add Clock and System stub view modules, install KEY0/KEY1 IRQ handlers, add software debounce, replace `time.sleep(REFRESH_SECONDS)` with a `ticks_ms()` poll scheduler, draw the page-dot indicator.
