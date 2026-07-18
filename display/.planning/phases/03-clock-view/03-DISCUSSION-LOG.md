# Phase 3: Clock View — Discussion Log

**Date:** 2026-07-18
**Mode:** default (text-mode fallback — `gsd-sdk`/AskUserQuestion unavailable)
**Turns:** 5 areas, 1 follow-up. All 5 gray areas selected via `all`.

This log is for human reference only (audits, retrospectives) and is NOT
consumed by downstream agents (researcher, planner, executor). The
authoritative decision record lives in `03-CONTEXT.md`.

---

## Gray Areas Presented

The initial presentation surfaced 5 gray areas after loading prior context and
verifying against Phase 1 / Phase 2 / Phase 2.1 CONTEXT.md files. The user
selected `all`.

Domain: Clock view — NTP-synced local time with minute-boundary updates and a
`--:--` degraded state when NTP has never succeeded.

Prior-decision carryforward acknowledged (not re-asked):
- Stateless `render(oled)` per view, module-level cache (Phase 2 D-16/17/18).
- Poll scheduler with `_POLL_MS = 100`, no asyncio, no Timer (Phase 2 D-15).
- Rows 0–53 reserved for view content, page dots at y=60 (Phase 2 D-19/20/21).
- On-view-switch = instant redraw of cached data (Phase 2 D-22).
- 60s-retry-until-success + revert-to-normal-cadence pattern (Phase 2.1 D-31/32/33).
- Single hardcoded TZ offset at top of `main.py` (CLOCK-02, PROJECT.md).
- `--:--` when NTP never synced (CLOCK-05).
- Every-second updates while displayed (CLOCK-03) — refined by Area 1 to
  every-minute repaints since the display omits seconds.
- NTP sync at boot + periodic (CLOCK-04) — Area 2 selected the period.

---

## Area 1 — Time format

**Question:** `19:47` (24h no seconds) vs `19:47:03` (24h w/ seconds) vs `7:47 PM` (12h) vs `7:47:03 PM` (12h w/ seconds)?

**Options presented:**
- (a) `19:47` — 24h no seconds *(recommended)*
- (b) `19:47:03` — 24h with seconds
- (c) `7:47 PM` — 12h no seconds
- (d) `7:47:03 PM` — 12h with seconds

**User selection:** `a` — 24h no seconds.

**Rationale captured:** Minute-boundary repaint (1 write/min vs 60/min). Matches
"minimum sufficient state" pattern (page dots, degree ring, 3-tuple weather cache).
Simpler tick predicate.

**Recorded as:** D-34.

---

## Area 2 — NTP re-sync cadence + retry (3 sub-questions)

### 2a — Re-sync cadence after first success

**Options presented:**
- (a) Never re-sync — one shot at boot
- (b) Every 6 hours *(recommended)*
- (c) Every 1 hour
- (d) Every 24 hours

**User selection:** `c` — every 1 hour.

**Rationale captured:** Tighter drift bound than the recommendation; RP2040 drift
over 1 h is well below `HH:MM` resolution.

**Recorded as:** D-35.

### 2b — Retry pattern on NTP failure

**Options presented:**
- (a) Mirror Phase 2.1 (60s until success, revert to normal cadence) *(recommended)*
- (b) No retry — wait for the normal cadence
- (c) Boot-only retry

**User selection:** `a` — mirror Phase 2.1.

**Rationale captured:** Symmetric with `weather_view.should_refresh`. `clock_view.should_sync`
reads `_synced` inline exactly as `should_refresh` reads `_cache_status`. No new
mental model.

**Recorded as:** D-36.

### 2c — WiFi drop after first successful sync

**Options presented:**
- (a) Keep showing time as-is; try to re-sync at normal cadence *(recommended)*
- (b) Show `--:--` after N hours without successful re-sync ("stale" state)

**User selection:** `a` — keep showing time.

**Rationale captured:** `--:--` means only "never synced on this boot", not "stale".
Local clock's short-term accuracy after a WiFi blip is more useful than an error
state. Stale-state indicator deferred.

**Recorded as:** D-37.

---

## Area 3 — Tick integration into the poll scheduler

**Options presented:**
- (a) Two predicates + one sync function: `should_tick(now_ms)`, `should_sync(now_ms)`, `sync(oled)` *(recommended)*
- (b) Merge both into one `tick(now_ms)` that returns an enum
- (c) `main.py` computes minute boundary itself, only `should_sync` delegated

**User selection:** `a`.

**Follow-up:** should `should_tick` accept `is_current` or fire always?

**Follow-up options presented:**
- Default: predicate is pure (no `is_current`); `main.py` gates re-render with `if _current_idx == 1 and ...`
- Push-back: `no — pass is_current`

**User selection:** `ratified, continue` (accepted the default — pure predicate).

**Rationale captured:** Predicate purity mirrors `weather_view.should_refresh`.
`main.py` remains the coordinator that knows about `_current_idx`; `clock_view.py`
stays pure and testable.

**Recorded as:** D-38.

---

## Area 4 — Visual composition

**Options presented:**
- (a) Clock only, scale 3, centered *(recommended)*
- (b) Clock scale 3 + TZ label
- (c) Clock scale 2 + date line
- (d) Clock scale 3 + tiny sync-status pixel/dot

**User selection:** `a` — clock only.

**Rationale captured:** Mirrors the project's minimalist choices (page dots, no
view labels, single-tuple weather cache). TZ label / date / sync indicator all
deferred to v2.

**Recorded as:** D-39.

**Deferred captured:**
- TZ label → `<deferred>` in CONTEXT.md
- Date / day-of-week → `<deferred>` in CONTEXT.md
- Sync-status visual indicator → `<deferred>` in CONTEXT.md

---

## Area 5 — NTP-status state machine

**Options presented:**
- (a) Two-state boolean `_synced: bool` *(recommended)*
- (b) Three-state string (`"never_synced"` / `"synced"` / `"in_flight"`)
- (c) Three-state with visible `"in_flight"` — dropped (excluded by Area 4 (a))

**User selection:** `a` — single boolean.

**Rationale captured:** Smallest state that answers all requirements. `"in_flight"`
would be dead state — not surfaced visually per D-39. Matches
weather.py's 3-tuple minimalism.

**Recorded as:** D-40.

---

## Scope Creep Redirects

None — no scope-creep suggestions surfaced during the discussion. The user
selected all pre-identified gray areas and did not raise new capabilities.

---

## Claude's Discretion

None — every gray area had a user-selected concrete choice. Sub-decisions locked
by requirement wording (CLOCK-02 timezone location, CLOCK-05 error state format)
were noted as pre-answered and not put to a vote.

---

*End of Phase 3 discussion log.*
