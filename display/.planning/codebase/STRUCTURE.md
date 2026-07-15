# Codebase Structure

**Analysis Date:** 2026-07-15

## Directory Layout

```
pico/display/
├── sh1107.py           # SH1107 OLED driver (framebuf.FrameBuffer subclass)
├── main.py             # Application entry point, config, render orchestration
├── wifi.py             # WiFi network connectivity
├── weather.py          # Weather API integration
├── icons.py            # Weather condition icon rendering
├── text_render.py      # Scaled text rendering helper
├── CLAUDE.md           # Project documentation (hardware, gotchas, reference)
└── .planning/
    └── codebase/       # Architecture/structure docs (this directory)
```

**No subdirectories or packages.** Flat structure matches MicroPython embedded constraints.

## Directory Purposes

**Project Root (`pico/display/`):**
- Purpose: MicroPython application for Pico W + Waveshare HAT
- Contains: Driver + app modules, config, documentation
- Key files: `sh1107.py` (driver), `main.py` (entry point)

**.planning/codebase/**
- Purpose: Generated architecture and structure documentation
- Contains: ARCHITECTURE.md, STRUCTURE.md, (future) CONCERNS.md, CONVENTIONS.md, etc.
- Key files: This directory

## Key File Locations

**Entry Points:**
- `main.py:37–41`: `if __name__ == "__main__"` block — spawns OLED, enters render loop

**Configuration:**
- `main.py:8–13`: User config constants (`WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`)

**Core Logic:**
- `sh1107.py`: Hardware driver — SPI init, display commands, framebuffer→GDDRAM transfer
- `main.py:22–34`: `_render()` — weather fetch + UI orchestration
- `weather.py:4–18`: `current()` — dual API calls (geolocation + weather)
- `icons.py:73–74`: `draw()` — weather condition dispatcher

**Testing:**
- None — embedded device, no host-side test harness

## Naming Conventions

**Files:**
- Lowercase with underscores: `sh1107.py`, `text_render.py`, `weather.py`
- Matches MicroPython convention
- Driver is named after hardware chip: `sh1107.py`

**Directories:**
- Lowercase: `.planning/`, `codebase/`

**Python Modules/Functions:**
- Lowercase with underscores: `connect()`, `current()`, `text()`, `draw()`
- Private (module-level only): prefixed with `_` — e.g., `_render()`, `_cmd()`, `_init()`, `_kind()`, `_sun()`, `_moon()`, etc.
- Public: No prefix — e.g., `OLED` class, `connect()`, `current()`

**Python Constants:**
- Uppercase: `WIDTH`, `HEIGHT`, `WIFI_SSID`, `REFRESH_SECONDS`, `ROTATE`
- Module-level config always uppercase in `main.py:8–13`

**Classes:**
- PascalCase: `OLED`

## Where to Add New Code

**New Feature (e.g., additional data display):**
- Primary code: Add function/class to `main.py` or create new module at root level (e.g., `clock.py`)
- Rendering logic: Add function to new module, import and call from `main.py._render()`
- Tests: Not applicable (embedded device)

**New Component/Module (e.g., SD card file I/O):**
- Implementation: Create new `.py` file in root (e.g., `sdcard.py`)
- Public interface: Define top-level functions or classes
- Integration: Import in `main.py` and call from `_render()` as needed

**Utilities (e.g., angle/color helpers):**
- Shared helpers: Create new module in root (e.g., `utils.py`) with underscore-prefixed functions
- Alternatively: Add private functions to existing module if scope is narrow

**Hardware Driver Modifications:**
- Location: `sh1107.py` only
- Constraints: Do not move pinout (fixed by HAT header). Do not change framebuffer format (`MONO_HMSB`). See CLAUDE.md "Non-obvious SH1107 gotchas" before modifying `_init()`, `show()`, or CS/DC logic.

**User Configuration:**
- Location: `main.py:8–13` (top of file)
- Pattern: Module-level constants in UPPERCASE
- Expected changes: `WIFI_SSID`, `WIFI_PASSWORD`, `REFRESH_SECONDS`, `ROTATE`
- Workflow: Edit, save, run `main.py` again (no build step)

## Special Directories

**.planning/codebase/**
- Purpose: Machine-readable architecture documentation (auto-generated)
- Generated: Yes (by codebase mapper)
- Committed: Yes (part of repo)

**No other special directories** (no `__pycache__`, `.git`, `venv`, etc. relevant to this project)

## Module Import Graph

```
main.py
  ├→ sh1107 (OLED driver)
  ├→ wifi (network)
  ├→ weather (weather API)
  ├→ icons (icon rendering)
  └→ text_render (text scaling)

sh1107.py
  └→ (no local imports, stdlib only)

wifi.py, weather.py, icons.py, text_render.py
  └→ (stdlib only, no interdependencies)
```

All dependencies are acyclic. Single import from main → modules, no feedback.

## File Size Guidelines

**Small (<300 lines):**
- `wifi.py` (15 lines) — minimal network wrapper
- `text_render.py` (16 lines) — single function, double-buffer scaling
- `weather.py` (19 lines) — API integration with error handling
- `icons.py` (75 lines) — icon lookup + 7 drawing functions

**Medium (<400 lines):**
- `main.py` (42 lines) — config + render + entry point
- `sh1107.py` (97 lines) — driver class, init sequence, show() implementation

Files are small by design — each module has single responsibility, suitable for code review and debugging on embedded device.

## Typical Workflow

**1. First-time setup:**
```bash
# Clone repo
git clone <repo>
cd pico/display

# Copy driver + app to Pico
mpremote cp sh1107.py main.py :
```

**2. Modify user config:**
```python
# Edit main.py:8-13 (WiFi SSID, password, refresh interval, rotation)
# Save
```

**3. Run on Pico:**
```bash
mpremote run main.py
# Or: Open main.py in Thonny, select Pico, press Run
```

**4. Debug:**
- Print to UART: `print()`calls go to Thonny console or `mpremote monitor`
- No file I/O needed; state is ephemeral

**5. Modify driver:**
- Avoid unless necessary (see CLAUDE.md gotchas)
- After modification, `mpremote cp sh1107.py :` and re-run `main.py`

## Co-Location Principle

Files are not organized by layer (no `drivers/`, `utils/`, `api/`). Instead, each module is a **logical unit** at the root level:
- `sh1107.py` — single responsibility: hardware abstraction
- `weather.py` — single responsibility: weather data fetch
- `icons.py` — single responsibility: icon rendering
- etc.

**Rationale:** Flat structure with small files aids readability and navigation on resource-constrained environments. No deep nesting or package management overhead.

---

*Structure analysis: 2026-07-15*
