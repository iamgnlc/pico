import urequests


def current():
    try:
        # ip-api's default response omits `offset` and `query`; request both
        # explicitly along with lat/lon. Without ?fields=..., the extended
        # fields come back as None and downstream setters no-op — persistence
        # never populates and the WAN IP display stays stuck at `--`.
        r = urequests.get("http://ip-api.com/json/?fields=lat,lon,offset,query")
        loc = r.json()
        r.close()
        offset = loc.get("offset")
        wan_ip = loc.get("query")
        url = ("https://api.open-meteo.com/v1/forecast"
               "?latitude={}&longitude={}"
               "&current=temperature_2m,weather_code,is_day").format(
            loc["lat"], loc["lon"])
        r = urequests.get(url)
        cur = r.json()["current"]
        r.close()
        return cur["temperature_2m"], cur["weather_code"], cur["is_day"], offset, wan_ip
    except Exception:
        return None, None, None, None, None
