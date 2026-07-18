import urequests


def current():
    try:
        # ip-api's default response omits `offset`; request it explicitly along
        # with lat/lon. Without ?fields=..., loc.get("offset") returns None and
        # clock_view.set_tz_offset(None) no-ops — the persistence file never
        # gets written and the Clock view stays stuck at "--:--".
        r = urequests.get("http://ip-api.com/json/?fields=lat,lon,offset")
        loc = r.json()
        r.close()
        offset = loc.get("offset")
        url = ("https://api.open-meteo.com/v1/forecast"
               "?latitude={}&longitude={}"
               "&current=temperature_2m,weather_code,is_day").format(
            loc["lat"], loc["lon"])
        r = urequests.get(url)
        cur = r.json()["current"]
        r.close()
        return cur["temperature_2m"], cur["weather_code"], cur["is_day"], offset
    except Exception:
        return None, None, None, None
