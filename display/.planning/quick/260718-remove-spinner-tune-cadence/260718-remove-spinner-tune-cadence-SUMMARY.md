---
quick_id: 260718-remove-spinner-tune-cadence
task: Remove spinner + tune NTP cadence to 6h (Phase 2 D-23 retired; Phase 3 D-35 updated)
date: 2026-07-18
status: complete
type: fix
---

# Quick Task Summary: Remove Spinner + Tune NTP Cadence

## Outcome

Operator requested (ASAP) four items during the between-phases resume. Two required code changes; two were already correct per the current codebase and required no edits.

**Applied:**
1. Removed all spinner code from `weather_view.py` (Phase 2 D-23 retired).
2. Changed `clock_view._SYNC_MS` from 1h to 6h (Phase 3 D-35 updated).

**Confirmed as already correct (no edits needed):**
3. Weather-view refresh cadence at 10 min — `_REFRESH_MS = 600_000` (unchanged since Phase 2).
4. Fetch-failure retry cadence at 1 min — `_RETRY_MS = 60_000` in both `weather_view.py` (WEATHER-09, Phase 2.1) and `clock_view.py` (Phase 3 D-36). Predicate shapes already select interval from cache/sync state and revert to normal per-view cadence after data returns.

## Files Modified

| File | Change |
|------|--------|
| `weather_view.py` | Removed `_spinner_frame = 0` state, `_draw_spinner(oled)` function, and the pre-fetch `if _cache_status == "ok": render + _draw_spinner + oled.show()` block in `refresh(oled)`. 28 lines deleted; 1 line adjusted. |
| `clock_view.py` | `_SYNC_MS`: `3_600_000` → `21_600_000`. Comment updated to reflect new cadence + D-35 revision date. |
| `.planning/phases/02-carousel-+-weather/02-CONTEXT.md` | D-23 marked RETIRED with a pointer to this quick task. Historical wording preserved as strikethrough for audit trail. |
| `.planning/phases/03-clock-view/03-CONTEXT.md` | D-35 wording updated ("every 1 hour" → "every 6 hours"; rationale line updated). |
| `.planning/STATE.md` | Frontmatter, decisions list, Quick Tasks Completed table, Session Continuity all updated. |

## Files NOT Modified

- `sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py`, `system_view.py`, `main.py`, `secrets.py`, `.gitignore`, `tz_offset.txt` — anti-diff verified.
- `REQUIREMENTS.md` — none of the CLOCK-XX / WEATHER-XX wording specified exact intervals; those live in phase CONTEXT.md decisions.
- `PROJECT.md` — no rows referenced spinner or specific NTP cadence.

## Automated Verification (12/12 pass)

| # | Check | Result |
|---|-------|--------|
| 1 | `weather_view.py` syntax parses | ok |
| 2 | `clock_view.py` syntax parses | ok |
| 3 | `_spinner_frame` references gone | ok (0 occurrences) |
| 4 | `_draw_spinner` references gone | ok (0 occurrences) |
| 5 | Any mention of `spinner` gone from `weather_view.py` | ok (0 occurrences) |
| 6 | `_SYNC_MS = 21_600_000` present | ok |
| 7 | `_REFRESH_MS = 600_000` unchanged (10 min) | ok |
| 8 | `_RETRY_MS = 60_000` unchanged in `weather_view.py` (1 min) | ok |
| 9 | `_RETRY_MS = 60_000` unchanged in `clock_view.py` (1 min) | ok |
| 10 | `weather_view.should_refresh` predicate shape unchanged | ok |
| 11 | `clock_view.should_sync` predicate shape unchanged | ok |
| 12 | Zero diff on `sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py`, `system_view.py`, `main.py` | ok |

## Commits

| Commit | Description |
|--------|-------------|
| `93064bd` | fix(cross-phase): remove spinner + change NTP cadence to 6h |
| *(this commit)* | docs(quick-260718-remove-spinner-tune-cadence): retire D-23, update D-35, capture summary |

## Retired / Updated Decisions

- **Phase 2 D-23** — RETIRED. The static `connecting...` text during `wifi.connect()` remains (still correct per operator's message: they said "remove all spinners", not "remove connecting text"). The spinner during weather HTTP fetch is gone. Weather background refreshes now run silently; the panel continues showing the last-known cache state throughout the fetch window.
- **Phase 3 D-35** — UPDATED. NTP re-sync cadence 1h → 6h. RP2040 drift over 6h is a few seconds at worst — well below the display's 1-minute resolution. Fewer WiFi wakeups; friendlier for a Pico W that lives on a home network long-term.

## Human-Verify Recommendation (non-blocking)

Next time you copy `weather_view.py` and `clock_view.py` to the Pico:
1. Confirm no rotating-dot spinner appears on the Weather view during a background refresh (either wait 10 min for the natural cadence, or force one via `mpremote reset`).
2. Confirm the clock keeps ticking at minute boundaries. NTP re-sync now fires only every 6h — you won't see it during a normal usage session unless you time a long wait.
3. Confirm the retry cadence still hits after a WiFi drop (~60 s between retry attempts, unchanged).

No standing preconditions changed — `secrets.py` and `tz_offset.txt` still in scope from prior phases.

## Next

The between-phases pause is still in effect from before this quick task. Phase 4 (System View) is the next work item.

Command: `/gsd:discuss-phase 4`
