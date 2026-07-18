# Phase 4: System View - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning
**Type:** Final v1 phase.

<domain>
## Phase Boundary

Replace the current `system_view.py` stub with a working diagnostics view:

- Displays connected SSID, WAN IP (public/internet-facing), and WiFi signal strength (as drawn bars).
- Refreshes its data only on view-switch (SC#3). No periodic polling.
- Shows `--` for every field when WiFi is disconnected — uniform, unambiguous offline UX.
- System view is READ-ONLY — never triggers WiFi reconnect attempts. Relies entirely on `weather_view.refresh`'s existing 1-min retry (offline) or 10-min normal cadence.

**Covers:** SYSTEM-01, SYSTEM-02, SYSTEM-03, SYSTEM-04 (4 requirements)

**IP semantic clarification (from user during discuss-phase):** SYSTEM-02's "device's IP address" is interpreted as **WAN IP** (public, internet-facing address as seen by ip-api's server), NOT the local RFC1918 device IP from `wlan.ifconfig()[0]`. This requires piggybacking on the existing ip-api weather round-trip. See D-43.

**Not in this phase:**

- No changes to the SH1107 driver, `wifi.py`, `clock_view.py`, `icons.py`, `text_render.py`, `secrets.py`.
- No new APIs — WAN IP comes for free from the existing ip-api call.
- No manual reconnect action (long-press semantics deferred to v2 per Out-of-Scope list).
- No dBm text on the panel — signal is bars-only per D-42.
- No last-known-SSID display when offline (uniform `--` per D-44).

</domain>

<decisions>
## Implementation Decisions

### Data refresh strategy (D-41)
- **D-41:** `system_view.render(oled)` queries `network.WLAN(network.STA_IF)` primitives INLINE (no cached data, no `should_tick` predicate). Called by `main.py`'s existing carousel branch on every view-switch (SC#3 satisfied literally). No new poll-loop branch. The only cached module state is `_cached_wan_ip` (see D-43), populated asynchronously by `weather_view.refresh`. All `network.WLAN` reads (`isconnected()`, `config('essid')`, `status('rssi')`, `ifconfig()`) are RAM/driver-only — no radio round-trip, no blocking.

### Signal-strength representation (D-42)
- **D-42:** Signal strength renders as 4 vertical bar rectangles, filled = active, hollow = inactive, based on RSSI thresholds:
  - `>= -55 dBm` → 4 bars (strong)
  - `-55 to -65` → 3 bars (good)
  - `-65 to -75` → 2 bars (fair)
  - `< -75` → 1 bar (weak)
  - Offline OR RSSI unavailable → 0 bars (all hollow)
- Bars geometry (planner discretion, following the project's page-dot idiom): each bar ~4 px wide × 6 px tall, 2 px gap between bars, starting immediately after the "Signal " label at y=40. Use `oled.fill_rect()` for filled bars, `oled.rect()` for hollow.
- NO dBm text on the panel — bars-only. If the user wants the exact number for troubleshooting, they can drop into REPL and call `network.WLAN(network.STA_IF).status('rssi')`.

### Layout (D-43)
- **D-43:** 3-line vertical list at scale 1, with bars inline on the signal line:
  - **y = 8:** SSID string, left-aligned at x=0. Truncated to `min(15, WIDTH // 8)` chars with NO ellipsis (same pattern as the reverted 02.1-01's location label). SSIDs longer than 15 chars are sliced; the operator recognises their own network from a prefix.
  - **y = 24:** WAN IP string, left-aligned at x=0. IPv4 addresses fit comfortably (`255.255.255.255` = 15 chars max).
  - **y = 40:** `"Signal "` label (7 chars = 56 px at scale 1), then 4 drawn bars starting at x=56, running to x≈80. Bar spacing per D-42.
- All content stays inside rows 0–53 (Phase 2 D-19 constraint). Page dots continue to draw at y=60 via `main.py`'s post-render pass.
- **`_center_text` NOT used** — SSID/IP are left-aligned for a diagnostic-view feel (contrasts with Weather/Clock's centered typography).

### WAN IP source + cache (D-43-bis)
- **IP field shows WAN IP (public), not local device IP.** Sourced from ip-api's `query` field, piggybacked on the existing ip-api weather call. `weather.current()` extends from 4-tuple to 5-tuple: `(temp, code, is_day, tz_offset, wan_ip)`.
- **URL update:** `http://ip-api.com/json/?fields=lat,lon,offset` becomes `http://ip-api.com/json/?fields=lat,lon,offset,query`. `query` is the field name for the client's IP as seen by ip-api. (Reminder from `.planning/.continue-here.md` anti-pattern: ip-api's default fields omit both `offset` and `query` — must be requested explicitly.)
- **Cache:** module state `_cached_wan_ip = None` in `system_view.py`. Public setter `set_wan_ip(ip)` — direct mirror of `clock_view.set_tz_offset(offset)`:
  - Returns early if `ip is None`
  - Returns early if `ip == _cached_wan_ip` (idempotent — no unnecessary state churn)
  - Otherwise, updates `_cached_wan_ip`
- **NOT persisted to flash** — unlike tz_offset (rarely changes; worth persisting), WAN IP is volatile (DHCP renewal, network changes) and less useful across boots. RAM-only.
- **Fresh-boot state:** `_cached_wan_ip = None` until the first successful weather fetch (up to 10 min post-boot). During that window, `system_view.render` shows `--` for the IP field.
- **Offline handling:** if `wlan.isconnected() == False`, the IP field shows `--` even when `_cached_wan_ip` is populated (showing a stale WAN IP while offline is misleading). See D-44.

### Offline UX (D-44)
- **D-44:** When `network.WLAN(network.STA_IF).isconnected() == False`, all three fields render as `--`:
  - SSID: `SSID: --`
  - IP: `IP: --`
  - Signal: all 4 bars hollow (0 bars active)
- Uniform, unambiguous. Does NOT show last-known SSID with `(offline)` marker (option (b) considered but rejected — the extra complexity isn't worth it for a diagnostics view where the user can easily reason "I'm not connected → nothing is valid").
- No centered "offline" text — the 3-line structure stays visually consistent between online and offline states (only the values change).

### Background reconnect responsibility (D-45)
- **D-45:** `system_view.py` is READ-ONLY. It never calls `wifi.connect()`, `wlan.connect()`, or `wlan.active(True)`. Never blocks the poll loop. All state-change work happens elsewhere:
  - Cold-boot connect: `weather_view.refresh(oled)` at boot (existing).
  - Reconnect-after-drop: `weather_view.refresh(oled)`'s 1-min retry when `_cache_status != "ok"` (Phase 2.1 D-31 / WEATHER-09).
  - Normal cadence reconnect (defense-in-depth): every 10 min via the normal `_REFRESH_MS` window.
- Long-press for manual reconnect explicitly OUT of scope for v1 (Out-of-Scope list: "Long-press behavior").

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core Value, Constraints, Key Decisions (specifically "WiFi-required views show error, background reconnect" — Phase 4 satisfies the "shows error" half; the "background reconnect" half is delegated to weather_view).
- `.planning/REQUIREMENTS.md` — SYSTEM-01..04 exact wording + Traceability table. **Note:** SYSTEM-02 says "device's IP address"; this phase interprets that as WAN IP per user clarification during discuss-phase (not local device IP).
- `.planning/ROADMAP.md` §"Phase 4: System View" — Goal + 3 Success Criteria (SSID/IP/signal visible; disconnected state clear; refresh on view-switch).
- `.planning/phases/02-carousel-+-weather/02-CONTEXT.md` — Phase 2 D-13..D-25 (carousel, IRQ, page dots, cache model). Substrate this phase extends; MUST NOT be violated. Note: D-23 (spinner) was retired 2026-07-18.
- `.planning/phases/03-clock-view/03-CONTEXT.md` — Phase 3 D-38 (pure predicates + main.py gates render — same pattern re-used here, though Phase 4 has no `should_tick` predicate since D-41 chose view-switch-only).
- `.planning/phases/02.1-location-label-+-fetch-retry/02.1-CONTEXT.md` — Phase 2.1 D-31 (retry predicate shape — Phase 4 does NOT introduce a new retry predicate; it relies on weather_view's existing one).
- `.planning/.continue-here.md` — Anti-pattern list: "ip-api default fields omit `offset`" — same applies to `query`; must include in the `?fields=` list.

### Hardware and driver constraints (must NOT be violated)
- `CLAUDE.md` §"Non-obvious SH1107 gotchas" — Four hardware traps. `sh1107.py` MUST NOT be modified.
- `.planning/codebase/CONVENTIONS.md` — Naming (snake_case, `_`-prefix privates), `.format()` not f-strings, no type hints, no docstrings — binding.

### MicroPython stdlib references
- `network.WLAN(network.STA_IF)` — the STA (station) mode WLAN interface. Already active after `wifi.connect()` in boot sequence.
  - `.isconnected()` → bool
  - `.config('essid')` → str (SSID of the connected AP)
  - `.status('rssi')` → int (RSSI in dBm, negative)
  - `.ifconfig()` → tuple `(local_ip, netmask, gateway, dns)` — the local IP is `[0]`, NOT used in Phase 4 (WAN IP is what's shown).
- All the above are RAM-only reads on the CYW43 WiFi driver — no radio round-trip, no blocking. Safe to call inline in `render(oled)`.

### Source files this phase will modify
- `weather.py` — Extend the return tuple of `current()` to include `wan_ip` per D-43-bis. Add `query` to the `?fields=` query param. Preserve the broad-exception fallback (5 Nones on failure).
- `weather_view.py` — Update the unpack from 4-tuple to 5-tuple. Add `import system_view` at the top (mirror of the existing `import clock_view` from Plan 03-02). Add `system_view.set_wan_ip(wan_ip)` call after `_cache_status = "ok"` and after the existing `clock_view.set_tz_offset(tz_offset)` call.
- `system_view.py` — Replace the current 2-line stub. New module state (`_cached_wan_ip = None`); new imports (`network`, `text_render`); new `set_wan_ip(ip)` public setter with idempotent guard; full `render(oled)` implementation.

### Source files this phase will NOT modify
- `sh1107.py`, `wifi.py`, `clock_view.py`, `main.py`, `icons.py`, `text_render.py`, `secrets.py`, `.gitignore`. Verifier will `git diff --exit-code` these against the phase-start commit.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`text_render.text(fb, s, x, y, scale, color)`** — the scaled font renderer. Phase 4 uses scale=1 for all text (SSID, IP, signal label).
- **`network.WLAN(network.STA_IF)`** — already active from Phase 2's boot sequence. `wifi.connect()` in `weather_view.refresh` keeps it alive. Phase 4 can read from it without any lifecycle management.
- **`weather.current()` extension pattern** — same shape used twice now (Phase 2.1's location — reverted; Plan 03-02's tz_offset — shipped). Piggyback the WAN IP on the ip-api call by adding it to the `?fields=` list and returning it in the tuple.
- **The `set_tz_offset(offset)` setter pattern in `clock_view.py`** — direct template for `set_wan_ip(ip)` in `system_view.py`. Same idempotent-guard logic, minus the file-persistence.

### Established Patterns
- **Module-level UPPER_SNAKE_CASE constants for tunables** — Phase 4 has no new constants (no cadences, no thresholds beyond the RSSI thresholds embedded in the bar-rendering logic).
- **`.format()` not f-strings** — mandatory. IP format is `"IP: {}".format(wan_ip)`; SSID is `"SSID: {}".format(ssid)`.
- **Cache written by upstream + read by view** — same shape as Plan 03-02's tz_offset flow (weather_view.refresh → clock_view.set_tz_offset → clock_view.render reads). Phase 4 reuses the pattern for WAN IP.

### Integration Points
- **`weather.current()` return contract change** ripples to exactly one caller: `weather_view.refresh(oled)`. Update the unpack to 5 values.
- **`weather_view.refresh` new call site** — `system_view.set_wan_ip(wan_ip)` placed immediately after the existing `clock_view.set_tz_offset(tz_offset)` call, so both view caches update in lockstep on the same successful fetch.
- **`system_view.render` interaction with `network.WLAN`** — read-only. No `active(True)`, no `connect()`, no `disconnect()`. Just query methods. If `network.WLAN(network.STA_IF)` is not active (unusual — would only happen if wifi.connect never ran), the query methods still return default values (e.g. `isconnected() == False`), which the render function handles via the offline-UX branch (D-44).
- **View-switch behavior** — inherits Phase 2 D-22. `main.py`'s existing carousel branch calls `VIEWS[_current_idx].render(oled)` on button press; `system_view.render` reads network state fresh + renders. No changes to `main.py`'s carousel branch.
- **No poll-loop changes** — D-41 explicitly rejects a `should_tick` predicate. `main.py`'s poll loop is byte-identical after Phase 4 (weather branch + clock tick branch + clock sync branch unchanged).

</code_context>

<specifics>
## Specific Ideas

- **User's exact clarification on IP:** "Ip has to be WAN IP not local device IP." Locked as D-43-bis. Sourced from ip-api's `query` field via the existing weather round-trip — no new API call.
- **Signal representation is bars-only** — the operator explicitly picked drawn bars over dBm text or a hybrid. Matches the project's "small drawn glyph" ethos (page dots, degree ring).
- **Layout is left-aligned, not centered** — the diagnostic-view aesthetic (list of key-value pairs) contrasts intentionally with the centered typography of Weather (icon + temp) and Clock (`HH:MM`). Signals visual identity of the view.
- **View-switch-only refresh** — no `should_tick`, no background polling. RSSI changes are visible when the user re-navigates. Aligns with the just-shipped D-35 relaxation (6h NTP) and D-23 retirement (no spinner) — the overall trajectory is "less panel churn, less WiFi churn".
- **System view never talks to the WiFi driver in write mode** — read-only integration. Delegation to `weather_view.refresh` for all reconnect work.

</specifics>

<deferred>
## Deferred Ideas

- **dBm text alongside bars** — considered in D-42 as option (e); rejected for v1. Could be a diagnostic-mode toggle in v2.
- **Last-known SSID displayed with `(offline)` marker when disconnected** — considered in D-44 as option (b); rejected for uniformity. Could revisit if v2 diagnostic mode wants it.
- **Local IP alongside WAN IP** — the local device IP (`wlan.ifconfig()[0]`, e.g. `192.168.1.42`) is not shown in v1. Could be a second line in a v2 diagnostic mode.
- **Manual reconnect action via long-press** — Out-of-Scope per PROJECT.md ("Long-press behavior" deferred to v2).
- **Timestamp of last successful WAN IP fetch** — could show "last seen: 3m ago" alongside the IP for troubleshooting. Deferred.
- **RSSI change indicator** — visualizing "signal is degrading" over time. Requires per-tick polling (rejected by D-41). Deferred.
- **Network diagnostics beyond WiFi** — gateway ping, DNS test, uptime. Out of scope for a small OLED status view.

</deferred>

---

*Phase: 4-System View*
*Context gathered: 2026-07-18*
