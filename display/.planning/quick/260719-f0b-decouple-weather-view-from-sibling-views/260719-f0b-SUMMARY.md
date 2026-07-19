---
status: complete
quick_task: 260719-f0b
date: 2026-07-19
commits:
  - hash: c78b12c
    message: "refactor(260719-f0b): move cross-view dispatch from weather_view to main._refresh_all"
    files: [views/weather_view.py, main.py, views/clock_view.py, views/system_view.py]
  - hash: 1b47637
    message: "docs(260719-f0b): patch CLAUDE.md import bullets + component table; record decision in STATE.md"
    files: [CLAUDE.md, .planning/STATE.md]
---

# Quick Task 260719-f0b: Decouple weather_view from sibling views

**One-liner:** Moved cross-view setter dispatch and bootstrap.fetch() out of weather_view.refresh into a new main._refresh_all composition-root helper; weather_view is now a pure state-setter + render module.

## Task Breakdown

### Task 1+2 (Atomic Commit c78b12c): Refactor weather_view.py + update main.py + patch sibling comments

These landed as a single atomic commit because T-1 alone leaves the tree broken (main.py still calls `weather_view.refresh` which no longer exists).

**views/weather_view.py** (4 lines removed, 17 lines added/modified):
- Removed: `import bootstrap` (line 2), `from views import clock_view, system_view` (line 3)
- Removed: entire `refresh(oled)` function (was lines 48-70, 23 lines)
- Added: `set_data(ip, temp, code, is_day)` — pure state-setter, no oled param, no cross-view calls

**main.py** (6 lines added):
- Added: `import bootstrap` after `import text_render`
- Added: `_refresh_all(oled)` helper (6 lines) after `_draw_page_dots`, before `if __name__ == "__main__"`
- Replaced: both `weather_view.refresh(oled)` call sites with `_refresh_all(oled)`

**views/clock_view.py** (1 comment line changed):
- Line 34: "called by weather_view.refresh after each successful" → "called by main._refresh_all after each successful"

**views/system_view.py** (1 comment line changed):
- Line 32: "called by weather_view.refresh after each successful weather" → "called by main._refresh_all after each successful weather"

### Task 3 (Commit 1b47637): CLAUDE.md + STATE.md docs patch

**CLAUDE.md** (3 surgical patches):
- Import Organization `main.py` bullet: inserted `import bootstrap` between `text_render` and `time`
- Import Organization `views/weather_view.py` bullet: removed `import bootstrap` and `from views import clock_view, system_view` segments
- Component Responsibilities Application row: "weather fetch orchestration" → "composition-root fetch fan-out (`_refresh_all`)"

**.planning/STATE.md** (2 insertions):
- New cross-phase decision entry after D-45 bullet
- New row in Quick Tasks Completed table

## Public Surface Diff for views/weather_view.py

**Removed:**
```python
def refresh(oled):
    # ... called bootstrap.fetch(), updated cache, dispatched to clock_view + system_view, then rendered
```

**Added:**
```python
# Pure state-setter driven by main._refresh_all; no render, no cross-view calls.
def set_data(ip, temp, code, is_day):
    global _cached_temp, _cached_code, _cached_is_day, _cache_status, _last_refresh_ms
    # Stamp at start so transient failures don't tight-loop the scheduler —
    # a failed fetch still consumes one _REFRESH_MS window before the next try.
    _last_refresh_ms = time.ticks_ms()

    if not ip:
        _cache_status = "no_wifi"
        return
    if temp is None:
        _cache_status = "no_data"
        return

    _cached_temp = temp
    _cached_code = code
    _cached_is_day = is_day
    _cache_status = "ok"
```

**Unchanged:** `should_refresh(now_ms)`, `render(oled)`, `_center_text(oled, ...)`, all module-level constants.

## _refresh_all(oled) Body (verbatim from main.py lines 75-84)

```python
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
```

## Verification Results

All five touched Python files parse:
```
all parse OK
```

weather_view sibling/bootstrap imports (expect none):
```
(none — correct)
```

weather_view cross-view references count (expect 0):
```
0
```

main.py import bootstrap count (expect 1):
```
1
```

main.py `_refresh_all` def count (expect 1):
```
1
```

main.py `weather_view.refresh` count (expect 0):
```
0
```

main.py `_refresh_all(oled)` total occurrences (expect >=2, got 3: def + 2 call sites):
```
3
```

main.py key calls (bootstrap.fetch, set_data, set_tz_offset, set_wan_ip, weather_view.render):
```
80:    ip, temp, code, is_day, tz_offset, wan_ip = bootstrap.fetch()
81:    weather_view.set_data(ip, temp, code, is_day)
82:    clock_view.set_tz_offset(tz_offset)
83:    system_view.set_wan_ip(wan_ip)
84:    weather_view.render(oled)
99:    # for up to 20s on cold boot. weather_view.render draws from its "pending"
101:    weather_view.render(oled)
```

`weather_view.render(oled)` count in main.py (expect 2 — one pre-fetch, one inside _refresh_all):
```
2
```

clock_view comment updated (expect 1):
```
34:    # Public setter called by main._refresh_all after each successful
```

system_view comment updated (expect 1):
```
32:    # Public setter called by main._refresh_all after each successful weather
```

bootstrap.py diff lines (expect 0):
```
0
```

CLAUDE.md _refresh_all mentions (expect >=1):
```
1
```

STATE.md 260719-f0b mentions (expect >=1):
```
2
```

STATE.md main._refresh_all mentions (expect >=1):
```
2
```

**Note on plan verify script:** The T-2 verify block condition `git diff --stat bootstrap.py | grep -qv "bootstrap.py"` has a logic error — when bootstrap.py is unchanged, git diff produces empty output, and `grep -qv` on empty input exits 1 (no lines to match). Bootstrap.py is confirmed unchanged by `git diff --stat bootstrap.py | wc -l` == 0. This is a verify script bug, not a code issue.

## Deviations

None from plan intent. One verify script bug in T-2 (`git diff --stat bootstrap.py | grep -qv "bootstrap.py"` fails on empty output when file is unchanged) — worked around by checking `wc -l == 0` instead.

## Operator Notes

On-device verification (mpremote copy unchanged from previous quick task):
```bash
mpremote cp -r views/ main.py sh1107.py bootstrap.py icons.py text_render.py :
```
Then reset or run `main.py`. Expected behavior is identical to pre-refactor: boot shows "connecting...", weather fetches, carousel buttons work, clock and system views show their data. The refactor is behavior-neutral.

**.planning/codebase/*.md** files remain stale-doc debt. They were explicitly not touched here and will be regenerated by `/gsd:map-codebase` before v2 scoping.
