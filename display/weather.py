import urequests


def current():
    try:
        r = urequests.get("http://ip-api.com/json/")
        loc = r.json()
        r.close()
        url = ("https://api.open-meteo.com/v1/forecast"
               "?latitude={}&longitude={}"
               "&current=temperature_2m,weather_code,is_day").format(
            loc["lat"], loc["lon"])
        r = urequests.get(url)
        cur = r.json()["current"]
        r.close()
        return cur["temperature_2m"], cur["weather_code"], cur["is_day"]
    except Exception:
        return None, None, None
