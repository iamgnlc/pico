# Phase 4: System View — Discussion Log

**Date:** 2026-07-18
**Mode:** default (text-mode fallback — `gsd-sdk`/AskUserQuestion unavailable)
**Turns:** 5 areas, 1 clarification, 1 confirmation. All 5 gray areas selected via `all`.

This log is for human reference only (audits, retrospectives) and is NOT
consumed by downstream agents (researcher, planner, executor). The
authoritative decision record lives in `04-CONTEXT.md`.

---

## Gray Areas Presented

Domain: System view — WiFi diagnostics (SSID, IP, signal strength) with clean offline behavior.

Prior-decision carryforward acknowledged (not re-asked):
- Poll-scheduler pattern (Phase 2 D-15).
- Stateless `render(oled)` per view (Phase 2 D-16/17/18).
- Rows 0-53 for view content, page dots at y=60 (Phase 2 D-19/20/21).
- On-view-switch = instant redraw (Phase 2 D-22).
- Retry pattern (Phase 2.1 D-31..D-33) — delegated to weather_view.
- Single-boolean state where possible (Phase 3 D-40).
- Pure predicates + main.py gates re-render (Phase 3 D-38) — applies even though Phase 4 has no predicate.

User selected: `all`.

---

## Area 1 — Data refresh strategy

**Options presented:**
- (a) View-switch only *(recommended)*
- (b) View-switch + periodic tick (every 5 s while active)
- (c) View-switch + reactive (diff on tick, re-render only on change)

**User selection:** `a` — view-switch only.

**Rationale captured:** SC#3 satisfied literally. No new predicate. `network.WLAN` reads are RAM-only, safe inline in render. Matches project's "less churn" ethos (just shipped D-35 6h relaxation, D-23 spinner retirement).

**Recorded as:** D-41.

---

## Area 2 — Signal-strength representation

**Options presented:**
- (a) Raw dBm text (`Signal: -52 dBm`)
- (b) Bars as text (`Signal: 4/4`)
- (c) Textual quality (`Signal: strong`)
- (d) Drawn bars icon
- (e) Hybrid drawn bars + dBm label *(recommended)*

**User selection:** `d` — drawn bars only, no dBm text.

**Rationale captured:** Matches project's small-drawn-glyph ethos (page dots, degree ring). Cleaner visual than the hybrid; if user wants the exact number, REPL is one command away.

**Recorded as:** D-42.

**Deferred:** dBm text alongside bars — noted as v2 diagnostic-mode candidate.

---

## Area 3 — Layout

**Options presented:**
- (a) 3-line vertical list at scale 1
- (b) SSID at scale 2 + supporting detail at scale 1
- (c) 3-line list at scale 1 with bars inline on the signal line *(recommended)*
- (d) 3-line list + drawn WiFi icon at top-left

**User selection:** `c, but Ip has to be WAN IP not local device IP`.

**Rationale captured:** Compact, readable, matches diagnostics ethos. WAN IP twist required extending `weather.current()` to 5-tuple and adding a `set_wan_ip` setter to system_view mirroring `set_tz_offset`.

**Confirmation gate:** Presented the design implications of WAN IP:
- Source: ip-api's `query` field (add to `?fields=` list)
- Cache: RAM-only in `system_view._cached_wan_ip`, not persisted
- Fresh boot: `--` for IP until first weather fetch
- Offline: `--` for IP regardless of cache (showing stale WAN IP while offline is misleading)

**User selection on confirmation:** `yes` — approved the WAN-IP design.

**Recorded as:** D-43 (layout) + D-43-bis (WAN IP source + cache + offline handling).

**Deferred:**
- Local IP alongside WAN IP → v2 diagnostic mode candidate.
- Timestamp of last successful WAN IP fetch → deferred.

---

## Area 4 — Offline UX

**Options presented:**
- (a) Everything shows `--`
- (b) SSID keeps last-known with `(offline)` marker *(recommended)*
- (c) Single centered `offline` message
- (d) Alternating pixel "grey" pattern (impractical on 1-bit)

**User selection:** `a` — uniform `--` for all fields.

**Rationale captured:** Uniform, unambiguous. The extra complexity of the last-known-SSID marker isn't worth it for a diagnostics view where "not connected → nothing is valid" is the operator's obvious mental model.

**Recorded as:** D-44.

**Follow-up sub-questions:** SKIPPED (only relevant if user picked (b)).

**Deferred:**
- Last-known SSID with `(offline)` marker → v2 diagnostic mode candidate.

---

## Area 5 — Background reconnect responsibility

**Options presented:**
- (a) System view is read-only — no reconnect attempts *(recommended)*
- (b) System view triggers reconnect on view-switch when offline
- (c) System view exposes manual reconnect action (long-press)

**User selection:** `a` — read-only.

**Rationale captured:** Clean separation of concerns. `weather_view.refresh` already reconnects at 1-min (offline) / 10-min (normal) cadence. System view stays passive. Long-press is v2-deferred anyway.

**Recorded as:** D-45.

---

## Scope Creep Redirects

None. No scope-creep suggestions surfaced during the discussion. The WAN-IP interpretation of SYSTEM-02 is a spec clarification, not scope expansion (the requirement wording already says "IP address" — the ambiguity resolves toward WAN).

---

## Claude's Discretion

None — every gray area had a user-selected concrete choice. Sub-decisions locked by prior context (bar geometry, RSSI thresholds) are documented in D-42/D-43 with "planner discretion" for pixel-level tuning during on-device verification.

---

*End of Phase 4 discussion log.*
