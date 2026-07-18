import network
import text_render
from sh1107 import WIDTH


_cached_wan_ip = None


def _draw_bars(oled, x, y, level):
    # 4 vertical bars, filled if bar index < level, hollow otherwise.
    # Each bar is 4 px wide, 6 px tall, 2 px gap. Total width = 22 px.
    # y is the top of the bars (not baseline).
    for i in range(4):
        bx = x + i * 6
        if i < level:
            oled.fill_rect(bx, y, 4, 6, 1)
        else:
            oled.rect(bx, y, 4, 6, 1)


def _rssi_to_bars(rssi):
    if rssi >= -55:
        return 4
    if rssi >= -65:
        return 3
    if rssi >= -75:
        return 2
    return 1


def set_wan_ip(ip):
    # Public setter called by weather_view.refresh after each successful weather
    # fetch. Idempotent guard: skip on None (failed fetches) and on unchanged
    # value. RAM-only — no file persistence (D-43-bis).
    global _cached_wan_ip
    if ip is None:
        return
    if ip == _cached_wan_ip:
        return
    _cached_wan_ip = ip


def render(oled):
    oled.fill(0)
    wlan = network.WLAN(network.STA_IF)
    connected = wlan.isconnected()

    # SSID line (y=8)
    if connected:
        ssid = wlan.config("essid")
        ssid = ssid[:min(15, WIDTH // 8)]
        text_render.text(oled, "SSID: " + ssid, 0, 8, 1)
    else:
        text_render.text(oled, "SSID: --", 0, 8, 1)

    # IP line (y=24) — WAN IP; shown only when connected AND cache populated
    if connected and _cached_wan_ip is not None:
        text_render.text(oled, "IP: " + _cached_wan_ip, 0, 24, 1)
    else:
        text_render.text(oled, "IP: --", 0, 24, 1)

    # Signal line (y=40) — label + drawn bars
    text_render.text(oled, "Signal ", 0, 40, 1)
    if connected:
        try:
            rssi = wlan.status("rssi")
            level = _rssi_to_bars(rssi)
        except Exception:
            level = 0
    else:
        level = 0
    # Bars start at x=56 (7 chars * 8 px = 56), aligned with the label baseline
    _draw_bars(oled, 56, 40, level)
