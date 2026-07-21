import network
import time
import urequests


def _wifi_connect(ssid, password, timeout=30):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Fast path: mid-session refreshes must not pay for reconnect.
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    wlan.connect(ssid, password)
    for _ in range(timeout):
        if wlan.isconnected():
            break
        time.sleep(1)
    if wlan.isconnected():
        return wlan.ifconfig()[0]
    # One-shot recovery: full CYW43 radio reset before a shorter retry window.
    # Clears stuck association state that a plain wlan.connect() retry cannot.
    wlan.disconnect()
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    wlan.connect(ssid, password)
    for _ in range(10):
        if wlan.isconnected():
            break
        time.sleep(1)
    return wlan.ifconfig()[0] if wlan.isconnected() else None


def fetch():
    # Bootstrap round-trip: WiFi connect + ip-api (lat/lon/offset/query) +
    # open-meteo. Returns 6-tuple (ip, temp, code, is_day, offset, wan_ip).
    # Failure semantics:
    #   - WiFi fails        → (None, None, None, None, None, None) — ip is None
    #   - WiFi ok, API fail → (ip,   None, None, None, None, None) — temp is None
    # This lets the caller distinguish "no_wifi" from "no_data" cache states.
    #
    # Lazy import: secrets.py absence is caught by main.py's fallback block,
    # which halts before fetch() is ever called. Importing at module load
    # would fire ImportError during `import bootstrap` in main.py — before
    # the fallback screen renders — and drop to REPL instead.
    import secrets

    ip = _wifi_connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    if not ip:
        return None, None, None, None, None, None

    try:
        # ip-api's default response omits `offset` and `query`; request both
        # explicitly along with lat/lon. Without ?fields=..., the extended
        # fields come back as None and downstream setters no-op.
        r = urequests.get("http://ip-api.com/json/?fields=lat,lon,offset,query", timeout=10)
        loc = r.json()
        r.close()
        offset = loc.get("offset")
        wan_ip = loc.get("query")
        url = ("https://api.open-meteo.com/v1/forecast"
               "?latitude={}&longitude={}"
               "&current=temperature_2m,weather_code,is_day").format(
            loc["lat"], loc["lon"])
        r = urequests.get(url, timeout=10)
        cur = r.json()["current"]
        r.close()
        return ip, cur["temperature_2m"], cur["weather_code"], cur["is_day"], offset, wan_ip
    except Exception:
        return ip, None, None, None, None, None
