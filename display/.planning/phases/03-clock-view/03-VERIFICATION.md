---
phase: 03-clock-view
type: verification
status: passed
verified_by: operator (on-device)
date: 2026-07-18
requirements:
  - CLOCK-01
  - CLOCK-02
  - CLOCK-03
  - CLOCK-04
  - CLOCK-05
plans:
  - 03-01
  - 03-02
---

# Phase 3 Verification — Clock View

## Verdict

**PASSED** — on-device human-verify approved by operator on 2026-07-18 after the mid-verify fix (`c23bb5a`).

## Scope Covered

Phase 3 shipped the full Clock view: NTP-synced local time with automatic timezone derivation and cross-boot persistence. Two plans landed:

1. **Plan 03-01** — NTP-synced `HH:MM` clock, two pure predicates (`should_tick` + `should_sync`) plus `sync` and `render`, single boolean `_synced` state, scale-3 centered layout with `--:--` fallback.
2. **Plan 03-02** (gap closure) — CLOCK-02 redirect from "hardcoded TZ_OFFSET in main.py" to "auto-derived from ip-api's `offset` field, persisted to `tz_offset.txt` with flash-wear guard, loaded at module import".

## Mid-Verify Deviation

During human-verify of Plan 03-02, the operator reported: `tz_offset.txt` was never created and the Clock view stayed at `--:--` indefinitely.

**Root cause:** the ip-api URL requested no explicit `?fields=` param, so ip-api's default response was returned. The default response omits the `offset` field (it includes only `status, country, countryCode, region, regionName, city, zip, lat, lon, timezone, isp, org, as, query`). `loc.get("offset")` returned `None`, `set_tz_offset(None)` early-returned, and the persistence file was never written.

**Fix:** `c23bb5a fix(03-02): request offset field explicitly from ip-api` — changed the URL to `http://ip-api.com/json/?fields=lat,lon,offset`. Surgical one-line change; zero impact on the rest of Plan 03-02's design.

**Post-fix re-verify:** operator confirmed `tz_offset.txt` is now created after the first weather fetch and the Clock view displays the correct local time.

## Automated Verification (all pass)

- Plan 03-01: 22 assertions at commit `3b506a0`.
- Plan 03-02: 28 assertions at commits `44f5d4a` (initial) + `c23bb5a` (fix — URL check added).

All 50 automated checks pass across both plans.

## Human Verification (approved)

Operator confirmed on-device behavior:

1. **Success path**: after the URL fix, `tz_offset.txt` is created on the device after the first successful weather fetch and contains the correct integer offset. Clock view displays the correct local `HH:MM` once both `_synced` and `_cached_tz_offset` are populated. ✓ (approved)
2. **Fallback**: with either `_synced == False` OR `_cached_tz_offset is None`, Clock view shows `--:--`. ✓ (structurally guaranteed by the dual-gate in `should_tick` + `render`; observed during the pre-fix run where the offset was missing)
3. **Minute-boundary tick**: display repaints only at minute boundaries (implicit in the operator's approval — no reported flicker).
4. **View-switch responsiveness**: KEY0/KEY1 continue to work as expected across all views (no regression reported).

## Requirements Traceability

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CLOCK-01 (NTP-synced current time) | Complete | `ntptime.settime()` in `clock_view.sync`; `time.localtime` in `render`; commits `3b506a0` (initial) + `44f5d4a` (state gate) |
| CLOCK-02 (TZ offset auto-derived + persisted) | Complete (redirected) | ip-api `offset` piggyback in `weather.current()`; `clock_view.set_tz_offset` writes `tz_offset.txt`; module-load read; commits `44f5d4a` + `c23bb5a` |
| CLOCK-03 (updates every second while displayed → refined to minute-boundary repaints per D-34) | Complete | `should_tick` minute-boundary predicate; commit `3b506a0` |
| CLOCK-04 (NTP sync at boot + periodic) | Complete | Boot call `clock_view.sync(oled)`; periodic via `should_sync` at 1h cadence (D-35) with 60s retry (D-36) |
| CLOCK-05 (`--:--` when NTP never succeeded) | Complete | `render(oled)` dual-gate; commit `44f5d4a` extended to also require offset |

## Standing Preconditions Confirmed

- WiFi credentials current on device (implicit — weather + NTP fetches would fail otherwise).
- No manual `TZ_OFFSET` config required (per redirected CLOCK-02).

## Commits (Phase 3 lineage)

| Commit | Summary |
|--------|---------|
| `a422799` | docs(03): phase plan — 1 plan, 1 wave (clock view) |
| `3b506a0` | feat(03-01): NTP-synced clock view (CLOCK-01..05) |
| `6b47758` | docs(03-01): plan summary + STATE update — Phase 3 code-complete |
| `7e2ff9b` | docs(03-02): gap-closure plan — TZ from location, persisted |
| `44f5d4a` | feat(03-02): auto-derive TZ offset from ip-api, persist on device (CLOCK-02) |
| `1732659` | docs(03-02): plan summary + REQUIREMENTS/PROJECT/STATE updates |
| `c23bb5a` | fix(03-02): request offset field explicitly from ip-api |

## Retired Threats (from Plan 03-01)

- **T-03-01-07** — circular import `main → clock_view → main` via `from main import TZ_OFFSET`. Retired at Plan 03-02 (clock_view no longer imports from main).

## Deferred Items

- TZ label displayed on the Clock view — deferred to v2.
- Date / day-of-week displayed on the Clock view — deferred to v2.
- Sync-status visual indicator — deferred to v2.
- "Stale" state after N hours without a successful re-sync — deferred to v2.
- 12-hour AM/PM toggle — deferred to v2.
- Seconds display — deferred (would be a new mode).
- User-configurable location override (bypassing ip-api geolocation) — v2 backlog WEATHER-07 already tracks the location-fetch side; the same override would apply to TZ derivation.
