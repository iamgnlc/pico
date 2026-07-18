---
quick_id: 260718-remove-spinner-tune-cadence
task: Remove spinner + tune NTP cadence to 6h (Phase 2 D-23 retired; Phase 3 D-35 updated)
date: 2026-07-18
type: fix
---

# Quick Task: Remove Spinner + Tune NTP Cadence

## Context

Operator requested (ASAP):
1. Remove all spinners from the UI (Phase 2 D-23 shipped a rotating-dot spinner in `weather_view` during background weather fetches when cache was already `"ok"`).
2. Ensure weather-view refresh cadence is 10 min. **Already correct** — `_REFRESH_MS = 600_000`.
3. Change clock NTP sync cadence to every 6h (was 1h per Phase 3 D-35).
4. Ensure fetch-failure retry stays at 1 min then reverts to per-view normal cadence after data returns. **Already correct** — `_RETRY_MS = 60_000` in both `weather_view.py` and `clock_view.py`; predicates already select interval from cache/sync state (Phase 2.1 D-31 pattern).

## Scope

Two code changes + doc updates for retired/adjusted decisions.

## Code Changes

### `weather_view.py`
- Remove `_spinner_frame = 0` module state (line 18).
- Remove the `_draw_spinner(oled)` function entirely (lines 27-38).
- Remove the pre-fetch spinner block from `refresh(oled)` (lines 82-92 — the `if _cache_status == "ok": render + _draw_spinner + oled.show()` guard-and-draw).

### `clock_view.py`
- Change `_SYNC_MS = 3_600_000` → `_SYNC_MS = 21_600_000`.
- Update the trailing comment to reflect the new cadence.

## Doc Changes

- `.planning/phases/02-carousel-+-weather/02-CONTEXT.md` — mark D-23 (spinner during weather fetch) as RETIRED with a note pointing at this quick task.
- `.planning/phases/03-clock-view/03-CONTEXT.md` — update D-35's stated cadence from "every 1 hour" to "every 6 hours"; adjust the rationale line.
- `.planning/STATE.md` — append a Quick Tasks Completed row; update decisions list for D-23 retirement + D-35 cadence change; refresh session continuity.
- `.planning/quick/260718-remove-spinner-tune-cadence/260718-remove-spinner-tune-cadence-SUMMARY.md` — this task's summary artifact.

Note: `REQUIREMENTS.md` is unchanged — none of the CLOCK-XX or WEATHER-XX wording specifies the exact interval; those live in phase CONTEXT.md decisions.

## Do NOT

- Touch `sh1107.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py`, `system_view.py`, `main.py`, `secrets.py`, `.gitignore`, `tz_offset.txt`.
- Change the retry cadence (`_RETRY_MS = 60_000` stays in both views).
- Change the weather refresh cadence (`_REFRESH_MS = 600_000` stays).
- Rewrite the `should_refresh` / `should_sync` predicate shapes — only the constant they read changes.

## Commit Strategy

One atomic commit for the code (`fix(cross-phase): remove spinner + change NTP cadence to 6h`), one for the docs + STATE + SUMMARY (`docs(quick-260718): retire D-23, update D-35, capture summary`).
