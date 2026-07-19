# External Integrations

**Analysis Date:** 2026-07-19

## APIs & External Services

**Geolocation:**
- `ip-api.com/json/` - IP-based geolocation to retrieve latitude, longitude, timezone offset, and public WAN IP
  - SDK/Client: `urequests` (MicroPython HTTP library)
  - Auth: None (anonymous, no API key required)
  - Parameters: Explicit `?fields=lat,lon,offset,query` required in URL (`bootstrap.py:40`); default response omits `offset` and `query`
  - Response: JSON object with keys `lat`, `lon`, `offset` (seconds from UTC), `query` (public IP address)
  - Failure handling: Caught in `bootstrap.py:53` bare `except Exception` block; returns `(ip, None, None, None, None, None)` to allow caller to distinguish "WiFi ok but API failed" from "no WiFi"

**Weather:**
- `api.open-meteo.com/v1/forecast` - Weather forecast data (free, no auth)
  - SDK/Client: `urequests` (MicroPython HTTP library)
  - Auth: None (anonymous, no API key required)
  - Parameters: `latitude`, `longitude` (from ip-api), `current=temperature_2m,weather_code,is_day` (`bootstrap.py:45-48`)
  - Response: JSON with nested `current` object containing `temperature_2m` (°C), `weather_code` (WMO code), `is_day` (boolean)
  - Failure handling: Caught in `bootstrap.py:53` bare `except Exception` block; returns partial tuple with temperature set to None
  - WMO code mapping: `icons.py:1-14` maps weather codes to icon types (sun/moon/cloud/fog/thunder/snow/rain)

## Data Storage

**Databases:**
- None — no database backend

**File Storage:**
- Local filesystem only
- `tz_offset.txt` - Single file cache for timezone offset (seconds from UTC); written after first successful ip-api fetch (`clock_view.py:33-48`)
  - Flash wear protection: File only written when offset value changes from cached value (`clock_view.py:41-42`)
  - Persistence: Loaded at module import time (`clock_view.py:20-24`); subsequent boots have good offset before first weather fetch completes

**Caching:**
- `weather_view.py:7-10` - Three module-level cache variables: `_cached_temp`, `_cached_code`, `_cached_is_day`, plus `_cache_status` flag (states: "pending", "ok", "no_wifi", "no_data")
- `clock_view.py:7-10` - Clock sync state (`_synced` boolean) and cached timezone offset (`_cached_tz_offset`)
- `system_view.py:6` - Cached WAN IP address (`_cached_wan_ip`)
- Cache refresh: Driven by `main.py._refresh_all()` which calls `bootstrap.fetch()` once per refresh window, then distributes results to view setters

## Authentication & Identity

**Auth Provider:**
- None — both external APIs are anonymous, no authentication required

**WiFi Credentials:**
- Source: `secrets.py` (user-created, gitignored file)
- Fields: `WIFI_SSID`, `WIFI_PASSWORD`
- Failure: If `secrets.py` missing, `main.py:37-46` catches `ImportError` and displays fallback screen ("missing secrets.py")

## Monitoring & Observability

**Error Tracking:**
- None — no external error tracking service

**Logs:**
- None — no persistent logging
- Debugging via `mpremote` or Thonny IDE console only
- UI fallback states convey errors to user: "connecting...", "no wifi", "no data", "--:--" (clock unsync'd)

## CI/CD & Deployment

**Hosting:**
- Raspberry Pi Pico W (standalone, no cloud hosting)

**CI Pipeline:**
- None — no CI/CD pipeline; MicroPython files copied directly to device via `mpremote cp` or Thonny

**Deployment:**
- Manual file copy to Pico filesystem: `mpremote cp sh1107.py main.py bootstrap.py icons.py text_render.py views/ :`
- Auto-run on Pico power-up (MicroPython executes `main.py` automatically)

## Environment Configuration

**Required env vars:**
- None — all configuration via `secrets.py` (credentials file) or `main.py` module constants
- WiFi SSID/password: `secrets.py.WIFI_SSID`, `secrets.py.WIFI_PASSWORD`

**Secrets location:**
- `secrets.py` - User-created file in Pico root filesystem (`.gitignore`d)
- Example template: `secrets.py.example` (may be committed to show structure)

**Optional config:**
- `REFRESH_SECONDS` (default 600) - Weather refresh interval in seconds (`main.py:9`)
- `ROTATE` (default True) - Display 180° flip (`main.py:10`)
- `_POLL_MS` (default 100) - Main loop tick interval in milliseconds (`main.py:14`)
- `_DEBOUNCE_MS` (default 50) - Button debounce threshold in milliseconds (`main.py:15`)

## Webhooks & Callbacks

**Incoming:**
- None — Pico W is not a server; no HTTP endpoints exposed

**Outgoing:**
- None — API calls are request-response only, no webhook callbacks registered

## Network & Connectivity

**WiFi:**
- Standard 2.4GHz WiFi (WPA2 assumed)
- Timeout: 20 seconds for initial connection attempt (`bootstrap.py:11`)
- Retry: After failed fetch, 60s retry cadence for weather/NTP (`weather_view.py:13`, `clock_view.py:13`)
- Signal strength: Queried on-demand for system view display via `network.WLAN.status("rssi")` (`system_view.py:66`)

**DNS/NTP:**
- NTP pool assumed available on WiFi network (standard Pico W MicroPython setup)
- `ntptime.settime()` called with 60s retry until success, then 6h re-sync (`clock_view.py:64-73`)

## Rate Limiting & Throttling

**Not explicitly handled:**
- `ip-api.com` - No rate-limiting detection; limit is ~45 requests per minute per IP (gracefully degraded if exceeded)
- `api.open-meteo.com` - No rate-limiting detection; generous free tier (generous quota, unlikely to hit)
- Implicit throttling: Fetch cadence 10 minutes normal, 60s on failure (`weather_view.py:12-13`)

## Data Security

**HTTPS:**
- `ip-api.com` - HTTP only (non-sensitive geolocation, public IP known to ISP)
- `api.open-meteo.com` - HTTPS (`bootstrap.py:45`)

**Credentials:**
- WiFi SSID/password in `secrets.py` (local file only, not transmitted to external service)
- No API keys needed for either service

**Privacy:**
- Public WAN IP and location sent to `ip-api.com` on every weather refresh (~10 min cadence)
- No tracking or telemetry beyond these two requests

---

*Integration audit: 2026-07-19*
