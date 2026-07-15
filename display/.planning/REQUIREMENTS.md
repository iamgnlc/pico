# Requirements: Pico OLED Multi-View

**Defined:** 2026-07-15
**Core Value:** Pressing a button changes the view instantly and reliably; each view stays accurate on its own refresh cadence without user intervention.

## v1 Requirements

### Security

- [x] **SEC-01**: WiFi credentials live in a gitignored `secrets.py` — not in `main.py`
- [x] **SEC-02**: A committed `secrets.py.example` documents the expected keys without leaking values
- [x] **SEC-03**: The currently-exposed WiFi credentials (`main.py:9-10`) are rotated before shipping v1

### Navigation

- [ ] **NAV-01**: KEY0 (GP15) advances to the previous view; KEY1 (GP17) advances to the next view
- [ ] **NAV-02**: Button presses are debounced so a single physical press produces exactly one view change
- [ ] **NAV-03**: The carousel wraps at both ends (previous from the first view goes to the last, and vice versa)
- [ ] **NAV-04**: The device boots to the Weather view on every startup (no persistence)
- [ ] **NAV-05**: A page-dot indicator on the OLED shows the current position in the carousel
- [ ] **NAV-06**: A view switch triggers an immediate redraw (no visible lag between press and screen update)

### Weather View

- [x] **WEATHER-01**: The Weather view shows the current temperature with a degree symbol (e.g. `19°`) instead of `19C`
- [ ] **WEATHER-02**: The Weather view shows the current condition icon for the fetched Open-Meteo weather code
- [ ] **WEATHER-03**: The Weather view auto-refreshes every 600 seconds
- [ ] **WEATHER-04**: The Weather view refreshes immediately when navigated to (in addition to the periodic cadence)
- [ ] **WEATHER-05**: The Weather view shows a clear error state ("no wifi" / "no data") when the fetch fails, without crashing or blocking the carousel

### Clock View

- [ ] **CLOCK-01**: The Clock view shows the current time synced via NTP over WiFi
- [ ] **CLOCK-02**: The clock applies a single hardcoded timezone offset (configured at the top of `main.py`)
- [ ] **CLOCK-03**: The Clock view updates every second while displayed
- [ ] **CLOCK-04**: The Clock view re-syncs NTP on a reasonable cadence (once at boot + periodically)
- [ ] **CLOCK-05**: The Clock view shows a clear error state when NTP has never succeeded (e.g. `--:--`)

### System View

- [ ] **SYSTEM-01**: The System view displays the connected WiFi SSID
- [ ] **SYSTEM-02**: The System view displays the device's IP address
- [ ] **SYSTEM-03**: The System view displays WiFi signal strength (dBm or bars)
- [ ] **SYSTEM-04**: The System view remains functional when WiFi is disconnected — it shows the disconnected state clearly

## v2 Requirements

<!-- Deferred to future release. Tracked but not in current roadmap. -->

### Weather

- **WEATHER-06**: Multi-day / hourly forecast view
- **WEATHER-07**: User-configurable location override (skip ip-api geolocation)

### Clock

- **CLOCK-06**: User-configurable timezone with DST rules
- **CLOCK-07**: Alarm / stopwatch functionality

### Navigation

- **NAV-07**: Long-press semantics (e.g. hold-to-refresh, hold-to-open-settings)
- **NAV-08**: Persistence of last-viewed screen across reboots

## Out of Scope

<!-- Explicitly excluded. Documented to prevent scope creep. -->

| Feature | Reason |
|---------|--------|
| Menu- or list-style navigation | Two-button hardware makes a linear carousel the natural fit |
| Hardware RTC / offline clock | Clock intentionally depends on NTP; adds cost and complexity for a WiFi-first device |
| Per-view button actions beyond prev/next | Keeps navigation predictable across all views in v1 |
| Additional views (calendar, notifications, sensors) | v1 is Weather + Clock + System only |
| Host-side tests | Per `CLAUDE.md`: everything runs on-device |
| User-configurable API keys | Weather uses free/keyless APIs (ip-api, Open-Meteo); nothing to configure |
| Touchscreen or joystick support | Waveshare Pico-OLED-1.3 HAT has neither; only the two side buttons |

## Traceability

<!-- Which phases cover which requirements. Populated during roadmap creation. -->

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEC-01 | Phase 1 | Complete |
| SEC-02 | Phase 1 | Complete |
| SEC-03 | Phase 1 | Complete |
| NAV-01 | Phase 2 | Pending |
| NAV-02 | Phase 2 | Pending |
| NAV-03 | Phase 2 | Pending |
| NAV-04 | Phase 2 | Pending |
| NAV-05 | Phase 2 | Pending |
| NAV-06 | Phase 2 | Pending |
| WEATHER-01 | Phase 1 | Complete |
| WEATHER-02 | Phase 2 | Pending |
| WEATHER-03 | Phase 2 | Pending |
| WEATHER-04 | Phase 2 | Pending |
| WEATHER-05 | Phase 2 | Pending |
| CLOCK-01 | Phase 3 | Pending |
| CLOCK-02 | Phase 3 | Pending |
| CLOCK-03 | Phase 3 | Pending |
| CLOCK-04 | Phase 3 | Pending |
| CLOCK-05 | Phase 3 | Pending |
| SYSTEM-01 | Phase 4 | Pending |
| SYSTEM-02 | Phase 4 | Pending |
| SYSTEM-03 | Phase 4 | Pending |
| SYSTEM-04 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-15*
*Last updated: 2026-07-15 after roadmap creation — all 23 requirements mapped*
