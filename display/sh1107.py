from machine import Pin, SPI
from micropython import const
import framebuf
import time

# Waveshare Pico-OLED-1.3 HAT pinout (fixed by the header).
_DC   = const(8)
_CS   = const(9)
_SCK  = const(10)
_MOSI = const(11)
_RST  = const(12)

WIDTH  = const(128)
HEIGHT = const(64)


class OLED(framebuf.FrameBuffer):
    def __init__(self, rotate=False):
        self.rotate = rotate
        self.cs  = Pin(_CS,  Pin.OUT, value=1)
        self.rst = Pin(_RST, Pin.OUT, value=1)
        self.dc  = Pin(_DC,  Pin.OUT, value=1)
        self.spi = SPI(1, 20_000_000, polarity=0, phase=0,
                       sck=Pin(_SCK), mosi=Pin(_MOSI))

        self.buffer = bytearray(WIDTH * HEIGHT // 8)
        super().__init__(self.buffer, WIDTH, HEIGHT, framebuf.MONO_HMSB)
        self._init()

    def _cmd(self, c):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytes([c]))
        self.cs(1)

    def _init(self):
        self.rst(1); time.sleep_ms(1)
        self.rst(0); time.sleep_ms(10)
        self.rst(1); time.sleep_ms(10)

        for c in (
            0xAE,           # display off
            0x00, 0x10,     # column addr low / high nibble = 0
            0xB0,           # page addr = 0
            0xDC, 0x00,     # display start line
            0x81, 0x6F,     # contrast
            0x21,           # memory addressing mode: vertical (single-byte cmd)
            0xA0,           # segment remap (rotation handled in show())
            0xC0,           # COM output scan direction
            0xA4,           # display follows RAM
            0xA6,           # non-inverted
            0xA8, 0x3F,     # multiplex ratio = 64
            0xD3, 0x60,     # display offset
            0xD5, 0x41,     # oscillator / clock divide
            0xD9, 0x22,     # pre-charge period
            0xDB, 0x35,     # VCOMH deselect
            0xAD, 0x8A,     # internal DC-DC on
            0xAF,           # display on
        ):
            self._cmd(c)

    def show(self):
        if self.rotate:
            rot_buf = bytearray(len(self.buffer))
            rot_fb = framebuf.FrameBuffer(rot_buf, WIDTH, HEIGHT,
                                          framebuf.MONO_HMSB)
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if self.pixel(x, y):
                        rot_fb.pixel(WIDTH - 1 - x, HEIGHT - 1 - y, 1)
            buf = rot_buf
        else:
            buf = self.buffer

        self._cmd(0xB0)
        for i in range(64):
            col = 63 - i
            self._cmd(0x00 + (col & 0x0F))
            self._cmd(0x10 + (col >> 4))
            # SH1107 needs CS toggled around every data byte, not just the
            # whole chunk — a single continuous CS-low burst does not latch
            # bytes correctly into GDDRAM on this panel.
            for byte in buf[i * 16:(i + 1) * 16]:
                self.dc(1)
                self.cs(0)
                self.spi.write(bytes([byte]))
                self.cs(1)

    def poweroff(self):
        self._cmd(0xAE)

    def poweron(self):
        self._cmd(0xAF)
