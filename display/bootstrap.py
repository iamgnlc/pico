import network
import time
import urequests
import secrets

_IP_API_URL = "http://ip-api.com/json/?fields=lat,lon,offset,query"
_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,weather_code,is_day"
)

_WIFI_TIMEOUT_S = 30
_HTTP_TIMEOUT_S = 10


class WifiTimeout(Exception):
    pass


def _try_connect(wlan):
    wlan.active(True)
    if wlan.isconnected():
        return
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    deadline = time.ticks_add(time.ticks_ms(), _WIFI_TIMEOUT_S * 1000)
    while not wlan.isconnected():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise WifiTimeout()
        time.sleep_ms(200)


def connect():
    wlan = network.WLAN(network.STA_IF)
    try:
        _try_connect(wlan)
        return wlan
    except Exception:
        # CYW43 can come back from a soft reset in a wedged state where
        # wlan.active/connect raise EPERM or the wait loop times out.
        # One active(False)/active(True) cycle unsticks it; if it still
        # fails, surface as WifiTimeout so main's 10s retry kicks in.
        try:
            wlan.active(False)
        except Exception:
            pass
        time.sleep_ms(500)
    try:
        _try_connect(wlan)
        return wlan
    except Exception:
        raise WifiTimeout()


def _get_json(url):
    r = urequests.get(url, timeout=_HTTP_TIMEOUT_S)
    try:
        return r.json()
    finally:
        r.close()


def fetch_weather():
    connect()
    loc = _get_json(_IP_API_URL)
    lat = loc["lat"]
    lon = loc["lon"]
    weather = _get_json(_METEO_URL.format(lat=lat, lon=lon))
    current = weather["current"]
    return {
        "temp": current["temperature_2m"],
        "code": current["weather_code"],
        "is_day": bool(current["is_day"]),
        "lat": lat,
        "lon": lon,
    }
