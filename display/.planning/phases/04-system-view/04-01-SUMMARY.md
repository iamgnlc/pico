---
phase: 04-system-view
plan: 01
type: summary
status: complete-code-verified-human-pending
requirements:
  - SYSTEM-01
  - SYSTEM-02
  - SYSTEM-03
  - SYSTEM-04
commits:
  - 210f512
files_modified:
  - weather.py
  - weather_view.py
  - system_view.py
date: 2026-07-18
---

# Plan 04-01 Summary — System View (SYSTEM-01..04)

## What Shipped

`system_view.py` went from a 2-line stub to a full WiFi diagnostics view:
- **SSID** (y=8): connected AP name, truncated to 15 chars with no ellipsis; `SSID: --` when offline.
- **IP** (y=24): WAN IP (public, from ip-api's `query` field) — dual-gated on `wlan.isconnected() AND _cached_wan_ip is not None`; `IP: --` in any other case.
- **Signal** (y=40): `Signal ` label + 4 drawn vertical bars at x=56. Bars filled per RSSI thresholds (`>= -55` → 4, `-55..-65` → 3, `-65..-75` → 2, `< -75` → 1); all hollow when offline.

`weather.py` and `weather_view.py` extended to piggyback the WAN IP onto the existing ip-api round-trip — same pattern used for `tz_offset` in Plan 03-02.

`main.py` **unchanged** — Phase 4's whole design goal was zero poll-loop churn. The existing carousel branch (`VIEWS[_current_idx].render(oled)` on button press) already dispatches to `system_view.render` when `_current_idx == 2`.

## Requirements Delivered (code-verified)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| SYSTEM-01 (connected SSID) | Code ✓ | `wlan.config("essid")` read inline in `render(oled)`; truncation at `min(15, WIDTH // 8)` |
| SYSTEM-02 (device IP address — interpreted as WAN IP per D-43-bis) | Code ✓ | ip-api `query` field piggybacked in `weather.current()`; forwarded via `system_view.set_wan_ip` from `weather_view.refresh`; rendered with dual-gate |
| SYSTEM-03 (signal strength as dBm OR bars) | Code ✓ | 4 drawn bars via `_draw_bars` + `_rssi_to_bars` (bars-only per D-42) |
| SYSTEM-04 (offline state clarity) | Code ✓ | Uniform `--` for all three fields when `wlan.isconnected() == False` (D-44) |

## Decisions Honored

- **D-41**: View-switch-only refresh — no `should_tick` predicate; `network.WLAN` reads inline in `render(oled)`. Zero poll-loop changes.
- **D-42**: Bars-only signal; RSSI thresholds -55/-65/-75; no dBm text.
- **D-43**: 3-line left-aligned list at y=8/24/40 inside rows 0–53.
- **D-43-bis**: WAN IP from ip-api's `query` field; RAM-only cache (no file); dual-gate on connected + cache-populated.
- **D-44**: Uniform `--` for all fields when offline (no last-known SSID reveal).
- **D-45**: Read-only — zero `wlan.connect` / `wlan.disconnect` / `wlan.active` refs in system_view.py.

## Threat Model Outcome

Zero HIGH severity threats materialized. Notable:
- **T-04-01-01** (`wlan.status("rssi")` could raise on unsupported firmware) — mitigated by try/except in `render`; falls back to 0 bars.
- **T-04-01-06** (`wlan.config("essid")` may return bytes on some firmware) — documented as a defensive follow-up; if on-device verify shows bytes rendering as `b'...'`, a Task-3.5 will add `.decode()`.
- **T-04-01-07** (circular import) — verified: `system_view` imports only `network`, `text_render`, `WIDTH from sh1107`. No back-edges.

## Automated Verification (all 34 pass)

| # | Check | Result |
|---|-------|--------|
| 1 | `weather.py` syntax | ok |
| 2 | URL includes `?fields=lat,lon,offset,query` | ok |
| 3 | `wan_ip = loc.get("query")` extraction | ok |
| 4 | 5-tuple success return | ok |
| 5 | 5-tuple failure return | ok |
| 6 | `weather_view.py` syntax | ok |
| 7 | `import system_view` present | ok |
| 8 | 5-tuple unpack | ok |
| 9 | `system_view.set_wan_ip(wan_ip)` call | ok |
| 10 | Existing `clock_view.set_tz_offset(tz_offset)` preserved | ok |
| 11 | Spinner-free (quick 260718 preserved) | ok |
| 12 | `system_view.py` syntax | ok |
| 13 | `import network` present | ok |
| 14 | `import text_render` present | ok |
| 15 | `from sh1107 import WIDTH` present | ok |
| 16 | `_cached_wan_ip = None` state | ok |
| 17 | `_draw_bars` signature | ok |
| 18 | `_rssi_to_bars` signature | ok |
| 19 | `set_wan_ip` signature | ok |
| 20 | None guard in setter | ok |
| 21 | Same-value guard in setter | ok |
| 22 | `render` signature | ok |
| 23 | `wlan.isconnected()` read | ok |
| 24 | `wlan.config("essid")` read | ok |
| 25 | `wlan.status("rssi")` read | ok |
| 26 | IP dual-gate present | ok |
| 27 | RSSI thresholds -55/-65/-75 | ok |
| 28 | Exactly 4 `def` in system_view.py | ok |
| 29 | Zero docstrings | ok |
| 30 | Exactly 3 imports in system_view.py | ok |
| 31 | Zero WiFi write ops (D-45) | ok |
| 32 | Zero predicates (D-41) | ok |
| 33 | Zero file I/O (D-43-bis) | ok |
| 34 | Zero diff on 6 non-target source files | ok |

## Deferred to End-of-Phase Batch (blocking)

Task 5 human-verify — 8 scenarios on-device (see 04-01-PLAN.md `<how-to-verify>`):

1. Cold-boot: SSID + signal render immediately; IP shows `--` until first weather fetch populates cache.
2. Post-fetch: navigate back to System — IP now shows WAN IP.
3. SSID truncation for long AP names.
4. Signal-bar count changes as device moves closer to / farther from AP.
5. Offline behavior: all three fields uniform `--`.
6. Recovery: reconnect → next scheduled weather refresh → all fields repopulate.
7. View-switch responsiveness: < 100 ms (no visible lag).
8. Read-only structural verification: no WiFi write ops in system_view.py.

Watch for the T-04-01-06 defensive fallback — if SSID appears as `b'...'` instead of a clean string, executor adds `.decode()` in a follow-up commit.

## Commits

| Commit | Description |
|--------|-------------|
| `210f512` | feat(04-01): system view — SSID + WAN IP + signal bars (SYSTEM-01..04) |

## Next

Phase 4 is code-complete. On-device human-verify batch is the only remaining gate before Phase 4 (and v1) can be marked complete.
