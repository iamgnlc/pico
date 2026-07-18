---
phase: 03-clock-view
plan: 02
type: summary
status: complete-code-verified-human-pending
requirements:
  - CLOCK-02
gap_closure: true
commits:
  - 7e2ff9b
  - 44f5d4a
files_modified:
  - weather.py
  - weather_view.py
  - clock_view.py
  - main.py
  - .gitignore
  - .planning/REQUIREMENTS.md
  - .planning/PROJECT.md
date: 2026-07-18
---

# Plan 03-02 Summary — TZ from Location, Persisted (CLOCK-02 redirect)

## What Shipped

Redirected CLOCK-02 from manual `TZ_OFFSET` config to fully automatic derivation + persistence.

**Behavior:**
- On every successful weather fetch, `weather_view.refresh` calls `clock_view.set_tz_offset(offset)` with ip-api's `offset` field (int seconds from UTC, DST-aware).
- `set_tz_offset` updates `_cached_tz_offset` in memory AND writes `tz_offset.txt` — but only when the new value differs from what's cached (flash-wear guard).
- On module load, `clock_view.py` reads `tz_offset.txt` inside a broad `try/except` and populates `_cached_tz_offset` if it exists. Failure → `None`.
- Clock renders `HH:MM` iff BOTH `_synced == True` AND `_cached_tz_offset is not None`. Otherwise `--:--`.
- `main.py` no longer has a `TZ_OFFSET` config constant.

**Key UX property:** On reboots after the first-ever successful weather fetch, the file is loaded at module import, so the clock can display the correct local time as soon as NTP syncs — no need to wait for a weather fetch of the new session to complete first.

## Requirements Delivered (code-verified)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CLOCK-02 (redirected — auto-derived + persisted) | Code ✓ | `weather.current()` 4-tuple with `offset`; `weather_view.refresh` → `clock_view.set_tz_offset`; module-load file read; state gate in `should_tick`/`render`. `main.py` no longer defines TZ_OFFSET. |

CLOCK-01, CLOCK-03, CLOCK-04, CLOCK-05 unchanged from Plan 03-01 — this plan does not touch them.

## Decisions Traced

- **D-31 (Phase 2.1) reused**: `set_tz_offset`'s state model — "value differs?" guard mirrors the "cache status inline" style. No enum, no new state machine.
- **D-33 (Phase 2.1) unchanged**: `sync(oled)` still stamps `_last_sync_ms` at the START; the `set_tz_offset` writer does NOT touch `_last_sync_ms` (different concerns — NTP timing vs. offset value).
- **D-37 upheld**: If `_synced` is False (NTP never succeeded this boot), the display shows `--:--` even when a persisted offset is available. This preserves the "NTP is authoritative" posture — a persisted offset without a synced clock could still show hours-off time due to RP2040 drift since the last power-on.
- **D-38 tightened**: `should_tick`'s pure-predicate contract now returns True in TWO cases: (a) both bits set + minute changed, or (b) either bit missing + we haven't yet rendered the `--:--` state (`_last_render_min != -1`). This is a small extension of D-38, not a violation.
- **D-40 preserved (extended)**: State is still minimal — added ONE boolean-equivalent state field (`_cached_tz_offset: Optional[int]`) rather than a new enum.

## New Threats Introduced (from PLAN's threat model)

Zero HIGH severity.

| Threat ID | Category | Disposition |
|-----------|----------|-------------|
| T-03-02-01 | Excessive flash writes | mitigate (flash-wear guard in set_tz_offset) |
| T-03-02-02 | Malicious ip-api response | accept (same posture as any consumer geo service) |
| T-03-02-03 | open() failure at module load hanging import | mitigate (broad try/except) |
| T-03-02-04 | open() failure during set_tz_offset silently drops update | accept (graceful degradation) |
| T-03-02-05 | Malformed `tz_offset.txt` crashing module load | mitigate (broad try/except catches parse errors) |
| T-03-02-06 | Circular import weather_view → clock_view → weather_view | mitigate (verified: clock_view does not import weather_view) |

**Retired:** T-03-01-07 (circular import `main → clock_view → main`). The lazy-import workaround is no longer needed — clock_view no longer imports from main.

## Automated Verification (all 28 pass)

| # | Check | Result |
|---|-------|--------|
| 1 | `weather.py` syntax | ok |
| 2 | `offset = loc.get("offset")` extraction present | ok |
| 3 | 4-tuple success return | ok |
| 4 | 4-tuple failure return | ok |
| 5 | `weather_view.py` syntax | ok |
| 6 | `import clock_view` present | ok |
| 7 | 4-tuple unpack in refresh | ok |
| 8 | `clock_view.set_tz_offset(tz_offset)` call present | ok |
| 9 | `clock_view.py` syntax | ok |
| 10 | `_cached_tz_offset = None` state | ok |
| 11 | `_TZ_OFFSET_FILE = "tz_offset.txt"` constant | ok |
| 12 | Module-load `with open(_TZ_OFFSET_FILE) as f:` read | ok |
| 13 | `int(f.read().strip())` parse | ok |
| 14 | `def set_tz_offset(offset):` signature | ok |
| 15 | None-guard in setter | ok |
| 16 | Same-value flash-wear guard in setter | ok |
| 17 | `with open(_TZ_OFFSET_FILE, "w") as f:` write in setter | ok |
| 18 | Dual-gate `_synced and _cached_tz_offset is not None` present in BOTH should_tick and render (exactly 2 occurrences) | ok |
| 19 | `should_tick` sentinel `return _last_render_min != -1` | ok |
| 20 | Zero remaining `from main import TZ_OFFSET` lazy imports | ok |
| 21 | Sync interval selection (D-31 shape) unchanged | ok |
| 22 | Sync stamp-at-start (D-33) unchanged | ok |
| 23 | `main.py` syntax | ok |
| 24 | `TZ_OFFSET` removed from main.py | ok |
| 25 | Boot sync call unchanged | ok |
| 26 | Poll tick branch unchanged | ok |
| 27 | Poll sync branch unchanged | ok |
| 28 | `display/tz_offset.txt` in `.gitignore` + `git check-ignore` confirms exclusion + zero diff on 5 unchanged source files | ok |

## Deferred to End-of-Phase Batch (blocking)

Task 7 human-verify — 6 scenarios on-device (see 03-02-PLAN.md `<how-to-verify>` for full script). Highlights:

1. First-boot with no persisted offset: `tz_offset.txt` created after first weather fetch; contains correct offset.
2. Local time correctness on Clock view.
3. Persistence across reboots: correct time on second boot as soon as NTP syncs, without needing a weather fetch.
4. DST/travel simulation: editing `tz_offset.txt` to a wrong value auto-corrects on the next weather fetch.
5. Offline behavior (no NTP, no persistence) shows `--:--`.
6. Offline with persistence but no NTP shows `--:--` (respects D-37).

## Commits

| Commit | Description |
|--------|-------------|
| `7e2ff9b` | docs(03-02): gap-closure plan — TZ from location, persisted |
| `44f5d4a` | feat(03-02): auto-derive TZ offset from ip-api, persist on device (CLOCK-02) |
| *(this commit)* | docs(03-02): plan summary + REQUIREMENTS/PROJECT/STATE updates |

## Next

Phase 3 is now code-complete on the redirected CLOCK-02. On-device human-verify batch (6 scenarios from Task 7) is the only remaining gate before Phase 3 can be marked complete and Phase 4 (System View) can begin.
