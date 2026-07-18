---
phase: 03-clock-view
plan: 01
type: summary
status: complete-code-verified-human-pending
requirements:
  - CLOCK-01
  - CLOCK-02
  - CLOCK-03
  - CLOCK-04
  - CLOCK-05
commits:
  - 3b506a0
files_modified:
  - clock_view.py
  - main.py
date: 2026-07-18
---

# Plan 03-01 Summary — Clock View (CLOCK-01..05)

## What Shipped

`clock_view.py` replaced its 2-line stub with the full implementation. `main.py` gained 8 lines of integration (config + boot call + two poll-loop branches).

**Clock view rendering:**
- `HH:MM` at scale 3 centered at (WIDTH // 2, 27) when synced.
- `--:--` at the same scale and position when NTP has never succeeded on this boot.
- Repaints only at minute boundaries when Clock is the current view.

**NTP sync cadence:**
- 1-hour cadence (`_SYNC_MS = 3_600_000`) after first success.
- 60-second retry (`_RETRY_MS = 60_000`) until first success.
- Selection is inline in `should_sync`: `interval = _SYNC_MS if _synced else _RETRY_MS` — same shape as Phase 2.1 `weather_view.should_refresh`.

**Behavioral properties (structurally verified; on-device confirmation deferred):**
- WiFi drop after first successful sync keeps time visible; `_synced` stays True; local RP2040 clock keeps counting; failed re-syncs are silent (D-37).
- Cold-boot NTP failure symmetrically enters 60s retry mode (D-32 pattern) — no special-case boot logic.
- `sync(oled)` stamps `_last_sync_ms` at the START so a failed sync consumes one full retry window instead of tight-looping (D-33).

## Requirements Delivered (code-verified)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CLOCK-01 (NTP-synced current time) | Code ✓ | `ntptime.settime()` in `clock_view.sync`; `time.localtime` in `render` |
| CLOCK-02 (single hardcoded TZ offset) | Code ✓ | `TZ_OFFSET = 0` in `main.py` user-config block |
| CLOCK-03 (updates every second while displayed) | Code ✓ (refined per D-34) | Minute-boundary repaints via `should_tick`; the "every second" wording was refined to "every minute displayed value change" by D-34 (24h no seconds) — the underlying poll cadence is unchanged at 100 ms |
| CLOCK-04 (NTP sync at boot + periodic) | Code ✓ | Boot call `clock_view.sync(oled)` in `main.py`; periodic via `should_sync` at 1h cadence |
| CLOCK-05 (`--:--` when NTP never succeeded) | Code ✓ | `render(oled)` branches on `_synced`; renders `--:--` at scale 3 when False |

## Decisions Honored

- **D-34**: `"{:02d}:{:02d}".format(t[3], t[4])` — 24h, no seconds.
- **D-35**: `_SYNC_MS = 3_600_000` — 1h cadence after first success.
- **D-36**: `_RETRY_MS = 60_000` + inline selection in `should_sync` — 60s retry until success, revert to 1h after.
- **D-37**: `sync(oled)` never resets `_synced` to False; the display keeps rendering `HH:MM` after post-first-sync WiFi drops.
- **D-38**: `should_tick`, `should_sync`, `sync`, `render` — pure predicates + one action; `main.py` gates re-render with `_current_idx == 1`.
- **D-39**: `_center_text(oled, s, WIDTH // 2, 27, scale=3)` — no TZ label, no date, no sync indicator.
- **D-40**: Single boolean `_synced` — no enum, no `_cache_status` clone.

## Automated Verification (all 22 pass)

| # | Check | Result |
|---|-------|--------|
| 1 | `python3 ast.parse(clock_view.py)` | syntax ok |
| 2 | `python3 ast.parse(main.py)` | syntax ok |
| 3 | `_SYNC_MS = 3_600_000` | ok |
| 4 | `_RETRY_MS = 60_000` | ok |
| 5 | `_synced = False` module state | ok |
| 6 | `_last_render_min = -1` module state | ok |
| 7 | `_last_sync_ms = 0` module state | ok |
| 8 | `def should_tick(now_ms):` | ok |
| 9 | `def should_sync(now_ms):` | ok |
| 10 | `def sync(oled):` | ok |
| 11 | `def render(oled):` | ok |
| 12 | `interval = _SYNC_MS if _synced else _RETRY_MS` (D-31 shape) | ok |
| 13 | `_last_sync_ms = time.ticks_ms()` (D-33 stamp-at-start) | ok |
| 14 | `ntptime.settime()` present | ok |
| 15 | Exactly 2 `from main import TZ_OFFSET` sites (T-03-01-07 mitigation) | ok |
| 16 | `"{:02d}:{:02d}".format(t[3], t[4])` HH:MM format | ok |
| 17 | `_center_text(oled, s, WIDTH // 2, 27, scale=3)` render coords + scale | ok |
| 18 | `TZ_OFFSET` in `main.py` | ok |
| 19 | `clock_view.sync(oled)` in `main.py` boot | ok |
| 20 | `if _current_idx == 1 and clock_view.should_tick(now):` poll branch | ok |
| 21 | `if clock_view.should_sync(now):` poll branch | ok |
| 22 | Zero diff on 7 non-target source files | ok |

## Deferred to End-of-Phase Batch (blocking)

Task 2 human-verify — 6 scenarios on-device:

1. **Success path** — Clock view shows local `HH:MM` within 1–2 s of boot (WiFi + valid TZ_OFFSET).
2. **Minute-boundary tick** — display transitions at approximately :00 s of each new minute, not more often.
3. **View-switch responsiveness** — KEY0/KEY1 flip immediately (within ~100 ms) while on Clock.
4. **NTP failure retry** — with WiFi off, Clock shows `--:--`; measured interval between retries is ~60 s; recovery on WiFi restore flips to real time within one retry window.
5. **WiFi drop post-first-sync** — time stays visible; no revert to `--:--`.
6. **TZ_OFFSET behavior** — changing the constant and re-copying shifts the displayed hour by the expected offset.

Also confirm before running: valid `TZ_OFFSET` set in `main.py` for the device's location (`0` default = UTC).

## Commits

| Commit | Description |
|--------|-------------|
| `3b506a0` | feat(03-01): NTP-synced clock view (CLOCK-01..05) |

## Next

Phase 3 is code-complete. On-device human-verify batch (6 scenarios above) is the only remaining gate before Phase 3 can be marked complete and Phase 4 (System View) can begin.
