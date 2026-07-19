# Codebase Concerns

**Analysis Date:** 2026-07-19

## SH1107 Driver Gotchas

**Hardware Protocol Fragility:**

The SH1107 controller has four non-obvious protocol constraints that are load-bearing in `sh1107.py`. Violating any of them silently breaks the display without error messages.

### Gotcha 1: `0x21` Command is Single-Byte, Not Command+Argument

**What happens:** `sh1107.py:50` sends `0x21` (memory addressing mode: vertical) without an argument byte that follows. The init sequence groups single-byte commands separately from command+argument pairs.

**Why fragile:** Many SPI display protocols use command+argument pairs consistently (e.g., `0x20 0x21` → "enable vertical mode"). On SH1107, sending `0x21` followed by any data byte will interpret that data byte as the next command, silently breaking the addressing mode for all subsequent column/page commands.

**Risk:** If someone refactors the init loop to add a trailing argument or inserts a new command+arg pair after `0x21`, the display will go blank or show scrambled pixels with no exception thrown.

**Files:** `sh1107.py:50`

**Mitigation:** Comment at line 50 notes this is a "single-byte cmd". CLAUDE.md documents it in the "Non-obvious SH1107 gotchas" section.

---

### Gotcha 2: CS (Chip Select) Must Toggle Per Byte in `show()`

**What happens:** `sh1107.py:86-90` writes the 16-byte column to GDDRAM with CS toggled around each individual byte, not once per column (which is typical SPI protocol).

**Why fragile:** Standard SPI convention is to hold CS low for the entire transaction (all 16 bytes), then raise it once. On this panel, a continuous CS-low burst does not latch the bytes correctly into GDDRAM; the register pointer drifts and the display shows corrupted content in later columns.

**Risk:** Optimization attempts to "fix" the inefficient per-byte CS toggle will break the driver. Waveshare's reference implementation (`Pico-OLED-1.3(spi).py`) does the same per-byte toggle, confirming this is required by the hardware.

**Files:** `sh1107.py:83-90`

**Mitigation:** Inline comment at line 83-84 explains the behavior and its necessity.

---

### Gotcha 3: Rotation Must Use Pixel-Level Reads/Writes, Not Buffer-Byte Shuffling

**What happens:** `sh1107.py:66-76` implements 180° rotation by reading each pixel from the original buffer, then writing it to flipped coordinates in a temporary buffer. The original buffer is discarded and the rotated buffer is sent to the panel.

**Why fragile:** The SH1107 has a display-offset of `0x60` (96) set at init (`sh1107.py:56`). This creates a wrap in the visible GDDRAM region: physical rows 0–31 display GDDRAM bytes 96–127, and physical rows 32–63 display GDDRAM bytes 0–31. Because of this non-linear mapping, byte-level transforms (e.g., reverse all bytes, reverse bits within each byte) will move active pixels into the invisible half of the GDDRAM buffer, causing the screen to go blank or show only the lower half of the image. Hardware-based rotation (setting `0xA1` segment remap + `0xC8` COM scan) also fails because it fights the display-offset wrap.

**Risk:** Any attempt to optimize rotation by shuffling buffer bytes instead of using `framebuf.pixel()` will silently corrupt the display.

**Files:** `sh1107.py:66-76` (rotation implementation), `sh1107.py:56` (display offset `0x60`)

**Mitigation:** CLAUDE.md includes detailed explanation of the GDDRAM wrap and why byte-shuffling fails.

---

### Gotcha 4: Framebuffer Format Must Be `MONO_HMSB`

**What happens:** `sh1107.py:30` subclasses `framebuf.FrameBuffer` with format `MONO_HMSB` (horizontal byte packing, MSB first). This matches the SH1107's byte layout.

**Why fragile:** The `show()` method walks the buffer as 128-wide rows of 16 bytes. If the format is changed to `MONO_VLSB` (vertical byte packing, LSB first), the bit layout scrambles—pixels shift vertically within bytes, and the display shows garbled content.

**Risk:** Attempting to use `MONO_VLSB` for any reason (e.g., perceived memory optimization) will break the driver without a clear cause.

**Files:** `sh1107.py:30`

**Mitigation:** Format is specified at object construction; changing it requires modifying the class. No comment explicitly warns about `MONO_VLSB`, but the format matches Waveshare's reference.

---

## IP-API Extended Fields Risk

**Issue:** The `?fields=lat,lon,offset,query` parameter in `bootstrap.py:40` is critical and was added to fix a silent failure.

**What can go wrong:** If the `?fields=` query parameter is removed or the field list is incomplete (e.g., missing `offset` or `query`), the ip-api endpoint returns default fields only. The `offset` and `query` fields come back as `None`, causing downstream setters in `main._refresh_all()` to no-op (see `clock_view.set_tz_offset()` and `system_view.set_wan_ip()`). The clock will display `--:--` forever, and the system view will show `IP: --` even though WiFi is connected.

**Files:** `bootstrap.py:40` (the query string), `clock_view.py:39-42` (offset setter guards on None), `system_view.py:36-39` (IP setter guards on None)

**History:** Plan 03-02 shipped without the `?fields=` parameter. The clock stayed at `--:--` forever in that iteration because `ip-api` was returning `"offset": null` silently.

**Current state:** The `?fields=` parameter is present and correct as of 2026-07-19.

**Mitigation:** Add a test or assertion that verifies ip-api returns non-None `offset` and `query` fields on first successful boot, before relying on them in downstream logic.

---

## Memory and Heap Fragmentation

**Issue:** Framebuffer rotation allocates a temporary 1024-byte buffer on every call to `show()` when `ROTATE=True`.

**What happens:** `sh1107.py:67` creates `rot_buf = bytearray(len(self.buffer))` on every frame. With default settings (full screen refresh every tick, ~100ms poll cadence), this is ~10 allocations per second, each of 1024 bytes.

**Risk to this codebase:** The Pico W has ~264 KB SRAM. The rotation buffer + original buffer = 2 KB per frame; MicroPython's heap fragmentation from repeated alloc/free cycles could eventually prevent future feature additions (e.g., caching weather icons, larger text buffers).

**Frequency:** Only in frames where `ROTATE=True`. With `ROTATE=False` (the default in main.py is `ROTATE=True`; see line 10), this happens every frame.

**Files:** `sh1107.py:67`, `main.py:10` (ROTATE = True)

**Mitigation:** Not urgent for current scope. If fragmentation becomes an issue, pre-allocate `rot_buf` as an instance variable in `__init__` and reuse it.

---

## Boot WiFi Timeout is Blocking

**Issue:** The initial `bootstrap.fetch()` call at `main.py:108` is blocking and can take up to 20 seconds if WiFi is unavailable or slow to connect.

**What happens:** On cold boot, `_wifi_connect()` at `bootstrap.py:6-15` iterates up to 20 times with 1-second sleeps, for a total of 20 seconds. During this time, the UI shows "connecting..." and button presses are still captured (IRQ handlers fire), but the main loop is blocked.

**Risk:** Users pressing buttons during the 20s boot window see no response until the fetch completes. If WiFi is down, they wait 20 seconds to see "no wifi".

**Files:** `bootstrap.py:6-15` (timeout=20), `main.py:108` (blocking fetch call)

**Mitigation:** The comment at `main.py:97-103` acknowledges this and pre-renders "connecting..." before the fetch. The IRQ handlers capture button presses during the wait, which are dispatched immediately after the fetch returns (see `main.py:118-123`). This is a known trade-off; MicroPython has no async/await on embedded devices, so a timeout-agnostic approach would require event-driven WiFi driver integration (out of scope for current architecture).

---

## NTP Sync Retry Cadence

**Issue:** Clock syncing has a 60-second retry cadence until first success, then 6-hour re-sync cadence.

**What happens:** `clock_view.py:12-13` defines `_SYNC_MS = 21_600_000` (6h) and `_RETRY_MS = 60_000` (60s). If NTP fails on boot (e.g., no network yet), the clock shows `--:--`. The render loop at `main.py:136-137` calls `clock_view.should_sync()` and `clock_view.sync()`, retrying every 60 seconds until NTP succeeds once.

**Risk to experience:** 60-second retry means up to 1 minute of `--:--` on the clock after WiFi comes up, if the initial NTP call fails.

**Files:** `clock_view.py:12-13, 59-61, 64-73`, `main.py:136-137`

**Mitigation:** The retry cadence is intentional (D-36) to avoid tight-loop scheduler blocking. First sync typically succeeds within 1–2 attempts. The 6-hour re-sync window (D-35, updated 2026-07-18) avoids constant NTP queries and clock drift from local timekeeping.

---

## Weather Retry Cadence

**Issue:** Weather data has a 60-second fast-retry cadence when cache is not "ok", and 10-minute normal refresh when cache is "ok".

**What happens:** `weather_view.py:12-13` defines `_REFRESH_MS = 600_000` (10 min) and `_RETRY_MS = 60_000` (60s). If a weather fetch fails (WiFi down, API error), the next attempt is in 60 seconds. If it succeeds, the next refresh is in 10 minutes.

**Risk:** A persistent API outage (e.g., open-meteo down) will retry every 60 seconds. With multiple retries failing, this may accumulate network requests if the device is online but the API is not.

**Mitigation:** The current behavior is intentional (WEATHER-09, documented in code). The `should_refresh()` logic at `weather_view.py:23-25` ensures failed fetches consume one retry window before trying again, preventing tight-looping. The `_cache_status` in `set_data()` at `weather_view.py:47-63` handles the distinction between WiFi failure ("no_wifi") and API failure ("no_data"), allowing the UI to display different messages.

---

## Timezone Offset File Persistence

**Issue:** `clock_view.py` persists timezone offset to `tz_offset.txt` on every weather fetch that returns a new offset.

**What happens:** `clock_view.py:33-48` calls `set_tz_offset()` after each successful weather fetch. A flash wear-guard (line 41) only writes if the offset changes. For a stationary device with no DST transition, the file is written once on first boot and never again.

**Risk:** If a device moves to a different timezone and the user doesn't update the offset manually, the clock will show the old timezone until the next weather fetch updates it. No UI mechanism exists to manually override the timezone offset.

**Files:** `clock_view.py:14, 33-48`

**Mitigation:** The wear-guard preserves flash longevity. Manual offset override is out of scope for current phase (no UI for it). The pattern matches D-43-bis (RAM-only storage for WAN IP, file-only for TZ offset).

---

## HTTP vs HTTPS Mixed Transport

**Issue:** `bootstrap.py` uses HTTP for ip-api and HTTPS for open-meteo.

**What happens:** `bootstrap.py:40` queries `http://ip-api.com/json/?fields=...` (unencrypted), and line 45-48 queries `https://api.open-meteo.com/v1/forecast` (encrypted). The WAN IP and timezone are transmitted in plaintext; weather data is encrypted.

**Security posture:** This is not a vulnerability for the application's use case (weather and location are non-sensitive), but it reflects the available APIs. Both ip-api and open-meteo offer free tiers with HTTP and HTTPS endpoints, respectively. There is no token/auth mechanism for either service; the calls are anonymous.

**Files:** `bootstrap.py:40, 45-48`

**Mitigation:** Intended as-is. Switching to HTTPS for ip-api would incur extra bandwidth/latency for IP lookup; the cost/benefit doesn't justify it. No user PII is transmitted except the WAN IP address (which is inherent to any geolocation API call).

---

## Secrets File Management

**Issue:** `secrets.py` contains WiFi credentials and is gitignored.

**What happens:** `/Users/gnlc/Code/pico/.gitignore` (parent directory) ignores `display/secrets.py` and `display/tz_offset.txt`. The `main.py:37-46` entry point checks for ImportError and displays "missing secrets.py" if credentials are absent.

**Risk:** If `secrets.py` is lost (device reset, file deletion), the app halts with a message on the screen and loops forever sleeping (line 45-46).

**Files:** `/Users/gnlc/Code/pico/.gitignore` (parent), `main.py:37-46` (fallback)

**Mitigation:** `secrets.py.example` is committed as a template for new devices. Users must copy it to `secrets.py` and fill in credentials before running. Current state is secure; secrets are not in git history.

---

## Cross-View State Coupling

**Issue:** All view modules maintain module-level state (`_cached_*` globals) that is mutated by `main._refresh_all()`.

**What happens:** `main.py:80-83` calls `set_data()`, `set_tz_offset()`, and `set_wan_ip()` to populate the views after a bootstrap fetch. Each view owns its cache state and render logic independently.

**Risk:** If a new view is added without a corresponding setter in `main._refresh_all()`, it will render with stale/None data until the next fetch. No type signature or assertion enforces that setters are called.

**Files:** `main.py:75-84` (composition root), `views/*.py:set_*()` functions

**Mitigation:** The flat module namespace and simple composition are intentional for MicroPython's constraints (no abstract base classes, no typing). Adding a new view requires updating `main._refresh_all()` manually. This is low-risk for a three-view carousel; scalability is not a design goal.

---

## Phase Directory Naming Drift

**Issue:** The directory `/Users/gnlc/Code/pico/display/Plans/02.1-location-label-+-fetch-retry` no longer describes the phase's actual scope.

**What happens:** The phase was originally designed to add a location label and implement fetch retries. WEATHER-08 (location label) was dropped, narrowing the phase to retry-only. The directory name was not renamed to preserve git blame and commit history.

**Risk:** Low. The phase is archived and not active. Future developers reading the directory structure may be confused about what work was actually done in that phase.

**Files:** `/Users/gnlc/Code/pico/display/Plans/` (directory listing)

**Mitigation:** Documented in project context at startup (this brief). The phase is closed; renaming would obscure git history. No action needed.

---

## CLAUDE.md and Codebase Map Stale Documentation

**Issue:** `CLAUDE.md` and `.planning/codebase/` documentation refer to older module names and structures, even after recent refactors (2026-07-18 and 2026-07-19).

**What happens:** Recent quick tasks moved `weather.py` + `wifi.py` into `bootstrap.py` and moved view modules into `views/` package. Documentation prose was patched for file paths but not rewritten wholesale, so some sections still carry historical language.

**Risk:** Low, but confusing. New developers reading CLAUDE.md may expect separate `weather.py` and `wifi.py` files or views in the root directory.

**Files:** `CLAUDE.md` (Technology Stack, Conventions sections mention old module names), `.planning/codebase/` (if present, similar issue)

**Mitigation:** Not urgent. Path patches are correct; prose is descriptive of what *was* and includes current paths. A full rewrite of narrative sections would help but is not critical for functionality.

---

## Global State Management in Views

**Issue:** All state in view modules is global and mutable, with no encapsulation.

**What happens:** `weather_view.py`, `clock_view.py`, and `system_view.py` each define module-level variables like `_cached_temp`, `_synced`, etc., which are modified by setter functions (`set_data()`, `set_tz_offset()`, etc.). Render functions read these globals.

**Risk:** Potential race condition if button IRQ handlers were to call view functions concurrently. However, MicroPython is single-threaded on Pico W, so actual risk is nil. If true async/await support were added, this would break. Also, testing view logic in isolation requires mocking module globals.

**Files:** `views/*.py` (all three view modules)

**Mitigation:** Single-threaded event loop guarantees no concurrency issues. Module-level globals are idiomatic in MicroPython for embedded/performance-critical code. Testability is limited by MicroPython's design constraints (no native test framework on device). Current approach is acceptable for scope.

---

## Summary

**Critical:** SH1107 driver gotchas (4) — highly load-bearing, well-documented but fragile to unintended changes.

**High:** IP-API field parameter — single point of failure, already caused a bug in earlier phase.

**Medium:** Boot WiFi timeout, NTP retry cadence, memory allocation patterns — all acceptable given MicroPython constraints, documented with mitigation.

**Low:** Documentation drift, global state idiom, missing timezone override UI — known, acceptable for scope, not blocking.

---

*Concerns audit: 2026-07-19*
