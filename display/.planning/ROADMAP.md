# Roadmap: Pico OLED Multi-View

## Overview

Four vertical phases take the existing single-view weather demo to a fully navigable three-view carousel. Phase 1 closes the credential leak and fixes the degree-symbol rendering — the two things blocking safe further development. Phase 2 builds the complete carousel shell and delivers the polished Weather view end-to-end. Phases 3 and 4 replace the Clock and System stubs with real implementations, completing v1.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Secure Foundation** - Rotate exposed credentials, move to secrets.py, fix degree symbol (completed 2026-07-15)
- [x] **Phase 2: Carousel + Weather** - Two-button carousel navigation and complete Weather view (completed 2026-07-17)
- [x] **Phase 2.1: Fetch Retry** (INSERTED) - Retry every 60s on fetch failure until first success, then revert to 600s (completed 2026-07-18)
- [ ] **Phase 3: Clock View** - NTP-synced clock with timezone offset and per-second updates
- [ ] **Phase 4: System View** - WiFi diagnostics view completing the v1 carousel

## Phase Details

### Phase 1: Secure Foundation

**Goal**: The codebase is safe to push and the temperature renders with a degree symbol
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: SEC-01, SEC-02, SEC-03, WEATHER-01
**Success Criteria** (what must be TRUE):

  1. Running `git status` shows `secrets.py` as untracked (gitignored) and `main.py` no longer contains credential strings
  2. A `secrets.py.example` file is committed showing the expected keys with placeholder values
  3. The OLED displays the temperature as `19°` (with a drawn degree glyph) rather than `19C`
  4. The repo can be pushed to a public remote without leaking WiFi credentials

**Plans:** 3/3 plans complete
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Extract WiFi creds to gitignored secrets.py + committed secrets.py.example + ImportError fallback in main.py (SEC-01, SEC-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Drop the `C` from the temperature format and draw a hollow degree ring inline in _render (WEATHER-01)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Rewrite git history with git-filter-repo to scrub old creds, then force-push all branches (SEC-03)

### Phase 2: Carousel + Weather

**Goal**: Pressing KEY0/KEY1 cycles through all three views; the Weather view is fully functional
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06, WEATHER-02, WEATHER-03, WEATHER-04, WEATHER-05
**Success Criteria** (what must be TRUE):

  1. Pressing KEY1 advances to the next view and the screen redraws within one frame; pressing KEY0 goes back
  2. Pressing KEY0 while on Weather (first view) wraps to System (last view), and vice versa for KEY1 on System
  3. On every boot the device starts on the Weather view; Clock and System stubs are reachable via navigation
  4. Page dots at the bottom of the OLED show which of three positions is active, updating on each button press
  5. The Weather view shows the condition icon, refreshes every 600 s and immediately on view-switch, and displays "no wifi" / "no data" without crashing when the fetch fails

**Plans:** 3 plans
Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Extract Weather rendering into weather_view.py (behavior-preserving refactor). WEATHER-02.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Stub view modules + carousel dispatch + IRQ handlers + software debounce + poll scheduler + page-dot indicator. NAV-01..06.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — 600s Weather scheduler cadence + boot "connecting..." / spinner sequence + WEATHER-05 error-state confirmation. WEATHER-03, WEATHER-04, WEATHER-05.

**UI hint**: yes

### Phase 2.1: Fetch Retry (INSERTED)

**Goal**: The device recovers from fetch failures on a 60-second cadence until the first success, then reverts to the 600-second default cadence
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: WEATHER-09
**Success Criteria** (what must be TRUE):

  1. When a boot-time or scheduled weather fetch fails ("no wifi" or "no data"), the next refresh attempt fires ~60 s later — not the default 600 s
  2. As soon as one fetch succeeds after a failure run, the next refresh reverts to the 600-second default cadence (does NOT stay stuck at 60 s)
  3. The 60-second retry window does not miss button presses (poll loop remains responsive; presses queue via IRQ and dispatch after refresh returns)

**Plans:** 1 plan
Plans:
**Wave 1**

- [x] 02.1-02-PLAN.md — Add _RETRY_MS = 60_000 and cadence-aware should_refresh predicate (600s when _cache_status == "ok", else 60s). WEATHER-09.

**Note**: The original Wave 1 plan (`02.1-01-PLAN.md` — location label) was reverted in commit `b8823ab` after a layout regression; WEATHER-08 was dropped and Phase 2.1 was narrowed to retry-only. The `02.1-02` filename is retained (not renumbered) so git history for the plan-check work stays linkable.

**UI hint**: no

### Phase 3: Clock View

**Goal**: The Clock view shows live NTP-synced time and handles the WiFi-absent case gracefully
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CLOCK-01, CLOCK-02, CLOCK-03, CLOCK-04, CLOCK-05
**Success Criteria** (what must be TRUE):

  1. Navigating to the Clock view shows the current time adjusted by the hardcoded timezone offset, updating every second while the view is active
  2. After boot the device performs an NTP sync and re-syncs on a background cadence without blocking navigation
  3. When NTP has never succeeded (e.g. no WiFi at boot), the Clock view shows `--:--` instead of a wrong or blank time

**Plans:** 1 plan
Plans:
**Wave 1**

- [ ] 03-01-PLAN.md — Replace clock_view.py stub with full NTP-synced HH:MM clock: two pure predicates (should_tick, should_sync) + sync + render + single bool `_synced` state. Add TZ_OFFSET config + boot sync + two poll-loop branches to main.py. CLOCK-01..05.

**UI hint**: yes

### Phase 4: System View

**Goal**: The System view displays live WiFi diagnostics and remains usable when the device is offline
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: SYSTEM-01, SYSTEM-02, SYSTEM-03, SYSTEM-04
**Success Criteria** (what must be TRUE):

  1. Navigating to the System view shows the connected SSID, the device IP address, and WiFi signal strength (dBm or bar representation)
  2. When WiFi is disconnected, the System view shows a clear "disconnected" state for each field rather than blank or stale values
  3. The System view refreshes its data each time it is navigated to

**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Secure Foundation | 3/3 | Complete    | 2026-07-15 |
| 2. Carousel + Weather | 3/3 | Complete    | 2026-07-17 |
| 2.1. Fetch Retry (INSERTED) | 1/1 | Complete    | 2026-07-18 |
| 3. Clock View | 0/1 | Planned | - |
| 4. System View | 0/TBD | Not started | - |
