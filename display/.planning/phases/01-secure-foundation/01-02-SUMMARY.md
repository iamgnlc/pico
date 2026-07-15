---
phase: 01-secure-foundation
plan: 02
wave: 2
status: complete
requirements:
  - WEATHER-01
files_modified:
  - display/main.py
completed: 2026-07-16
---

# 01-02 Degree Symbol — Summary

## What Was Built

`main.py:_render()` now shows the temperature as `19°` instead of `19C`. The format string drops the trailing `C` and a small hollow ring (`oled.ellipse(cx, cy, 2, 2, 1, False)`) is drawn immediately after the digits — same idiom as `icons.py:22`, but with `fill=False` for a hollow appearance. Ring coordinates derive from the digit-string length so 1-, 2-, and 3-digit temperatures all place the ring correctly.

## Requirements Coverage

| REQ | Delivered by |
|-----|--------------|
| WEATHER-01 | Format string `"{:.0f}".format(temp)` (no `C`) + inline `oled.ellipse(...)` in the temperature-only branch of `_render` |

## Commits

| Task | SHA | Message |
|------|-----|---------|
| 1 | bbe57f4 | `feat(01-02): render temperature as \`19°\` via inline degree ring (WEATHER-01)` |

## Verification

**On-device visual test:** operator confirmed the OLED shows digits followed by a small hollow ring in the top-right position, with a visible 2–3 pixel gap between the last digit and the ring. Weather icon on the left is unchanged.

**Source acceptance:** `"{:.0f}C"` absent from `main.py`, `"{:.0f}"` present, exactly one `oled.ellipse(...)` call with `fill=False`, no new helper function, no `views/` import, `ast.parse` succeeds.

## Decisions Honored

- **D-06:** ring drawn via `fb.ellipse` with `rx=ry=2` and `fill=False`
- **D-07:** call inlined in `_render`; no extraction to `text_render.py` or `views/` module
- **D-08:** format string strips the `C`
- **CLAUDE.md gotchas:** `sh1107.py` untouched; framebuffer format, rotation, and `show()` loop all unchanged

## Handoff

Both code changes for Phase 1 are committed. `main.py` no longer contains WiFi credential literals and the OLED renders the temperature with a proper degree symbol. Wave 3 (Plan 01-03) is the destructive step — `git filter-repo` scrubs the two credential strings from all history, then force-push. Requires operator to confirm router-side password rotation before proceeding.
