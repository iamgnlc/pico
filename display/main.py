from sh1107 import OLED, WIDTH, HEIGHT
from machine import Pin, reset
import network
import text_render
import bootstrap
from views import weather
import time

REFRESH_SECONDS = 600
WIFI_RETRY_SECONDS = 10
ROTATE = True

_KEY0_PIN = 15
_KEY1_PIN = 17
_DEBOUNCE_MS = 50

_pending_refresh = False
_pending_reset = False
_last_press_ms = 0


def _show_error(oled, msg):
    oled.fill(0)
    text_render.text(oled, "error:", 4, 8, 1)
    chunk = 16
    for i in range(3):
        seg = msg[i * chunk:(i + 1) * chunk]
        if not seg:
            break
        text_render.text(oled, seg, 4, 24 + i * 10, 1)
    oled.show()


def _refresh(oled):
    data = bootstrap.fetch_weather()
    weather.set_data(data["temp"], data["code"], data["is_day"])
    weather.render(oled)


def _tick(oled):
    """Attempt a refresh; return seconds until the next attempt."""
    try:
        _refresh(oled)
        return REFRESH_SECONDS
    except bootstrap.WifiTimeout:
        _show_error(oled, "wifi timeout")
        return WIFI_RETRY_SECONDS
    except Exception as e:
        _show_error(oled, str(e))
        return REFRESH_SECONDS


def _on_key0(pin):
    global _pending_reset, _last_press_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS:
        return
    _last_press_ms = now
    _pending_reset = True


def _on_key1(pin):
    global _pending_refresh, _last_press_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS:
        return
    _last_press_ms = now
    _pending_refresh = True


def _hard_reset():
    # Clean CYW43 shutdown so the post-reset boot's wifi connect starts
    # from a known-good state, not a retained-associated wedge.
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.disconnect()
        wlan.active(False)
    except Exception:
        pass
    reset()


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)
    weather.render(oled)

    # Keep Pin objects in scope; MicroPython GCs them otherwise and IRQs stop.
    key0 = Pin(_KEY0_PIN, Pin.IN, Pin.PULL_UP)
    key1 = Pin(_KEY1_PIN, Pin.IN, Pin.PULL_UP)
    key0.irq(handler=_on_key0, trigger=Pin.IRQ_FALLING)
    key1.irq(handler=_on_key1, trigger=Pin.IRQ_FALLING)

    next_refresh = time.ticks_add(time.ticks_ms(), _tick(oled) * 1000)
    while True:
        if _pending_reset:
            _pending_reset = False
            _hard_reset()
        if _pending_refresh:
            _pending_refresh = False
            _tick(oled)
            next_refresh = time.ticks_add(time.ticks_ms(),
                                          REFRESH_SECONDS * 1000)
        if time.ticks_diff(next_refresh, time.ticks_ms()) <= 0:
            next_refresh = time.ticks_add(time.ticks_ms(), _tick(oled) * 1000)
        time.sleep_ms(500)
