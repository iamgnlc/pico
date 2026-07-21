from sh1107 import OLED, WIDTH, HEIGHT
from machine import Pin, reset
import rp2
import network
from views import weather_view, clock_view, system_view
import text_render
import bootstrap
import time

# ---- user config -----------------------------------------------------------
REFRESH_SECONDS = 600      # Weather auto-refresh cadence (Plan 02-03 wires this in)
ROTATE          = True     # True = flip display 180°
# ---------------------------------------------------------------------------

# ---- private tunables ------------------------------------------------------
_POLL_MS      = 100        # main-loop tick (D-15, 50-100ms band)
_DEBOUNCE_MS  = 50         # software debounce threshold (D-14, 30-80ms band)
_KEY0_PIN     = 15         # KEY0 GPIO (previous view) — Waveshare HAT
_KEY1_PIN     = 17         # KEY1 GPIO (next view) — Waveshare HAT
# ---------------------------------------------------------------------------

# ---- carousel + IRQ state --------------------------------------------------
# Shared debounce timestamp (single _last_press_ms across both buttons):
# two buttons on the same HAT will not physically fire within the debounce
# window, so a single timestamp is sufficient and simpler than one per button.
_current_idx   = 0          # boot on Weather (NAV-04)
_pending_dir   = 0          # IRQ writes -1 (KEY0) or +1 (KEY1); loop reads + clears
_last_press_ms = 0
VIEWS = (weather_view, clock_view, system_view)
# ---------------------------------------------------------------------------


def _center_text(oled, s, x_center, y_center, scale=1):
    w = 8 * len(s) * scale
    h = 8 * scale
    text_render.text(oled, s, x_center - w // 2, y_center - h // 2, scale)


try:
    import secrets
except ImportError:
    oled = OLED(rotate=ROTATE)
    oled.fill(0)
    _center_text(oled, "missing", WIDTH // 2, HEIGHT // 3)
    _center_text(oled, "secrets.py", WIDTH // 2, 2 * HEIGHT // 3)
    oled.show()
    while True:
        time.sleep(3600)


def _on_key0(pin):
    global _pending_dir, _last_press_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS:
        return
    _last_press_ms = now
    _pending_dir = -1


def _on_key1(pin):
    global _pending_dir, _last_press_ms
    now = time.ticks_ms()
    if time.ticks_diff(now, _last_press_ms) < _DEBOUNCE_MS:
        return
    _last_press_ms = now
    _pending_dir = 1


def _draw_page_dots(oled, current_idx):
    # Three dots at y=60, r=2, x-centers 52/64/76 (12px spacing, centered on 128px).
    # Filled active + hollow inactive via fb.ellipse (D-19, D-20, D-21).
    for i in range(3):
        cx = 52 + i * 12
        oled.ellipse(cx, 60, 2, 2, 1, i == current_idx)


def _refresh_all(oled):
    # Composition-root fan-out: bootstrap fetches once; each view's public
    # setter absorbs its field. weather_view then paints the panel. main
    # overlays the current view before the final show() at each call site
    # (see boot-fetch and scheduler-tick blocks below).
    ip, temp, code, is_day, tz_offset, wan_ip = bootstrap.fetch()
    weather_view.set_data(ip, temp, code, is_day)
    clock_view.set_tz_offset(tz_offset)
    system_view.set_wan_ip(wan_ip)
    weather_view.render(oled)


if __name__ == "__main__":
    oled = OLED(rotate=ROTATE)

    # Pin + IRQ setup — keep key0/key1 locals in scope so MicroPython doesn't
    # garbage-collect the Pin objects and stop delivering interrupts.
    key0 = Pin(_KEY0_PIN, Pin.IN, Pin.PULL_UP)
    key1 = Pin(_KEY1_PIN, Pin.IN, Pin.PULL_UP)
    key0.irq(handler=_on_key0, trigger=Pin.IRQ_FALLING)
    key1.irq(handler=_on_key1, trigger=Pin.IRQ_FALLING)

    # Pre-fetch render: draw "connecting..." + dots to the panel BEFORE the
    # blocking wifi.connect() call so the user isn't staring at a black screen
    # for up to 20s on cold boot. weather_view.render draws from its "pending"
    # cache_status (initial value) which produces "connecting...".
    weather_view.render(oled)
    _draw_page_dots(oled, _current_idx)
    oled.show()

    # Initial boot fetch. Blocking (up to ~20s on wifi timeout); presses during
    # this window are still captured by the IRQ handlers into _pending_dir and
    # dispatched immediately after this returns.
    _refresh_all(oled)
    _draw_page_dots(oled, _current_idx)
    oled.show()

    # Best-effort boot NTP sync. Non-blocking failure — clock_view.render will
    # show '--:--' if _synced stays False; the poll loop retries at _RETRY_MS.
    clock_view.sync(oled)

    while True:
        # BOOTSEL short-press = hard reset. Wait-for-release avoids the boot-ROM mass-storage trap.
        if rp2.bootsel_button():
            # BOOTSEL is also read by the boot ROM at reset time — if still held
            # when reset() fires, the Pico enters USB mass-storage mode instead
            # of rebooting into main.py. Wait for release before resetting.
            while rp2.bootsel_button():
                pass
            # Clean CYW43 shutdown so the post-reset boot's _wifi_connect starts
            # from a known-good state, not a retained-associated wedge that
            # hangs urequests forever. reset() below MUST stay unconditional.
            try:
                wlan = network.WLAN(network.STA_IF)
                wlan.disconnect()
                wlan.active(False)
            except Exception:
                pass
            reset()
        now = time.ticks_ms()
        if _pending_dir != 0:
            _current_idx = (_current_idx + _pending_dir) % 3
            _pending_dir = 0
            VIEWS[_current_idx].render(oled)
            _draw_page_dots(oled, _current_idx)
            oled.show()
        if weather_view.should_refresh(now):
            _refresh_all(oled)
            # Refresh's final render draws Weather content. If the user is on
            # Clock or System, overpaint with the current view so the visible
            # panel matches _current_idx.
            VIEWS[_current_idx].render(oled)
            _draw_page_dots(oled, _current_idx)
            oled.show()
        if _current_idx == 1 and clock_view.should_tick(now):
            clock_view.render(oled)
            _draw_page_dots(oled, _current_idx)
            oled.show()
        if clock_view.should_sync(now):
            clock_view.sync(oled)
        time.sleep_ms(_POLL_MS)
