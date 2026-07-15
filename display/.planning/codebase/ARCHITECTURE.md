# Architecture

**Analysis Date:** 2026-07-15

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│                           main.py                                │
│  Renders weather + temp UI, manages refresh loop                │
└──────────────────────┬───────────────────────────────────────────┘
                       │ calls
         ┌─────────────┼─────────────┬──────────────┐
         │             │             │              │
         ▼             ▼             ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│   wifi.py    │ │ weather  │ │ icons.py │ │text_render.py│
│  WiFi/IP     │ │ .py      │ │Weather   │ │Font scaling  │
│  connect()   │ │API calls │ │graphics  │ │&positioning  │
└──────────────┘ └──────────┘ └──────────┘ └──────────────┘
                                   │
                                   │ uses
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Hardware Abstraction Layer                    │
│                          sh1107.py                               │
│              OLED class (framebuf.FrameBuffer)                   │
│   SPI init, display commands, show() buffer→panel flow          │
└──────────────────────────────────────────────────────────────────┘
                       │
                       │ drives
         ┌─────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│         Waveshare Pico-OLED-1.3 HAT (SH1107 Controller)         │
│     128×64 OLED, SPI (GP8:DC, GP9:CS, GP10:SCK, GP11:MOSI,    │
│                     GP12:RST, SPI bus 1)                        │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| OLED Driver | Hardware initialization, SPI comms, framebuffer→GDDRAM transfer, power management | `sh1107.py` |
| Application | User configuration, UI rendering loop, weather fetch orchestration | `main.py` |
| WiFi | Network connectivity, IP retrieval | `wifi.py` |
| Weather | Remote API calls (geolocation + weather), JSON parsing | `weather.py` |
| Icons | Weather condition → visual rendering (sun/moon/cloud/rain/snow/thunder/fog) | `icons.py` |
| Text Render | Font scaling via double-buffer framebuf technique | `text_render.py` |

## Pattern Overview

**Overall:** Layered monolithic application with hardware abstraction driver.

**Key Characteristics:**
- Single-file driver (`sh1107.py`) decoupled from app logic via `framebuf.FrameBuffer` subclassing
- Framebuffer-first design — all drawing operations happen in-memory first, then pushed to hardware via `show()`
- No state persistence or complex inter-module dependencies
- Flat namespace (no packages) suitable for embedded constraint

## Layers

**Hardware Driver (`sh1107.py`):**
- Purpose: Abstract Raspberry Pi Pico SPI hardware and SH1107 OLED controller protocol
- Location: `sh1107.py`
- Contains: OLED class, SPI pin configuration, init sequence, `show()` method, power control
- Depends on: `machine.Pin`, `machine.SPI`, `framebuf`, `time` (MicroPython stdlib)
- Used by: `main.py` and any user code needing display output

**Application Layer (`main.py`):**
- Purpose: User-facing configuration, rendering orchestration, refresh loop
- Location: `main.py`
- Contains: User config constants (`WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`), `_render()` orchestrator, `__main__` entry point
- Depends on: `sh1107.OLED`, `wifi`, `weather`, `icons`, `text_render`
- Used by: MicroPython runtime (executed as main entry point)

**WiFi Module (`wifi.py`):**
- Purpose: Network connection and IP acquisition
- Location: `wifi.py`
- Contains: `connect(ssid, password, timeout)` function
- Depends on: `network`, `time` (MicroPython stdlib)
- Used by: `main.py._render()`

**Weather Module (`weather.py`):**
- Purpose: Fetch current weather data from remote APIs
- Location: `weather.py`
- Contains: `current()` function that queries IP geolocation then weather forecast
- Depends on: `urequests` (MicroPython HTTP library)
- Used by: `main.py._render()`

**Icon Renderer (`icons.py`):**
- Purpose: Draw weather condition icons using framebuffer primitives
- Location: `icons.py`
- Contains: WMO weather code → icon type mapping, 7 rendering functions (sun/moon/cloud/rain/snow/thunder/fog), dispatcher
- Depends on: `framebuf` (via caller-supplied framebuffer)
- Used by: `main.py._render()` for icon drawing at screen coordinates

**Text Renderer (`text_render.py`):**
- Purpose: Scaled font rendering (native 1x only available in framebuf)
- Location: `text_render.py`
- Contains: `text(fb, s, x, y, scale, color)` function using double-buffer technique
- Depends on: `framebuf` (via caller-supplied framebuffer)
- Used by: `main.py._center_text()` for temperature display

## Data Flow

### Primary Render Cycle

1. **Entry:** `__main__` block in `main.py:37–41` spawns OLED instance with rotation config, enters infinite loop
2. **Trigger:** Loop calls `_render(oled)` every `REFRESH_SECONDS` (config at `main.py:11`)
3. **Clear:** `oled.fill(0)` clears framebuffer in-memory (`sh1107.py:29`, inherited from `framebuf.FrameBuffer`)
4. **Fetch WiFi:** `wifi.connect(ssid, password)` blocks up to 20s to establish network; returns IP or None (`wifi.py:5`)
5. **Fetch Weather:** If connected, `weather.current()` calls IP geolocation API then Open-Meteo API; returns `(temp, wmo_code, is_day)` or `(None, None, None)` on error (`weather.py:4`)
6. **Render UI:** Depending on data availability:
   - No WiFi → center "no wifi" text
   - No weather data → center "no data" text
   - Success → draw weather icon + temperature via `icons.draw()` + `_center_text()`
7. **Show:** `oled.show()` transfers framebuffer to display GDDRAM via SPI (`sh1107.py:65–90`)
8. **Sleep:** `time.sleep(REFRESH_SECONDS)` blocks until next render

### SPI Buffer Transfer (`show()` flow, `sh1107.py:65–90`)

1. **Optional Rotation:** If `self.rotate == True`:
   - Create temporary 1024-byte buffer `rot_buf`
   - Iterate all 128×64 pixels, read source pixel, write to rotated position (180° flip)
   - Use pixel-level operations to preserve GDDRAM wrap correctness (see **SH1107 Gotchas** below)
   - Point `buf` to rotated buffer; otherwise use original `self.buffer`
2. **Page-by-Page Addressing:** SH1107 uses page-based (vertical) addressing — 64 rows / 8 bits per row = 8 pages
   - For each of 64 rows `i`:
     - Calculate column address `col = 63 - i` (reverse row order for GDDRAM layout)
     - Send page address: `0xB0` (page register)
     - Send column low/high nibble: `0x00 + (col & 0x0F)` and `0x10 + (col >> 4)`
     - Write 16 bytes (128 pixels / 8 bits per byte) from `buf[i*16:(i+1)*16]`
3. **Per-Byte CS Toggle:** For each data byte:
   - Set DC high (data mode)
   - Set CS low
   - Write single byte to SPI
   - Set CS high
   - **Reason:** SH1107 does not latch correctly with continuous CS; see **SH1107 Gotchas #2**

## SH1107 Hardware Constraints

These constraints are baked into `sh1107.py` — **do not modify without understanding the hardware:**

### Gotcha #1: 0x21 Single-Byte Command

**The trap:** On SH1107, control register `0x20` (horizontal addressing) and `0x21` (vertical addressing) are *complete commands* that self-encode the addressing mode. Sending `0x21` followed by a data byte treats the data byte as the *next command*, silently breaking column/row addressing.

**Current implementation:** `_init()` sends `0x21` alone without follow-up argument (`sh1107.py:50`). Do not add `0x20` or `0x21` with parameters.

### Gotcha #2: CS Must Toggle Per Byte in `show()`

**The trap:** Typical SPI convention groups all chip-select activity — one CS pulse per multi-byte chunk. SH1107 *does not latch data into GDDRAM unless CS toggles between bytes*. A single continuous CS-low burst across 16 bytes results in 15 bytes silently discarded.

**Current implementation:** `show()` toggles CS around every single data byte (`sh1107.py:87–90`). This matches Waveshare's reference implementation. Violates typical SPI conventions but required for this panel.

### Gotcha #3: Rotation via Pixel Operations, Not Byte Shuffling

**The trap:** The `_init()` sequence sets display offset `0x60` (96 lines), creating a GDDRAM wrap: physical rows 0–31 display GDDRAM rows 96–127; physical rows 32–63 display GDDRAM rows 0–95. Because of this wrap, the buffer-to-panel mapping is *not a linear transform* across all 1024 bytes. A naive byte-reverse + bit-reverse (which produces 180° rotation mathematically) moves active pixels into the invisible GDDRAM half, blanking the screen.

**Hardware rotation attempted and broken:** Registers `0xA1` (segment remap) and `0xC8` (COM scan direction) exist, but enabling them *fights the display-offset wrap* and produces inverted/scrambled output.

**Current implementation:** `show()` rotates at the framebuffer pixel level (`sh1107.py:66–74`), reading/writing via `framebuf.FrameBuffer.pixel()` operations. This stays within the logical 128×64 coordinate space guaranteed to display correctly. Cost: ~8KB temporary buffer + O(128×64) pixel operations vs. byte-level, but guarantees correctness. Enable only when `OLED(rotate=True)` is passed.

### Gotcha #4: MONO_HMSB Framebuffer Format Required

**The trap:** `show()` assumes framebuffer format `MONO_HMSB` (128 bits = 16 bytes per row, bits packed horizontally/MSB-first). The alternative `MONO_VLSB` (bits packed vertically) scrambles the byte layout. Once the wrong format is set in the `FrameBuffer` constructor, all subsequent pixel operations invert the mapping, producing garbage output.

**Current implementation:** Framebuffer created with `framebuf.MONO_HMSB` (`sh1107.py:30`). Matches Waveshare's reference. Do not change to `MONO_VLSB`.

## Entry Points

**MicroPython Runtime Entry:**
- Location: `main.py:37–41` (`if __name__ == "__main__"` block)
- Triggers: Pico boots or user runs `main.py` via `mpremote run`/Thonny
- Responsibilities:
  1. Instantiate `OLED(rotate=ROTATE)` with user's rotation preference
  2. Enter infinite loop calling `_render(oled)` every `REFRESH_SECONDS`
  3. Graceful degradation if WiFi/weather APIs fail (shows fallback messages)

**Typical Deployment:**
```bash
mpremote cp sh1107.py main.py :
mpremote run main.py
```

Or open both in Thonny IDE, select Pico as device, and press Run.

## Architectural Constraints

- **Threading:** Single-threaded event loop. `wifi.connect()` and `weather.current()` are blocking. No async/await. Refresh cycle is synchronous.
- **Global state:** None — all state is local or instance variables within `OLED` class.
- **Circular imports:** None. Dependency graph is acyclic: `main.py` → {`sh1107`, `wifi`, `weather`, `icons`, `text_render`}, no feedback.
- **Memory model:** Framebuffer is 1024 bytes fixed. Rotation creates additional 1024-byte temporary buffer. Total ~2KB active + MicroPython runtime heap.
- **Hardware pinout:** Fixed by HAT header — no configuration possible (DC=GP8, CS=GP9, SCK=GP10, MOSI=GP11, RST=GP12, SPI bus 1). Do not attempt to move pins.

## Error Handling

**Strategy:** Silent degradation with on-screen messaging.

**Patterns:**
- WiFi connection timeout → `wifi.connect()` returns `None` after 20s, `main.py` displays "no wifi"
- Weather API failure (network, JSON parse, HTTP error) → `weather.current()` catches all exceptions, returns `(None, None, None)`, `main.py` displays "no data"
- No exception bubbling; all failures result in fallback UI display

## Cross-Cutting Concerns

**Logging:** None — embedded device with no host console at runtime. Debug via printing to UART (outside scope of display driver).

**Validation:** `weather.current()` validates HTTP response structure via `.json()["current"][field]` access — KeyError → caught and returns `(None, None, None)`. Input validation not needed (hardcoded URLs, no user config at runtime).

**Configuration:** All user config at module level in `main.py:8–13`:
- `WIFI_SSID`, `WIFI_PASSWORD` — network credentials
- `REFRESH_SECONDS` — render cycle interval
- `ROTATE` — 180° display flip (boolean passed to `OLED()`)

---

*Architecture analysis: 2026-07-15*
