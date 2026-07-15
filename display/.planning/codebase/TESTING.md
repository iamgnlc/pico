# Testing Patterns

**Analysis Date:** 2026-07-15

## Test Framework

**Status:** No automated test framework

This is a **MicroPython embedded project**. Per `CLAUDE.md`:
> Everything runs on-device; there are no host-side tests to run.

Testing is **manual and on-device only**. The Pico W executes the code in real-time with a live display and live Wi-Fi/weather API calls.

## Test Execution

**Setup:**

1. **Via `mpremote` (recommended):**
   ```bash
   mpremote cp sh1107.py main.py weather.py wifi.py icons.py text_render.py :
   mpremote run main.py
   ```

2. **Via Thonny IDE:**
   - Open files in Thonny with Pico W selected
   - Press Run to execute `main.py`
   - Monitor REPL output for exceptions

**Manual Testing Workflow:**

1. **Copy source files to Pico** using mpremote or Thonny
2. **Run `main.py`** — entry point is the `if __name__ == "__main__":` block at the end
3. **Observe display** — Pico-OLED-1.3 should show either:
   - Weather icon (sun/moon/cloud/rain/snow/thunder/fog) at (16,16)
   - Temperature in Celsius at (88,32)
   - "no wifi" fallback if Wi-Fi fails
   - "no data" fallback if weather API fails
4. **Monitor REPL** for exception tracebacks (reachable via Thonny or `mpremote repl`)

## Test Coverage Strategy

**What gets tested (manual on-device):**

1. **Driver correctness:** Does SPI initialization, register sequence, and framebuffer display work?
   - Verified by: Comparing against Waveshare's official reference script (see CLAUDE.md)
   - Reference: `https://github.com/waveshare/Pico_code/blob/main/Python/Pico-OLED-1.3/Pico-OLED-1.3(spi).py`
   - Test method: Drop Waveshare script onto Pico, observe if display works; if yes, driver is correct

2. **Hardware integration:** Do pins, SPI bus, and reset timing work with the HAT?
   - Verified by: Display responds to `show()` calls without corruption
   - Test method: Visual inspection of rendered pixels

3. **Weather integration:** Does the API call succeed and return valid data?
   - Verified by: Icons render and temperature displays
   - Test method: Watch display refresh every 600 seconds (REFRESH_SECONDS)
   - Fallback text "no data" indicates API failure

4. **Wi-Fi connectivity:** Does `wifi.connect()` establish a connection?
   - Verified by: Weather display appears (depends on successful connection)
   - Test method: Visual inspection; "no wifi" fallback indicates connection failure

**What does NOT get tested:**

- Unit tests for individual functions (not practical on MicroPython)
- Mock network calls (would require mocking `urequests` and `network`, which adds complexity; not worth it for a single-purpose display app)
- Rotation logic (manual: set `ROTATE=True` in `main.py`, observe 180° flip)
- Icon rendering (manual: change weather code or time-of-day to see different icons)
- Text centering (manual: visual inspection of text position)

## Integration Points

**Wi-Fi Module (`wifi.py`):**
- Uses MicroPython's built-in `network.WLAN` API
- Test: Does `connect()` return a valid IP string, or `None` on timeout?
- Failure is caught in `main.py:_render()` with "no wifi" fallback

**Weather API (`weather.py`):**
- Uses `urequests` to call `ip-api.com` and `open-meteo.com`
- Test: Do both requests succeed and return JSON with expected keys?
- Failure is caught with bare `except Exception:` and returns `(None, None, None)`

**Display Driver (`sh1107.py`):**
- Test: Does `show()` correctly push the framebuffer to GDDRAM?
- Reference comparison: Run Waveshare's demo script; if display shows the same output, driver is correct
- Known traps documented in CLAUDE.md (CS toggling, rotation via pixel-level reads, `MONO_HMSB` format, single-byte commands)

**Icon Drawing (`icons.py`):**
- Test: Visual inspection of rendered icons for each weather code
- Failure mode: Dictionary lookup error if weather code maps to unknown icon kind (returns "cloud" as default fallback via `_kind()`)

**Text Rendering (`text_render.py`):**
- Test: Does text appear at correct position and scale?
- Implementation: Creates temporary framebuffer, renders text, then reads pixels and draws scaled versions on target
- Test via: Setting `scale=2` for temperature display (line 33 in main.py) and observing font size

## Common Pitfalls & Debugging

**Blank Display (all pixels off):**
- Most likely: CS pin not toggling correctly in `show()` (documented in CLAUDE.md #2)
- Debug: Compare your `show()` method against Waveshare's reference script
- Check: Are you toggling CS around every byte, not just the column write?

**Scrambled/Corrupted Display:**
- Most likely: Framebuffer format wrong or hardware rotation re-enabled (documented in CLAUDE.md #4)
- Debug: Verify `framebuf.MONO_HMSB` is used, not `MONO_VLSB`
- Check: `show()` implementation matches reference; do not enable segment remap (`0xA1`) or COM scan (`0xC8`)

**Wi-Fi Not Connecting:**
- Debug: Add print statements to `wifi.py` to check `wlan.isconnected()` status
- Check SSID and password in `main.py` match your network
- Verify Pico W firmware is up-to-date

**Weather Data Not Appearing:**
- Debug: Add print statements in `weather.py` to see which API call fails
- Check: Is the Pico connected to Wi-Fi? ("no wifi" message appears instead)
- Check: Are the URLs in `weather.py` correct? (`ip-api.com`, `open-meteo.com`)
- Fallback: "no data" displays if any request fails; check REPL for exception details

**Rotation Inverted (display flipped but wrong direction):**
- Debug: Rotation uses pixel-level reads; if ROI is wrong, active pixels may end up in invisible GDDRAM region
- Check: `show()` logic matches lines 66–73 in `sh1107.py`
- Note: Do NOT use hardware rotation; it is broken due to display offset (documented in CLAUDE.md #3)

## Manual Test Checklist

When modifying driver or display code, verify these on-device:

- [ ] Display powers on (pixels illuminate)
- [ ] Text renders centered at (64, 32)
- [ ] Weather icon renders at (16, 16)
- [ ] Temperature renders at (88, 32) with correct scale
- [ ] "no wifi" appears when connected to wrong SSID
- [ ] "no data" appears when Wi-Fi is on but weather API fails
- [ ] Display refreshes every 600 seconds with updated weather
- [ ] `ROTATE=True` flips display 180°
- [ ] No visual corruption or partial-pixel glitches

## Reference Implementation

For driver validation, always compare against Waveshare's official implementation:

**URL:** `https://github.com/waveshare/Pico_code/blob/main/Python/Pico-OLED-1.3/Pico-OLED-1.3(spi).py`

**How to use:**
1. Download the script
2. Copy to Pico as a standalone test file
3. Run and observe display behavior
4. If Waveshare's script displays correctly and yours does not, the bug is in your implementation
5. Use Waveshare's register sequence and byte-writing logic as the source of truth

---

*Testing analysis: 2026-07-15*
