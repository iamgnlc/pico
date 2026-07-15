# Codebase Concerns

**Analysis Date:** 2026-07-15

## Fragile Areas: SH1107 Hardware Traps

These four hardware-specific behaviors are documented in `CLAUDE.md` and encoded in the driver. Future modifications to `sh1107.py` must not violate these constraints or the display will silently malfunction.

### 1. Single-Byte Command `0x21`

**What happens:** The SH1107 addressing-mode command `0x21` is a complete, self-contained instruction—not a command+argument pair like most SPI commands.

**Files:** `sh1107.py:50`

**Why fragile:** If a refactor sends an argument byte after `0x21`, that byte will be interpreted as the *next* command and silently corrupt the addressing state. The display will continue responding (no error), but output will be scrambled.

**Do this instead:** When sending `0x21`, send it alone via `_cmd(0x21)`. Never follow it with a data byte.

**Current state:** Correctly implemented at line 50 in the init sequence. The command is sent standalone.

---

### 2. CS Must Toggle Per-Byte in `show()`

**What happens:** In `show()`, the chip-select (CS) line must toggle around *every single data byte* written to GDDRAM, not in one continuous burst across the 16-byte column.

**Files:** `sh1107.py:86-90`

**Why fragile:** This violates typical SPI protocol (CS usually low for the entire transaction). The SH1107 does not latch 16-byte columns correctly when CS stays low continuously. Attempting to optimize by holding CS low across all 16 bytes will cause bytes to drop or corrupt in GDDRAM.

**Do this instead:** Keep the per-byte toggle pattern:
```python
for byte in buf[i * 16:(i + 1) * 16]:
    self.dc(1)
    self.cs(0)
    self.spi.write(bytes([byte]))
    self.cs(1)
```

**Current state:** Correctly implemented. CS toggles for every byte. Verified against Waveshare's reference `write_data()`.

---

### 3. Rotation Must Use Framebuf-Pixel Level, Not Byte Shuffling

**What happens:** The display is initialized with offset `0xD3 0x60` (display offset = 96 bytes), which creates a wrap in the visible GDDRAM region. Physical rows 0–31 show GDDRAM bytes 96–127; rows 32–63 show GDDRAM bytes 0–31. Because of this wrap, the 1024-byte framebuffer does not map linearly to the panel.

**Files:** `sh1107.py:56, 65-75`, `main.py:12`

**Why fragile:** Byte-level or bit-level buffer transforms (reverse + flip) will move active pixels into the invisible half of the GDDRAM and blank the screen. Hardware rotation via segment-remap (`0xA1`) and COM-scan (`0xC8`) commands also breaks because they fight the display-offset wrap.

**Do this instead:** Rotate at the framebuffer-pixel level using `framebuf.pixel()` reads and writes, as implemented in `show()` lines 66–74. This keeps pixel coordinates guaranteed to stay within the displayable region.

**Current state:** Correctly implemented. When `rotate=True`, a temporary framebuffer is created and pixels are read/written individually via `pixel()`. Hardware rotation is disabled.

---

### 4. Framebuffer Format Must Be `MONO_HMSB`

**What happens:** The framebuffer is initialized with `framebuf.MONO_HMSB` (horizontal, most-significant-bit-first). The `show()` method walks the buffer as 128-bit-wide rows of 16 bytes.

**Files:** `sh1107.py:30, 69`

**Why fragile:** Using `MONO_VLSB` (vertical, least-significant-bit-first) will scramble the bit layout because the byte ordering and bit significance differ. Pixels will appear in the wrong positions or not at all.

**Do this instead:** Always use `framebuf.MONO_HMSB`. This matches Waveshare's reference implementation and the `show()` byte-walking logic.

**Current state:** Correctly implemented at initialization and in the rotation buffer.

---

## No Test Coverage

**What's not tested:** None. There are no unit tests, integration tests, or automated test fixtures on-device or host-side.

**Files:** All source files (`sh1107.py`, `main.py`, `wifi.py`, `weather.py`, `icons.py`, `text_render.py`)

**Risk:** Any change to the four SH1107 gotchas above (or to pixel rendering logic) has zero protection. A refactor can silently break the display. The only validation is manual testing on physical hardware.

**Priority:** High

**Safe modification:** Before changing `show()`, rotation logic, or the init sequence, always test on hardware with both `rotate=True` and `rotate=False`. Compare against the Waveshare reference: https://github.com/waveshare/Pico_code/blob/main/Python/Pico-OLED-1.3/Pico-OLED-1.3(spi).py

---

## WiFi Credentials in Source Code

**Problem:** WiFi SSID and password are hardcoded in `main.py:9-10`.

**Files:** `main.py:9-10`

**Exposure risk:** Credentials in source become part of git history. If the repository is ever made public or shared, the network password is exposed.

**Current mitigation:** Repository is private. Credentials are not in a `.env` file, so they cannot be accidentally gitignored and exposed.

**Recommendation:** Before deploying to a shared or public repository, externalize credentials:

1. Move `WIFI_SSID` and `WIFI_PASSWORD` to a `secrets.py` file (not committed; added to `.gitignore`)
2. Import them in `main.py`: `from secrets import WIFI_SSID, WIFI_PASSWORD`
3. Provide a `secrets.example.py` template for setup

---

## No Error Handling for WiFi/API Failures

**Problem:** WiFi and weather API calls can fail silently or with partial results in production, leaving users without feedback on what went wrong.

**Files:** `wifi.py:5-14`, `weather.py:4-18`, `main.py:24-33`

**Current behavior:**

- `wifi.connect()` returns `None` if unable to connect within 20 seconds. `main.py` catches this and displays "no wifi".
- `weather.current()` wraps all network I/O in a try-except that silently swallows exceptions (line 17-18). Returns `(None, None, None)` on any error. `main.py` displays "no data".

**Why it's brittle in the field:**

- No visibility into *why* the API call failed (DNS timeout? HTTP 5xx? Bad JSON response?).
- No retry logic. If `ip-api.com` or `api.open-meteo.com` is temporarily unavailable, users see "no data" forever (or until the next refresh cycle).
- Exception types are discarded, making it impossible to distinguish transient errors (retry) from permanent ones (config).
- Stale display: If one API call times out, the weather icon may not refresh for `REFRESH_SECONDS` (600 seconds = 10 minutes).

**Improvement path:**

1. Add structured error handling in `weather.py`:
   - Distinguish network timeouts (retry) from parsing errors (skip).
   - Return a status tuple: `(temp, code, is_day, error_reason)` where `error_reason` is a string like `"timeout"`, `"no_connection"`, or `"api_error"`.
   - Log (via `print()`) the error for debugging.

2. Implement retry logic in `main.py`:
   - On transient errors, retry after a shorter interval (10–30 seconds) before the next full refresh.
   - On permanent errors (bad API endpoint), skip retries and wait for the next refresh cycle.

3. Display more informative messages:
   - `"timeout"` instead of generic `"no data"` so users know to wait.

---

## Hardcoded Pinout

**What it is:** The pinout is defined as module-level constants in `sh1107.py:7-11` (DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1).

**Files:** `sh1107.py:7-11`

**Is this a concern?** No. The Waveshare Pico-OLED-1.3 HAT plugs directly onto the Pico W header with a fixed pinout. The HAT user cannot change the pins without removing the HAT and hand-soldering a custom cable (not a user-supported workflow). Hardcoding is the correct choice.

**Current state:** Correct as-is.

---

## API Response Parsing

**Problem:** Weather data parsing in `weather.py:14-16` assumes specific JSON structure without validation.

**Files:** `weather.py:14-16`

**Risk:** If `api.open-meteo.com` changes response format, `cur["temperature_2m"]`, `cur["weather_code"]`, or `cur["is_day"]` may raise `KeyError` (caught by the broad `except Exception` on line 17, but user sees "no data" without knowing why).

**Safe modification:** Use `.get()` with defaults:
```python
temp = cur.get("temperature_2m")
code = cur.get("weather_code")
is_day = cur.get("is_day")
if temp is None or code is None or is_day is None:
    return None, None, None
```

This makes the intent explicit: if any field is missing, bail out (rather than relying on exception handling).

---

## Battery/Power Monitoring

**Problem:** The device has no battery status monitoring or power-down logic for battery-powered operation.

**Files:** `main.py:37-41`, `sh1107.py:92-96`

**Current state:** The main loop runs forever, refreshing weather every 600 seconds. If battery-powered, the device will drain the battery in hours without user intervention.

**Recommendation:** If intended for battery deployment:

1. Add a battery-voltage ADC read (GPIO27 on Pico W) and display voltage or battery percentage.
2. Implement a `poweroff()` mode that disables WiFi and dims/turns off the display after a timeout.
3. Add a wake-up mechanism (GPIO interrupt on a button) to return from sleep.

**Current state:** Not a concern if powered by USB or a 5V supply. Not required for development, but critical for field deployment.

---

## Missing Network Diagnostics

**Problem:** There is no way to debug network issues on the device without serial output.

**Files:** `wifi.py`, `weather.py`

**Current behavior:** Both modules return `None` on failure, with no logged message to serial. Debugging requires attaching a serial console and waiting for the next `_render()` call.

**Recommendation:** Add debug output to `wifi.py` and `weather.py`:
```python
# wifi.py
if not wlan.isconnected():
    print("WiFi connection timeout after {}s".format(timeout))
```

This helps diagnose network issues in the field when users don't have a serial connection.

---

## Dependency on External APIs

**Problem:** Weather data is fetched from two external services: `ip-api.com` (geo) and `api.open-meteo.com` (weather).

**Files:** `weather.py:6, 9`

**Risk:**
- If either service is down, the device displays "no data" with no fallback.
- Both services are free-tier, which may have rate limits or occasional downtime.
- `ip-api.com` has a 45-request/minute rate limit on free tier. If `REFRESH_SECONDS=600`, that's 1 request per 10 min = ~144/day, safely under the limit.

**Mitigation in place:** Broad exception handling prevents crashes if APIs are down.

**Future improvement:** Implement response caching so if both API calls fail, display the last successful data (with an age indicator like "2 hrs old") instead of "no data".

---

*Concerns audit: 2026-07-15*
