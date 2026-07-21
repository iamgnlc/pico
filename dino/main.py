# Endless-runner game for Raspberry Pi Pico + Waveshare Pico-OLED-1.3 HAT.
# Jump the dino over cacti; game speed ramps with score.
# Controls: KEY0 (GP15), KEY1 (GP17), joystick UP (GP2), joystick CTRL (GP3).
# BOOTSEL short-press = soft reset (matches sibling display project).

from sh1107 import OLED, WIDTH, HEIGHT
from machine import Pin, reset
from sprites import (
    DINO_A, DINO_B, DINO_W, DINO_H,
    CACT_S, CACT_S_W, CACT_S_H,
    CACT_L, CACT_L_W, CACT_L_H,
)
import rp2
import framebuf
import random
import time

ROTATE = False   # flip display 180° if the HAT is oriented that way

# ---- gameplay tunables ----------------------------------------------------
_GROUND_Y       = 52
_DINO_X         = 6
_GRAVITY        = 0.55
_JUMP_V         = -5.5
_INIT_SPEED     = 2.0
_MAX_SPEED      = 6.0
_SPEED_STEP     = 0.25
_SPEED_EVERY    = 300     # frames between speed bumps
_MIN_GAP_PX     = 72
_MAX_GAP_PX     = 130
_FRAME_MS       = 40      # ~25 fps target
_SCORE_DIVISOR  = 5       # frames per score point
_HIGHSCORE_FILE = "highscore.txt"

# ---- input pins (fixed by Waveshare HAT) ----------------------------------
_KEY0     = 15
_KEY1     = 17
_JOY_UP   = 2
_JOY_CTRL = 3

# ---- sprite framebuffers --------------------------------------------------
# Bytes come from sprites.py, generated from dino.png / cactus.png by
# tools/build_sprites.py. Source is MONO_HLSB; cross-format blit onto the
# SH1107's MONO_HMSB panel works because framebuf.blit is pixel-by-pixel
# when source and dest formats differ.
_DINO_FB_A = framebuf.FrameBuffer(bytearray(DINO_A), DINO_W,   DINO_H,   framebuf.MONO_HLSB)
_DINO_FB_B = framebuf.FrameBuffer(bytearray(DINO_B), DINO_W,   DINO_H,   framebuf.MONO_HLSB)
_CACT_FB_S = framebuf.FrameBuffer(bytearray(CACT_S), CACT_S_W, CACT_S_H, framebuf.MONO_HLSB)
_CACT_FB_L = framebuf.FrameBuffer(bytearray(CACT_L), CACT_L_W, CACT_L_H, framebuf.MONO_HLSB)
_DINO_W, _DINO_H = DINO_W, DINO_H
_CS_W, _CS_H     = CACT_S_W, CACT_S_H
_CL_W, _CL_H     = CACT_L_W, CACT_L_H


def _read_highscore():
    try:
        with open(_HIGHSCORE_FILE) as f:
            return int((f.read().strip() or "0"))
    except (OSError, ValueError):
        return 0


def _write_highscore(v):
    try:
        with open(_HIGHSCORE_FILE, "w") as f:
            f.write(str(int(v)))
    except OSError:
        pass


class Dino:
    __slots__ = ("y", "vy", "on_ground", "ticks")

    def __init__(self):
        self.reset()

    def reset(self):
        self.y = float(_GROUND_Y - _DINO_H)
        self.vy = 0.0
        self.on_ground = True
        self.ticks = 0

    def jump(self):
        if self.on_ground:
            self.vy = _JUMP_V
            self.on_ground = False

    def step(self):
        self.ticks += 1
        if not self.on_ground:
            self.vy += _GRAVITY
            self.y += self.vy
            floor = _GROUND_Y - _DINO_H
            if self.y >= floor:
                self.y = floor
                self.vy = 0.0
                self.on_ground = True

    def draw(self, oled):
        # Freeze on frame A while airborne so the legs don't flap mid-jump.
        if self.on_ground and (self.ticks // 4) % 2:
            fb = _DINO_FB_B
        else:
            fb = _DINO_FB_A
        oled.blit(fb, _DINO_X, int(self.y), 0)

    def rect(self):
        # Hitbox skips the head (well above cactus tops), the tail tip, and a
        # bit of the toes so grazes past thin extremities don't feel unfair.
        return (_DINO_X + 3, int(self.y) + 8, _DINO_W - 6, _DINO_H - 10)


class Obstacle:
    __slots__ = ("x", "w", "h", "fb")

    def __init__(self, x, kind):
        self.x = float(x)
        if kind == 0:
            self.fb, self.w, self.h = _CACT_FB_S, _CS_W, _CS_H
        else:
            self.fb, self.w, self.h = _CACT_FB_L, _CL_W, _CL_H

    def step(self, speed):
        self.x -= speed

    def draw(self, oled):
        oled.blit(self.fb, int(self.x), _GROUND_Y - self.h, 0)

    def rect(self):
        return (int(self.x) + 1, _GROUND_Y - self.h + 2,
                self.w - 2, self.h - 2)

    def offscreen(self):
        return self.x + self.w < 0


def _aabb(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)


def _draw_ground(oled, offset):
    oled.hline(0, _GROUND_Y, WIDTH, 1)
    step = 14
    off = int(offset)
    for i in range(-1, WIDTH // step + 2):
        x = i * step - off
        oled.hline(x, _GROUND_Y + 2, 3, 1)
        oled.pixel(x + 8, _GROUND_Y + 3, 1)


def _center_text(oled, s, y):
    oled.text(s, (WIDTH - 8 * len(s)) // 2, y, 1)


def _draw_hud(oled, score, high):
    if high > 0:
        oled.text("HI{:04d}".format(high), 2, 1, 1)
    oled.text("{:04d}".format(score), WIDTH - 8 * 4 - 2, 1, 1)


def _draw_attract(oled, high):
    oled.fill(0)
    _draw_ground(oled, 0)
    oled.blit(_DINO_FB_A, _DINO_X, _GROUND_Y - _DINO_H, 0)
    _center_text(oled, "PICO DINO", 8)
    _center_text(oled, "PRESS KEY", 22)
    _center_text(oled, "TO START",  32)
    if high > 0:
        _center_text(oled, "HI {:04d}".format(high), 56)
    oled.show()


def _draw_game_over(oled, score, high):
    oled.fill(0)
    _draw_ground(oled, 0)
    _draw_hud(oled, score, high)
    _center_text(oled, "GAME OVER",      18)
    _center_text(oled, "PRESS TO RETRY", 32)
    oled.show()


def _make_keys():
    return (
        Pin(_KEY0,     Pin.IN, Pin.PULL_UP),
        Pin(_KEY1,     Pin.IN, Pin.PULL_UP),
        Pin(_JOY_UP,   Pin.IN, Pin.PULL_UP),
        Pin(_JOY_CTRL, Pin.IN, Pin.PULL_UP),
    )


def _pressed(keys):
    for k in keys:
        if k.value() == 0:
            return True
    return False


def _bootsel_reset_if_pressed():
    if rp2.bootsel_button():
        # BOOTSEL is also latched by the boot ROM at reset time — wait for
        # release so the Pico reboots into main.py instead of USB MSD mode.
        while rp2.bootsel_button():
            pass
        reset()


def _wait_release(keys):
    while _pressed(keys):
        _bootsel_reset_if_pressed()
        time.sleep_ms(10)


def _wait_press(keys):
    while not _pressed(keys):
        _bootsel_reset_if_pressed()
        time.sleep_ms(15)


def main():
    oled = OLED(rotate=ROTATE)
    keys = _make_keys()
    high = _read_highscore()

    _draw_attract(oled, high)
    _wait_press(keys)
    _wait_release(keys)

    while True:
        dino = Dino()
        obstacles = []
        score = 0
        speed = _INIT_SPEED
        ground_offset = 0.0
        next_gap = random.randint(_MIN_GAP_PX, _MAX_GAP_PX)
        gap_travelled = _MAX_GAP_PX // 2   # first obstacle appears faster
        last_frame = time.ticks_ms()

        while True:
            _bootsel_reset_if_pressed()

            # Frame pacing
            elapsed = time.ticks_diff(time.ticks_ms(), last_frame)
            if elapsed < _FRAME_MS:
                time.sleep_ms(_FRAME_MS - elapsed)
            last_frame = time.ticks_ms()

            # Input — held key still only triggers one jump because Dino.jump
            # is a no-op unless on_ground.
            if _pressed(keys):
                dino.jump()

            # Step world
            dino.step()
            ground_offset = (ground_offset + speed) % 14
            for o in obstacles:
                o.step(speed)
            obstacles = [o for o in obstacles if not o.offscreen()]

            # Spawn on gap-distance travelled, so cadence scales with speed.
            gap_travelled += speed
            if gap_travelled >= next_gap:
                obstacles.append(Obstacle(WIDTH + 4, random.randint(0, 1)))
                next_gap = random.randint(_MIN_GAP_PX, _MAX_GAP_PX)
                gap_travelled = 0

            # Score & difficulty ramp
            score += 1
            if score % _SPEED_EVERY == 0 and speed < _MAX_SPEED:
                speed = min(_MAX_SPEED, speed + _SPEED_STEP)

            # Collide
            drect = dino.rect()
            hit = False
            for o in obstacles:
                if _aabb(drect, o.rect()):
                    hit = True
                    break

            # Render
            oled.fill(0)
            _draw_ground(oled, ground_offset)
            for o in obstacles:
                o.draw(oled)
            dino.draw(oled)
            _draw_hud(oled, score // _SCORE_DIVISOR, high)
            oled.show()

            if hit:
                break

        # Post-game
        final = score // _SCORE_DIVISOR
        if final > high:
            high = final
            _write_highscore(high)
        _draw_game_over(oled, final, high)
        time.sleep_ms(400)   # brief guard so the fatal press doesn't restart
        _wait_release(keys)
        _wait_press(keys)
        _wait_release(keys)


if __name__ == "__main__":
    main()
