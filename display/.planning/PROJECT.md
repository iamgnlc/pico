# Pico OLED Multi-View

## Current State — v1.0 SHIPPED (2026-07-18)

All 4 v1 requirements categories delivered end-to-end and human-verified on device:

- **Security**: SEC-01/02/03 — WiFi creds gitignored, secrets.py.example committed, prior creds rotated
- **Navigation**: NAV-01..06 — two-button carousel, debounce, wrap-around, page dots, boot-to-Weather
- **Weather view**: WEATHER-01..05, WEATHER-09 — icon + degree-glyph temp, 10-min refresh + view-switch redraw, error states, 60s fetch-retry
- **Clock view**: CLOCK-01..05 — NTP-synced HH:MM, auto-derived timezone (ip-api piggyback + persistence), 6h re-sync + 60s retry, `--:--` fallback
- **System view**: SYSTEM-01..04 — SSID + WAN IP + drawn signal bars, uniform `--` offline state

Git tag: `v1.0` at `a20bb0e`. Archive: `.planning/milestones/v1.0-ROADMAP.md` + `v1.0-REQUIREMENTS.md`.

**WEATHER-08 (location label) was dropped mid-milestone** after Plan 02.1-01 shipped and human-verify caught a layout regression. See archive for the full audit trail.

## Next Milestone Goals

*No milestone declared yet. Run `/gsd:new-milestone` to begin scoping. Deferred v2 candidates from v1's REQUIREMENTS.md § "v2 Requirements" (WEATHER-06/07, CLOCK-06/07, NAV-07/08) will need to be re-scoped and prioritized.*

Additional deferred UX ideas surfaced during v1 phase discussions (see `milestones/v1.0-ROADMAP.md § Deferred UX Ideas` for the full list): TZ label, date display, sync indicator, "stale" state, 12h AM/PM, seconds, dBm text, last-known SSID marker, local IP alongside WAN IP, etc.

<details>
<summary>v1.0 archived context (click to expand)</summary>

## What This Is

A MicroPython app for a Raspberry Pi Pico W driving a Waveshare Pico-OLED-1.3 HAT (128×64, SH1107). Two physical buttons on the HAT cycle through a small set of always-on info views — weather, clock, system status — with a page-dot indicator showing position in the carousel.

## Core Value

Pressing a button changes the view instantly and reliably; each view stays accurate on its own refresh cadence without user intervention.

## Requirements

### Validated

<!-- Shipped and confirmed valuable — inferred from existing code. -->

- ✓ SH1107 SPI driver with framebuf.FrameBuffer subclass — existing (`sh1107.py`)
- ✓ Text rendering with integer scale factor — existing (`text_render.py`)
- ✓ Weather-icon glyphs for Open-Meteo weather codes — existing (`icons.py`)
- ✓ Bootstrap round-trip: WiFi connect + ip-api geolocation + Open-Meteo forecast (single 6-tuple return) — existing (`bootstrap.py`, consolidated from former `wifi.py` + `weather.py` at post-v1 refactor)
- ✓ Single-view weather demo with 10-minute refresh — existing (`main.py`)
- ✓ Optional 180° display rotation via `ROTATE` config — existing (`main.py:12`, `sh1107.py`)

### Active

<!-- v1 scope. Building toward these. -->

- [ ] Two-button navigation (KEY0 = previous view, KEY1 = next view) with debounce
- [ ] View carousel with three v1 views: Weather, Clock, System status
- [ ] Boot to Weather view by default (no persistence across reboots)
- [ ] Page-dot indicator showing current position in the carousel
- [ ] Weather view renders temperature with a degree symbol (e.g. `19°`) instead of `19C`
- [ ] Clock view synchronized via NTP over WiFi with a timezone offset auto-derived from ip-api geolocation (piggybacked on the weather fetch) and persisted across reboots in `tz_offset.txt`
- [ ] System view displays SSID, IP address, and WiFi signal strength
- [ ] Per-view refresh policy: Weather every 600s + on view-switch; Clock every 1s; System on view-switch
- [ ] Graceful WiFi-failure behavior: affected views show a clear error state; background reconnect
- [ ] Move WiFi credentials from `main.py` to a gitignored `secrets.py`
- [ ] Rotate the currently-exposed WiFi credentials before shipping

### Out of Scope

<!-- Explicit boundaries. Reasons prevent re-adding later. -->

- Multi-day / hourly weather forecast — v1 stays single-value current conditions
- Menu- or list-style navigation — carousel is intentionally the only navigation model
- Persisting last-viewed screen across reboots — always boot to Weather by design
- Hardware RTC or offline clock — Clock view depends on NTP; without WiFi it shows an error
- User-configurable timezone / DST logic — one hardcoded offset in config
- Per-view button actions beyond prev/next — buttons are exclusively navigation in v1
- Long-press behavior — short-press only in v1
- Additional views (calendar, notifications, sensors, etc.) — v1 is Weather + Clock + System only
- Host-side tests — this remains an on-device only project (per `CLAUDE.md`)

## Context

- **Hardware is fixed by the HAT.** The Pico-OLED-1.3 dictates the SPI pinout (DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1) and the two-button pinout (KEY0=GP15, KEY1=GP17 on the standard Waveshare HAT). Not user-configurable.
- **SH1107 driver is hardened.** `sh1107.py` documents four non-obvious gotchas (single-byte `0x21`, per-byte CS toggling in `show()`, framebuf-pixel-level rotation only, MONO_HMSB required). Any driver change must respect them.
- **APIs are free and keyless.** ip-api for geolocation, Open-Meteo for forecast — no secrets to manage for weather.
- **No test infrastructure.** Everything runs on-device; validation is manual via `mpremote` or Thonny.
- **WiFi credentials are currently in `main.py:9-10` and are tracked in git.** Rotating and moving them is a v1 requirement, not a stretch goal.
- **Default framebuf font is ASCII-only (8×8).** No `°` glyph — rendering it requires either a custom mini-glyph or a small drawn circle.

## Constraints

- **Tech stack**: MicroPython on Pico W — no host-side tooling, no external Python packages beyond what the firmware ships with (`urequests`, `network`, `framebuf`, `machine`, `time`, `ntptime`).
- **Hardware**: Waveshare Pico-OLED-1.3 HAT — pinout fixed; only 128×64 monochrome.
- **Memory**: Pico W has ~264 KB SRAM; the framebuffer is 1024 bytes and must stay reusable — no per-frame allocations in the render loop.
- **Rendering**: SH1107 driver quirks documented in `CLAUDE.md` — any changes to `sh1107.py` must preserve the four gotchas.
- **Networking**: Weather/clock views assume WiFi; System view must remain usable when offline.
- **Security**: `secrets.py` must be gitignored; example file (`secrets.py.example`) may be committed.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Carousel navigation, not menu | Simplest UX for two-button hardware; no state machine beyond current index | — Pending |
| Boot to Weather, no view persistence | Weather is the primary use case; simpler than flash-writes for a single int | — Pending |
| Show page dots as position indicator | Cheap to draw, immediately readable, no font/text work | — Pending |
| WiFi-required views show error, background reconnect | Keeps device usable in offline moments; System view acts as diagnostic | — Pending |
| Move WiFi creds to gitignored `secrets.py` | Current creds are committed to git; needs remediation before further work | — Pending |
| Keep 600s weather refresh | Existing setting is already appropriate for API churn / weather change rate | — Pending |
| TZ offset auto-derived from ip-api + persisted on device | Removes the "user must edit config for every location and DST transition" chore; ip-api's `offset` field is DST-aware; persistence means correct time appears immediately after NTP sync on subsequent boots (no need to wait for a weather fetch first) | — Pending |
| Render `°` via custom draw (not font swap) | Default 8×8 framebuf font lacks the glyph; a small circle is cheaper than shipping a new font | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-15 after initialization; archived under v1.0 milestone close on 2026-07-18.*

</details>
