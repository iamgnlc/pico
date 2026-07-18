# Phase 3: Clock View - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning
**Type:** Planned milestone phase.

<domain>
## Phase Boundary

Replace the current `clock_view.py` stub with a working clock view:

- Displays local time in 24-hour `HH:MM` format, updated at minute boundaries while the Clock view is the current view in the carousel.
- Syncs from NTP over WiFi at boot and every hour thereafter; retries every 60 s after a failure until the first success.
- Shows `--:--` when NTP has never succeeded on this boot. Continues showing the last-known time after a WiFi drop (post-first-sync) — `--:--` is not a "stale" state.

**Covers:** CLOCK-01, CLOCK-02, CLOCK-03, CLOCK-04, CLOCK-05 (5 requirements)

**Not in this phase:**

- No changes to the SH1107 driver, `wifi.py`, `weather.py`, `weather_view.py`, `icons.py`, `text_render.py`, `system_view.py`, or `secrets.py`.
- No changes to the poll scheduler in `main.py` beyond the two additional predicate calls for the Clock view and one `TZ_OFFSET` config constant.
- No date display, day-of-week display, timezone label, DST logic, or sync-status visual indicator (all deferred to v2 backlog).

</domain>

<decisions>
## Implementation Decisions

### Time format (D-34)
- **D-34:** The Clock view displays local time as `HH:MM` in 24-hour format with no seconds (e.g. `19:47`). The panel repaints only at minute boundaries when Clock is the current view — one panel write per minute (vs 60/min for seconds). Rationale: matches the project's "small, glanceable, minimum-state" ethos (page dots over labels, degree ring over font swap, single-tuple weather cache) and yields a much simpler tick predicate.

### NTP re-sync cadence (D-35)
- **D-35** *(updated 2026-07-18 — see `.planning/quick/260718-remove-spinner-tune-cadence/`)*: After the first successful NTP sync, the device re-syncs from NTP every 6 hours (`_SYNC_MS = 21_600_000`). Originally set to 1 hour during discuss-phase; relaxed to 6 hours at operator request to reduce WiFi churn. RP2040 drift over 6 hours remains well below the 1-minute display resolution.

### NTP failure retry (D-36)
- **D-36:** On any NTP sync failure (WiFi down, DNS fail, NTP server unresponsive), the device retries every 60 s until the first success, then reverts to the D-35 1-hour cadence. Symmetric with Phase 2.1's `weather_view.should_refresh` predicate (D-31): `clock_view.should_sync(now_ms)` reads `_synced` inline — 1 h if `_synced`, 60 s otherwise. `_RETRY_MS = 60_000` module constant.

### WiFi-drop behavior after first successful sync (D-37)
- **D-37:** If WiFi drops AFTER the first successful NTP sync, the Clock view keeps rendering the last-known time (RP2040 continues counting locally). The device attempts to re-sync at the D-35 1-hour cadence; failed re-syncs do NOT revert the display to `--:--`. Rationale: `--:--` means only "never synced on this boot" — the local clock's short-term accuracy after a WiFi blip is more useful than showing an error state. A "stale" state (e.g. hours since last sync) is deferred to v2.

### Tick integration into the poll scheduler (D-38)
- **D-38:** `clock_view.py` exposes two pure predicates and one sync function:
  - `should_tick(now_ms)` — returns True when the displayed `HH:MM` would change (minute boundary elapsed since last render). Reads only `now_ms` and module state; does NOT know about `_current_idx`.
  - `should_sync(now_ms)` — returns True when NTP should be re-attempted (1 h if `_synced`, 60 s otherwise, per D-35/D-36). Same purity.
  - `sync(oled)` — invokes `ntptime.settime()`; on success sets `_synced = True` and updates `_last_sync_ms`; on any exception, leaves `_synced` unchanged and updates `_last_sync_ms` to the attempt-start timestamp (D-33 pattern — stamp at start so failure doesn't tight-loop).
- `main.py`'s poll loop gates the redraw itself: `if _current_idx == 1 and clock_view.should_tick(now): clock_view.render(oled); _draw_page_dots(...); oled.show()`. This matches how `weather_view.refresh` + main.py's post-refresh overpaint already work — `main.py` is the coordinator, `clock_view.py` is the pure worker.
- The `sync` predicate does NOT depend on `_current_idx` — NTP re-syncs happen in the background regardless of which view is active. On successful sync while Clock is not the current view, no repaint is issued; the next tick after view-switch or minute boundary picks up the freshly-synced time.

### Visual composition (D-39)
- **D-39:** Clock view renders `HH:MM` at scale 3 centered horizontally on x=64 and vertically on y=27 (safely inside rows 0–53 which are reserved for view content per Phase 2 D-19). When `_synced == False`, renders `--:--` at the same scale and position. No TZ label, no date, no day-of-week, no sync-status indicator. Concrete call: `_center_text(oled, "19:47", 64, 27, scale=3)` — 120 px wide × 24 px tall, with 4 px margin on each side.

### Sync-status state machine (D-40)
- **D-40:** Single module-level boolean `_synced` (`False` on module load, `True` after first successful `ntptime.settime()`, never reverts). `should_sync` selects the interval by reading `_synced` inline (mirrors D-31's `_cache_status` inline check). No enum, no `"in_flight"` state (would be dead — not surfaced visually per D-39). `render(oled)` branches on `_synced` alone.

### TZ configuration (from CLOCK-02, ratified)
- Single hardcoded `TZ_OFFSET` constant at the top of `main.py` alongside the existing user-config block (`REFRESH_SECONDS`, `ROTATE`). Value is the offset in seconds from UTC (positive east, negative west). No `TZ_LABEL`, no DST logic — dropped explicitly in D-39.
- `clock_view.render(oled)` imports `TZ_OFFSET` from `main` via a top-of-file import, then computes local seconds via `time.time() + TZ_OFFSET` before formatting.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core Value, Constraints, Key Decisions.
- `.planning/REQUIREMENTS.md` — CLOCK-01..CLOCK-05 exact wording + Traceability table.
- `.planning/ROADMAP.md` §"Phase 3: Clock View" — Goal + 3 Success Criteria.
- `.planning/phases/02-carousel-+-weather/02-CONTEXT.md` — Phase 2 locked decisions D-13..D-25 (carousel, IRQ, page dots, cache model, stateless render). Substrate this phase extends; MUST NOT be violated.
- `.planning/phases/02.1-location-label-+-fetch-retry/02.1-CONTEXT.md` — Phase 2.1 D-31/D-32/D-33 (retry predicate pattern, cold-boot symmetry, stamp-at-start). D-36 mirrors D-31 directly.

### Hardware and driver constraints (must NOT be violated)
- `CLAUDE.md` §"Non-obvious SH1107 gotchas" — Four hardware traps. `sh1107.py` MUST NOT be modified.
- `.planning/codebase/CONVENTIONS.md` — Naming (snake_case, `_`-prefix privates), `.format()` not f-strings, no type hints, no docstrings — binding.
- `.planning/codebase/CONCERNS.md` — "No error handling for WiFi/API failures" concern; D-36's retry pattern partially addresses it for the NTP case (same posture as WEATHER-09).

### MicroPython stdlib references
- `ntptime` module — `ntptime.settime()` syncs the RP2040 RTC to UTC via SNTP. Blocking; typically returns within ~1–2 s over healthy WiFi. Raises `OSError` on any failure (DNS, timeout, packet malformed). Documentation: MicroPython "network — Network functionality" doc set.
- `time` module — `time.time()` returns Unix epoch seconds (int); `time.localtime(secs)` unpacks a struct-time tuple; `time.ticks_ms()` and `time.ticks_diff()` remain the correct timing primitives for scheduler predicates (Phase 2 D-15).

### Source files this phase will modify
- `clock_view.py` — Replace the current 2-line stub. New module state (`_synced`, `_last_render_min`, `_last_sync_ms`); new constants (`_SYNC_MS = 3_600_000`, `_RETRY_MS = 60_000`); new functions (`should_tick`, `should_sync`, `sync`, `render`). Imports `time`, `ntptime`, and `TZ_OFFSET` from `main`.
- `main.py` — Add `TZ_OFFSET` to the user-config block near `REFRESH_SECONDS` and `ROTATE`. Add two poll-loop calls: `if _current_idx == 1 and clock_view.should_tick(now): ...` and `if clock_view.should_sync(now): clock_view.sync(oled)`. No changes to IRQ handlers, VIEWS tuple, `_draw_page_dots`, or the weather-view branches.

### Source files this phase will NOT modify
- `sh1107.py`, `wifi.py`, `weather.py`, `weather_view.py`, `icons.py`, `text_render.py`, `system_view.py`, `secrets.py`. Verifier will `git diff --exit-code` these against the phase-start commit.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`text_render.text(fb, s, x, y, scale, color)`** — the scaled font renderer already used by `weather_view` for the temperature. `clock_view.render` reuses it via the module-local `_center_text` helper pattern (copied from `main.py` or `weather_view.py`).
- **`ntptime.settime()`** — MicroPython stdlib; a single blocking call that syncs the internal RTC. No config needed for the default NTP pool. Raises `OSError` on failure — matches the broad-exception pattern already used by `weather.py`.
- **`_POLL_MS = 100` in main.py** — the existing scheduler tick. `clock_view`'s predicates plug into the same loop; no changes to the poll cadence.
- **The stateless `render(oled)` pattern from `weather_view.render`** — read cached module state, write to the framebuffer, return. `clock_view.render` follows the same shape.
- **`_center_text` helper pattern (present in main.py and weather_view.py)** — inline into `clock_view.py` as `_center_text(oled, s, x_center, y_center, scale)`.

### Established Patterns
- **Module-level UPPER_SNAKE_CASE constants for tunables** (`_REFRESH_MS`, `_RETRY_MS`, `_POLL_MS`, `_DEBOUNCE_MS`, `_KEY0_PIN`, `_KEY1_PIN`). `_SYNC_MS = 3_600_000` and `_RETRY_MS = 60_000` in `clock_view.py` follow this pattern.
- **`.format()` not f-strings** — mandatory for MicroPython idiom compliance.
- **Broad-exception fallback for network calls** — `weather.py` returns `(None, None, None)` on any exception; `clock_view.sync` mirrors this by catching `Exception` from `ntptime.settime()` and leaving `_synced` unchanged.
- **Stamp-at-start for scheduler predicates (D-33)** — `_last_sync_ms = time.ticks_ms()` at the START of `sync()`, before the blocking `ntptime.settime()` call, so a failed sync consumes one full retry window instead of tight-looping.

### Integration Points
- **`main.py` poll loop** — two new branch conditions after the existing `weather_view.should_refresh(now)` block:
  ```
  if _current_idx == 1 and clock_view.should_tick(now):
      clock_view.render(oled)
      _draw_page_dots(oled, _current_idx)
      oled.show()
  if clock_view.should_sync(now):
      clock_view.sync(oled)
  ```
  Position: between the weather-refresh block and `time.sleep_ms(_POLL_MS)`. Order matters slightly — `should_tick` first so a freshly-synced time renders on the next minute boundary, not on the same tick as the sync.
- **`TZ_OFFSET` config constant** — added to `main.py`'s user-config block. `clock_view.render` imports it lazily (top of `clock_view.py`) via `from main import TZ_OFFSET`. Lazy note: MicroPython allows this because `main.py` is fully loaded before `clock_view.render` is first called from the poll loop.
- **Boot-time sync attempt** — `main.py` calls `clock_view.sync(oled)` once at boot, after the existing `weather_view.refresh(oled)` boot call. If it fails, `_synced` stays False and `--:--` renders on view-switch to Clock; the poll loop's `should_sync` retries every 60 s. If it succeeds, next re-sync is in 1 h.
- **View-switch behavior** — inherits Phase 2 D-22 (on-view-switch = redraw cached data instantly). `main.py`'s existing carousel branch already calls `VIEWS[_current_idx].render(oled)` on button press; `clock_view.render` reads `_synced` + local time and renders the current minute. No changes to the carousel branch needed.

</code_context>

<specifics>
## Specific Ideas

- **User's exact directive on format:** 24-hour, no seconds — matches "minimum sufficient state" pattern. Interpretation locked as D-34.
- **1-hour re-sync cadence** — chosen over 6h/24h for tighter drift bound within a reasonable WiFi-cost envelope. RP2040 clock drift over 1 hour is well below the display's 1-minute resolution.
- **Symmetric retry semantics with Phase 2.1** — the 60s-until-success + revert-to-normal pattern from D-31 applies unchanged. No new state machine vocabulary — a boolean `_synced` replaces `_cache_status`'s string enum because the display doesn't need to distinguish `"no_wifi"` from `"no_data"` for the clock.
- **`--:--` means never-synced only** — not a stale indicator. Time stays visible after WiFi drops post-first-sync.
- **No `is_current` in predicates** — `should_tick` returns True on minute boundaries regardless of which view is active; `main.py` gates the re-render with `if _current_idx == 1 and ...`. Predicate purity mirrors `weather_view.should_refresh` which also doesn't know about the current view.
- **Boot sync + minute-boundary ticks** — the boot `clock_view.sync(oled)` attempt happens ONCE explicitly in `main.py`'s startup sequence, after the boot weather refresh. Subsequent syncs come from the poll loop's `should_sync` predicate.

</specifics>

<deferred>
## Deferred Ideas

- **Timezone label displayed on the Clock view** (e.g. `PST`, `+02`). Requires a `TZ_LABEL` config constant alongside `TZ_OFFSET`. User's timezone is already implicitly known from where the device sits; label is decorative. Deferred to v2.
- **Date / day-of-week displayed on the Clock view** (e.g. `Sat 18 Jul` under `19:47`). Not in CLOCK-01..05; would be new scope. Deferred to v2.
- **Sync-status visual indicator** (spinner, dot, "syncing..." text). Explicitly dropped in D-39 to keep the view minimal. Any signal about sync activity is deferred to a future "diagnostic overlay" if ever desired.
- **"Stale" state after N hours without a successful re-sync** (e.g. clock changes color, dims, or shows an indicator when local time is more than 24 h since last NTP success). Interesting but out of scope for v1 per D-37. Deferred.
- **DST rules** — explicitly out-of-scope per PROJECT.md decisions; a single hardcoded offset covers v1. Deferred to v2 alongside user-configurable timezone (CLOCK-06 in v2 backlog).
- **12-hour AM/PM format toggle** — considered in D-34 as option (c/d); rejected for v1. Could be a v2 config constant if a user asks.
- **Seconds display** — considered in D-34 as option (b); rejected because minute-boundary repaint is 60× cheaper. Could be revisited if a diagnostic mode is added.

</deferred>

---

*Phase: 3-Clock View*
*Context gathered: 2026-07-18*
