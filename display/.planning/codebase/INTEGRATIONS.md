# External Integrations

**Analysis Date:** 2026-07-15

## APIs & External Services

**Weather & Geolocation:**
- **IP Geolocation (ip-api.com)** - Locates device by public IP address
  - Endpoint: `http://ip-api.com/json/`
  - Client: `urequests` (MicroPython HTTP)
  - Auth: None (free tier)
  - Response fields used: `lat`, `lon` (`weather.py:6`)

- **Open-Meteo API** - Open-source weather forecast service (no API key required)
  - Endpoint: `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,is_day`
  - Client: `urequests`
  - Auth: None
  - Response fields used: `current.temperature_2m`, `current.weather_code`, `current.is_day` (`weather.py:14`)
  - Weather codes: Integer values mapped to WMO codes; icons map codes to visual conditions (rain/snow/thunder/fog/cloud/sun/moon) (`icons.py:1-14`)

**Error Handling:**
All API calls wrapped in try/except; returns `(None, None, None)` on any failure (`weather.py:17-18`). Display shows "no data" fallback if weather unavailable (`main.py:29-30`).

## Network & Connectivity

**WiFi:**
- **Network Standard:** 802.11 wireless (2.4 GHz band)
- **SSID:** Hardcoded in `main.py:9` (REDACTED_SSID)
- **Connection:** MicroPython `network.WLAN(network.STA_IF)` class (`wifi.py:6`)
- **Auth:** WPA/WPA2 (password passed to `connect()`) (`wifi.py:5`)
- **Timeout:** 20 seconds default; retries connection check every 1 second (`wifi.py:10-13`)
- **DHCP:** Automatic; returns assigned IP via `ifconfig()[0]` (`wifi.py:14`)

**Fallback Behavior:**
If WiFi connection fails or times out, display shows "no wifi" and skips weather fetch (`main.py:24-26`).

## Hardware Peripherals

**SH1107 OLED Display:**
- **Protocol:** SPI (not I2C)
- **Resolution:** 128×64 pixels
- **Connection:** Direct HAT to Pico W header (pinout fixed)
- **Pinout:** 
  - DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12
  - SPI Bus 1
  - Frequency: 20 MHz
- **Control Flow:**
  1. Initialize reset sequence (`sh1107.py:40-42`)
  2. Send init command sequence (`sh1107.py:44-62`)
  3. Framebuffer writes via `text()`, `fill()`, `pixel()`, `ellipse()`, `line()`, etc. (inherited from `framebuf.FrameBuffer`)
  4. `show()` pushes buffer to panel via SPI with per-byte CS toggling (`sh1107.py:78-90`)

**Critical Quirks:**
- CS must toggle around every data byte (not continuous burst) for correct GDDRAM latching (`sh1107.py:84-90`)
- `0x21` addressing command is single-byte only; no argument byte follows (`sh1107.py:50`)
- Rotation handled at pixel level in `show()`, not hardware-based, due to GDDRAM display-offset wrap (`sh1107.py:66-76`)
- Buffer format must be `MONO_HMSB` (`sh1107.py:30`); `MONO_VLSB` scrambles pixel layout

**Pico W Onboard:**
- Dual-core ARM Cortex-M0+ (RP2040)
- WiFi: Broadcom CYW43439 (2.4 GHz 802.11 b/g/n)
- RAM: 264 KB (sufficient for 1024-byte framebuffer + runtime)

## Data Flow

1. **Startup** (`main.py:37-41`):
   - Initialize OLED with `OLED(rotate=ROTATE)` → SPI setup + panel init sequence
   - Enter refresh loop every `REFRESH_SECONDS`

2. **Per-Refresh Cycle** (`main.py:22-34`):
   - Clear framebuffer: `oled.fill(0)`
   - WiFi connect: calls `wifi.connect(SSID, PASSWORD)` → returns IP or None
   - If no WiFi: show "no wifi" text and `show()` to panel
   - If WiFi: fetch weather:
     - Query ip-api.com for geolocation (lat, lon)
     - Query Open-Meteo with coordinates
     - Extract temperature, weather_code, is_day
   - If no data: show "no data" text
   - If data: draw weather icon (`icons.draw()`) and temperature text (`text_render.text()`)
   - Render to panel: `oled.show()` → copies framebuffer to SPI → SH1107 GDDRAM

3. **State Management:**
   - No persistent state; WiFi connection is per-cycle (connects fresh each refresh)
   - Framebuffer is the only mutable shared state (inherited from `framebuf.FrameBuffer`)
   - Display rotation applied per `show()` if enabled

## Environment Configuration

**Required Credentials (Hardcoded in main.py):**
- WiFi SSID: `REDACTED_SSID` (`main.py:9`)
- WiFi password: `REDACTED_PASSWORD` (`main.py:10`) — **⚠️ WARNING: Credentials in source code** (no .env support in MicroPython)

**Configuration Knobs (main.py:8-12):**
- `WIFI_SSID` - Change to your network name
- `WIFI_PASSWORD` - Change to your network password
- `REFRESH_SECONDS` - Adjust update frequency (default 600s = 10 min)
- `ROTATE` - Set `True` to flip display 180°

**Secrets Location:**
No .env or secrets management; credentials must be edited directly in `main.py` before deployment. No environment variable support in MicroPython on Pico.

## Bandwidth & Latency Expectations

- **Geolocation Query:** ~100 bytes response (ip-api.com)
- **Weather Query:** ~300 bytes response (Open-Meteo)
- **Total per refresh:** ~400 bytes + overhead
- **Refresh interval:** 10 min default (600 sec)
- **Network data usage:** ~0.24 MB/hour

---

*Integration audit: 2026-07-15*
