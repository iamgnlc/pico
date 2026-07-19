---
gsd_state_version: 1.0
milestone: none
milestone_name: (between milestones)
previous_milestone: v1.0
previous_milestone_tag: v1.0
previous_milestone_archived_at: "2026-07-18T20:15:00.000Z"
status: milestone_archived
stopped_at: v1.0 archived and tagged (fold-into-v1.0 packaging). Ready for /gsd:new-milestone when the operator wants to scope v1.1 or v2.
last_updated: "2026-07-19T09:20:00.000Z"
last_activity: 2026-07-19
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-15)

**Core value:** Pressing a button changes the view instantly and reliably; each view stays accurate on its own refresh cadence without user intervention.
**Current focus:** v1 COMPLETE — all 24 v1 requirements delivered, all 5 phases code + on-device verified. Ready for `/gsd:complete-milestone` to archive and plan v2.

## Current Position

Phase: 5 of 5 (v1 milestone complete)
Plan: 10/10 shipped and verified
Status: v1 milestone ready to archive
Last activity: 2026-07-18

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 3
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: none yet
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Phase 1: Move credentials to gitignored `secrets.py`; provide `secrets.py.example`
- Phase 1: Render `°` via custom drawn glyph — default 8×8 framebuf font has no degree character
- Phase 2: Carousel only — no menu/list navigation; KEY0 = prev, KEY1 = next; wraps at ends
- Phase 2: Always boot to Weather view; no persistence across reboots
- Phase 2 (D-13/14/15): KEY0/KEY1 via `Pin.irq(FALLING)` + ticks_ms software debounce; main loop is a ticks_ms poll scheduler (no asyncio, no machine.Timer)
- Phase 2 (D-16/17/18): Three flat view files (`weather_view.py`, `clock_view.py`, `system_view.py`) with `render(oled)` stateless interface; carousel state in `main.py`
- Phase 2 (D-19/20/21): Page dots at y=60, r=2, 12px spacing, filled active + hollow inactive; view content restricted to rows 0-53
- Phase 2 (D-22): On-view-switch = redraw cached data instantly; 600s cadence in the scheduler
- Phase 2 (D-23): Boot sequence = "connecting..." static during wifi.connect(), then spinner during weather fetch
- Phase 2 (D-24): Clock and System stubs render fully blank in Phase 2 — page dots only
- Phase 2.1 (D-31/32/33): should_refresh reads _cache_status inline; 60s if not "ok", 600s if "ok"; boot-fetch failure = immediate 60s retry mode; stamp-at-start unchanged
- Phase 2.1 (2026-07-18): WEATHER-08 (location label) dropped after Plan 02.1-01 layout regression → revert `b8823ab`. D-26..D-30 retired; Phase 2.1 narrowed to retry-only
- Phase 3 (D-34): Clock format `HH:MM` 24h no seconds; repaint at minute boundaries only
- Phase 3 (D-35/36/37): NTP re-sync every 1h after first success; 60s retry-until-success mirrors Phase 2.1 pattern; WiFi drop post-first-sync keeps time visible (`--:--` = never-synced only)
- Phase 3 (D-38): `clock_view.should_tick(now_ms)` + `should_sync(now_ms)` + `sync(oled)` — pure predicates; `main.py` gates re-render with `_current_idx == 1`
- Phase 3 (D-39): `HH:MM` scale 3 centered at (64, 27); no TZ label / date / sync indicator (all deferred to v2)
- Phase 3 (D-40): Single boolean `_synced` state; no enum
- Phase 3 (2026-07-18, Plan 03-02): CLOCK-02 redirected from "hardcoded `TZ_OFFSET` in main.py" to "auto-derived from ip-api's `offset` field on each weather fetch, persisted to `tz_offset.txt` with flash-wear guard, loaded at module import so subsequent boots show correct time as soon as NTP syncs". Clock renders `HH:MM` iff both `_synced` and `_cached_tz_offset is not None`. T-03-01-07 (circular import) retired.
- Cross-phase (2026-07-18, quick 260718-remove-spinner-tune-cadence): Phase 2 D-23 (spinner during weather HTTP fetch) RETIRED. Phase 3 D-35 (NTP re-sync cadence) UPDATED from 1h to 6h. Weather refresh (600s) and both retry cadences (60s) unchanged. Predicate shapes unchanged.
- Phase 4 (D-41): System view = view-switch-only refresh. No `should_tick` predicate. Reads `network.WLAN` primitives inline in `render(oled)`.
- Phase 4 (D-42): Signal strength = 4 drawn bars (RSSI thresholds -55/-65/-75); no dBm text.
- Phase 4 (D-43): Layout = 3-line left-aligned list at scale 1 (SSID / IP / Signal + bars) inside rows 0-53.
- Phase 4 (D-43-bis): IP field = WAN IP (public), sourced from ip-api's `query` field via extended `weather.current()` 5-tuple; cached RAM-only in `system_view._cached_wan_ip`; shows `--` when either offline OR cache is None.
- Phase 4 (D-44): Offline UX = uniform `--` for all three fields (SSID, IP, empty bars). No last-known SSID with `(offline)` marker.
- Phase 4 (D-45): System view is READ-ONLY — no reconnect attempts. Relies on `weather_view.refresh`'s existing 1-min retry / 10-min normal cadence.
- Cross-phase (2026-07-19, quick 260719-f0b): Cross-view setter dispatch moved out of weather_view.refresh into main._refresh_all. weather_view.refresh(oled) removed; replaced by weather_view.set_data(ip, temp, code, is_day) — a pure state-setter with no oled parameter and no cross-view calls. main.py now imports bootstrap and owns the boot + scheduler-tick fan-out to weather_view.set_data + clock_view.set_tz_offset + system_view.set_wan_ip + weather_view.render. bootstrap.py unchanged.

### Pending Todos

None yet.

### Blockers/Concerns

- WiFi credentials are currently committed in `main.py:9-10` — must be remediated in Phase 1 before any public push
- SH1107 driver has four hardware gotchas (see CLAUDE.md and .planning/codebase/CONCERNS.md); any `sh1107.py` changes must preserve them

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260718-scope-cleanup-phase-2.1 | Narrow Phase 2.1 scope to retry-only after Plan 02.1-01 revert | 2026-07-18 | — | [260718-scope-cleanup-phase-2.1](./quick/260718-scope-cleanup-phase-2.1/) |
| 260718-remove-spinner-tune-cadence | Retire D-23 spinner + update D-35 NTP cadence to 6h | 2026-07-18 | `93064bd` | [260718-remove-spinner-tune-cadence](./quick/260718-remove-spinner-tune-cadence/) |
| 260718-rename-bootstrap | Rename weather.py → bootstrap.py; absorb wifi.connect into a private helper; 6-tuple fetch() | 2026-07-18 | `bb2d763` | [260718-rename-bootstrap](./quick/260718-rename-bootstrap/) |
| 260719-e5g | Move view modules (weather_view/clock_view/system_view) into `views/` package | 2026-07-19 | `dcb4470` | [260719-e5g-move-view-modules-to-views-subdirectory](./quick/260719-e5g-move-view-modules-to-views-subdirectory/) |
| 260719-f0b | Decouple weather_view from sibling views; move cross-view setter dispatch to main._refresh_all | 2026-07-19 | — | [260719-f0b-decouple-weather-view-from-sibling-views](./quick/260719-f0b-decouple-weather-view-from-sibling-views/) |

## Session Continuity

Last session: 2026-07-19T09:20:00Z
Stopped at: Completed quick task 260719-e5g — moved the three view modules into a `views/` package (git mv preserved history; imports rewritten; CLAUDE.md path references patched). Operator to `mpremote cp -r views/ ...` for on-device verification. Still between milestones — `/gsd:new-milestone` remains the natural next command.
Resume file: n/a — between milestones. `/gsd:new-milestone` is the natural next command.
