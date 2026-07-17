---
phase: 02-carousel-+-weather
plan: 03
wave: 3
completed: 2026-07-17
requirements: [WEATHER-03, WEATHER-04, WEATHER-05]
status: passed
---

# Plan 02-03 Summary — Weather scheduler + boot visuals + error state

## Outcome

Phase 2's final wave. The Weather view now auto-refreshes on a 600 s cadence, boots into a visible "connecting..." + page-dot screen within 1-2 s of power-on (no more black-screen-during-wifi-connect), animates a spinner frame during the HTTP fetch, and gracefully handles WiFi/API failures without blocking the carousel. On-device verification is batched at end of phase per `workflow.human_verify_mode: end-of-phase`.

## Files Modified

- `weather_view.py` (55 → 91 lines, Δ = +36)
  - Added `import time` to the imports block.
  - Added module-level state: `_REFRESH_MS = 600_000`, `_last_refresh_ms = 0`, `_spinner_frame = 0`.
  - Added `_draw_spinner(oled)` — 4-frame rotating single-pixel indicator on a 4-px ring at (88, 20).
  - Added `should_refresh(now_ms)` predicate: `time.ticks_diff(now_ms, _last_refresh_ms) >= _REFRESH_MS`.
  - Modified `refresh(oled)`: stamps `_last_refresh_ms = time.ticks_ms()` at the START (T-02-11 mitigation — prevents transient-failure tight-loop); after `wifi.connect()` succeeds and before the blocking `urequests.get()`, renders + draws spinner + `oled.show()` so the user sees at least one visible frame during the fetch phase (D-23 satisfaction).
- `main.py` (100 → 117 lines, Δ = +17)
  - Pre-fetch render: `weather_view.render(oled)` + `_draw_page_dots` + `oled.show()` inserted BEFORE the initial `weather_view.refresh(oled)` call so the "connecting..." + dots screen is on the panel within 1-2 s of power-on.
  - Scheduler branch in the poll loop: reads `time.ticks_ms()` once per tick and calls `weather_view.should_refresh(now)`. On True, fires `weather_view.refresh(oled)`, then overpaints with `VIEWS[_current_idx].render(oled)` (so users on Clock/System don't see a flash of Weather content), then dots + show.

## Files NOT Modified (Verified)

`sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py`, `clock_view.py`, `system_view.py` — `git diff --exit-code` returned zero for all seven. Phase 1's four SH1107 gotchas remain intact. Task 1's changes are scoped to `weather_view.py`; Task 2's changes are scoped to `main.py`.

## Acceptance Criteria — All Pass

Task 1 (weather_view.py scheduler + spinner):
- `_REFRESH_MS = 600_000` present ✓
- `_last_refresh_ms = 0` present ✓
- `_spinner_frame = 0` present ✓
- `import time` present ✓
- `def should_refresh(now_ms):` present ✓
- Predicate body: `time.ticks_diff(now_ms, _last_refresh_ms) >= _REFRESH_MS` ✓
- `def _draw_spinner(oled):` present ✓
- `_last_refresh_ms = time.ticks_ms()` present (stamped at start of refresh) ✓
- `grep -c "oled.show()"` in weather_view.py = 1 (only the spinner flush) ✓
- `_draw_spinner(oled)` invoked in refresh ✓
- No retry keywords ✓
- No asyncio/Timer ✓
- Python 3 syntax parses ✓
- sh1107 + 6 other unrelated files: zero diff ✓

Task 2 (main.py scheduler wiring):
- `weather_view.should_refresh` call present ✓
- `weather_view.refresh(oled)` call count = 2 (boot + scheduler branch) ✓
- `weather_view.render(oled)` (pre-fetch connecting render) present ✓
- Order-preservation check via awk: render appears at line 15, refresh at line 22 — render BEFORE refresh ✓
- VIEWS tuple + IRQ install + `_draw_page_dots` all preserved from Plan 02-02 ✓
- No `time.sleep(REFRESH_SECONDS)` ✓
- No asyncio/Timer ✓
- Python 3 syntax parses ✓
- sh1107 + 6 other unrelated files: zero diff ✓

## Requirement Coverage

- **WEATHER-03** — `_REFRESH_MS = 600_000` drives the cadence via `should_refresh(now_ms)` called on every ~100 ms poll tick. First fetch happens at boot; subsequent fetches every ~600 s regardless of which view is currently displayed.
- **WEATHER-04** — Handled entirely by Plan 02-02's cache-based `render(oled)`. On view-switch, main.py dispatches to `VIEWS[_current_idx].render(oled)` which for Weather reads from the module-level cache (no network I/O, no delay). This plan verifies the semantic; no new code needed.
- **WEATHER-05** — Handled entirely by Plan 02-02's `_cache_status` model (`"no_wifi"` / `"no_data"` states rendered inline via `_center_text` at y=26). Page dots draw on top via main.py's `_draw_page_dots` call after every render. Carousel navigation continues to work during error states. This plan verifies the semantic on-device; no new code needed.

## Deferred (per plan)

- On-device verification is batched at end of phase per config. Human-verify checklist (all deferred):
  1. Cold-boot shows "connecting..." + dots within 1-2 s (no black screen).
  2. Spinner visible for at least one frame during the HTTP fetch phase.
  3. After boot, real weather displays; navigating to Clock/System and back is instant (from cache).
  4. Wrong-creds boot renders "no wifi" + dots; KEY0/KEY1 still switch views.
  5. Optional shortcut for the 600 s cadence: temporarily set `_REFRESH_MS = 30_000` for the on-device check, then revert.

## Implementation Choices (Planner Discretion Applied)

- **Spinner geometry:** Kept the plan's reference `oled.ellipse(88, 20, 4, 4, 1, False)` + `oled.pixel(88 + dx, 20 + dy, 1)` unchanged. The plan noted potential text-overlap with the "connecting..." glyph at y=22-30; kept the reference coordinates because they're pinned in the plan's specifics. If on-device verification shows a visually poor overlap, the fallback coordinate (108, 20) is documented in the plan and can be swapped in without any structural change.
- **Constants alignment:** Initially column-aligned the three new constants (`_REFRESH_MS`, `_last_refresh_ms`, `_spinner_frame`) but reverted to single-space `=` to satisfy the plan's literal `grep -q "^_spinner_frame = 0"` acceptance check. Minor style delta from `main.py`'s aligned constant block; noted for future consistency.
- **Cadence stamping at start of refresh:** Followed the plan verbatim — `_last_refresh_ms = time.ticks_ms()` on the first line of `refresh()`. Prevents T-02-11 (tight-loop on repeated fetch failure) as designed.
- **Scheduler pass placement:** Placed the `if weather_view.should_refresh(now):` block AFTER the `_pending_dir` handling so a queued button press dispatches before the scheduler runs — smaller worst-case press-to-visible-change latency during a refresh window.

## Phase 2 Human-Verify Checklist (for end-of-phase batch)

All ten requirements now have code paths that satisfy them. Deferred on-device verification checklist:

- NAV-01: KEY0 (GP15) → previous view; KEY1 (GP17) → next view.
- NAV-02: Rapid double-tap of KEY0 or KEY1 advances exactly one view (50 ms debounce).
- NAV-03: KEY0 on Weather wraps to System; KEY1 on System wraps to Weather.
- NAV-04: Every cold boot lands on Weather (left dot filled).
- NAV-05: Three page dots at y=60 visible on every view; active dot filled, other two hollow.
- NAV-06: View-switch redraws within ~100-150 ms (poll tick + one framebuf pass).
- WEATHER-02: Condition icon renders at (16, 16) on Weather; verify with several weather codes (may want to test at different times of day if `is_day` matters visually).
- WEATHER-03: Weather cache updates every ~600 s. Optional: temporarily set `_REFRESH_MS = 30_000` for a faster verification loop.
- WEATHER-04: Navigate away from Weather, wait, navigate back — the display updates instantly with the last-known data (no spinner, no delay).
- WEATHER-05: Boot with wrong wifi credentials → "no wifi" + dots + navigable carousel. Restore credentials, reboot → recovery to Weather.

## Deferred Ideas Surfaced During Implementation

- **Spinner true-animation upgrade:** Currently one frame per refresh (per D-23 planner-discretion clause). If an async HTTP client is introduced in a future phase, the spinner could animate continuously during the fetch instead of showing one static frame. Not required for Phase 2 completion.
- **Cadence tunability from device UI:** No mechanism for the operator to change `_REFRESH_MS` at runtime — it's hard-coded. Would require a "settings" view or a config file. Deferred to v2.
- **Response caching with age indicator ("2 hrs old"):** Already noted in 02-CONTEXT.md deferred ideas. Not implemented; not required.
- **Distinguished error reasons (timeout vs no-connection vs api-error):** `codebase/CONCERNS.md § "No Error Handling for WiFi/API Failures"` describes this improvement path. Deferred; WEATHER-05 satisfied by the coarse "no wifi"/"no data" copy in place.

## Commits

- `289f5b2 feat(02-03): scheduler predicate + spinner in weather_view` — Task 1
- `c8271d9 feat(02-03): pre-fetch connecting render + 600s scheduler pass` — Task 2

Note: `b0c8477 fix(02-02): lazy-import secrets in weather_view.refresh` landed between Plan 02-02 and Plan 02-03 as a scope fix (not a new plan). It restored Phase 1's missing-secrets fallback reachability which Plan 02-02 had accidentally shadowed. Included here for phase-summary completeness.

## Next

- **End-of-phase verification.** Flash all seven `.py` files to the Pico, cycle through the human-verify checklist above, and record results in `02-VERIFICATION.md` (produced by `/gsd:verify-work` or the `gsd-verifier` agent).
- **Reminder before flashing:** update `display/secrets.py` with the rotated WiFi password (HANDOFF flagged this at the start of the session). Without it, `wifi.connect()` will hit the 20 s timeout and the "no wifi" state will be the resting state — that's the WEATHER-05 verification path but not the happy-path check.
