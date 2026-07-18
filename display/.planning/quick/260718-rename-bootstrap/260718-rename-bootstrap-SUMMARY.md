---
quick_id: 260718-rename-bootstrap
task: Rename weather.py → bootstrap.py + absorb wifi.connect (scope option b)
date: 2026-07-18
status: complete
type: refactor
---

# Quick Task Summary: Rename to bootstrap.py + Consolidate wifi.connect

## Outcome

`weather.py` renamed to `bootstrap.py` with `wifi.py:connect()` merged in as a private helper. Public API is now a single `bootstrap.fetch()` returning a 6-tuple `(ip, temp, code, is_day, offset, wan_ip)` — one round-trip encompasses WiFi + geolocation + weather + timezone + WAN IP.

**Externally-visible behavior is unchanged.** The refactor is purely structural: same cache_status transitions, same render branches, same refresh cadence, same retry cadence, same D-33 stamp-at-start, same D-31 predicate shape.

## Files Modified

| File | Change |
|------|--------|
| `weather.py` | RENAMED to `bootstrap.py` (via `git mv`). Contents rewritten to add `_wifi_connect` helper, rename `current()` → `fetch()`, consolidate WiFi + API calls, expand return to 6-tuple. |
| `wifi.py` | DELETED. Body absorbed into `bootstrap._wifi_connect`. |
| `weather_view.py` | Imports simplified: `import wifi` + `import weather` → `import bootstrap`. `import secrets` removed (bootstrap owns it now). `refresh()` body simplified from 10 lines to 5 (one `bootstrap.fetch()` call replaces `wifi.connect + weather.current` sequence). Two failure branches preserved (no_wifi via `if not ip`; no_data via `if temp is None`). |
| `.planning/PROJECT.md` | Validated-requirements list: merged the wifi.py + weather.py rows into a single bootstrap.py row. |
| `CLAUDE.md` | Targeted inventory patches: Frameworks list, Key Dependencies, Module Names line, Import Organization, Error Handling example, Component Responsibilities table, Architectural Constraints threading line, Error Handling narrative. Rest of the file's descriptive prose is intentionally left with historical wifi.py/weather.py references — full regeneration deferred to `/gsd:map-codebase` at v2 start. |
| `.planning/STATE.md` | Frontmatter + Session Continuity refreshed; Quick Tasks Completed table gains new row. |

## Files NOT Modified

- `sh1107.py`, `icons.py`, `text_render.py`, `clock_view.py`, `system_view.py`, `main.py`, `secrets.py`, `.gitignore`, `tz_offset.txt` — anti-diff verified.
- `.planning/REQUIREMENTS.md` — no requirement wording referenced module names.
- `.planning/codebase/*.md` (STACK.md, STRUCTURE.md, ARCHITECTURE.md, CONVENTIONS.md, INTEGRATIONS.md, CONCERNS.md, TESTING.md) — INTENTIONALLY NOT UPDATED. All 7 files reference `weather.py` or `wifi.py`. Full sweep is deferred to `/gsd:map-codebase` at v2 start. This is the v1 archive's frozen state; sweeping it now would just create work that will be redone.

## Automated Verification (all 20 pass)

| # | Check | Result |
|---|-------|--------|
| 1 | `bootstrap.py` syntax | ok |
| 2 | `weather_view.py` syntax | ok |
| 3 | `_wifi_connect` signature | ok |
| 4 | `fetch()` signature | ok |
| 5 | Lazy `import secrets` inside bootstrap | ok |
| 6 | WiFi-fail return: 6 Nones | ok |
| 7 | API-fail return: `(ip, None, None, None, None, None)` | ok |
| 8 | Success return: `(ip, temp, code, is_day, offset, wan_ip)` | ok |
| 9 | ip-api URL includes `?fields=lat,lon,offset,query` | ok |
| 10 | `import wifi` gone from weather_view | ok |
| 11 | `import weather` gone from weather_view | ok |
| 12 | `import secrets` gone from weather_view (moved to bootstrap) | ok |
| 13 | `import bootstrap` present in weather_view | ok |
| 14 | `bootstrap.fetch()` call in refresh | ok |
| 15 | 6-tuple unpack: `ip, temp, code, is_day, tz_offset, wan_ip` | ok |
| 16 | `no_wifi` branch on `if not ip:` | ok |
| 17 | `no_data` branch on `if temp is None:` | ok |
| 18 | `wifi.py` deleted from disk | ok |
| 19 | `weather.py` renamed away (no longer on disk) | ok |
| 20 | Zero diff on 7 unchanged source files | ok |

## Commits

| Commit | Description |
|--------|-------------|
| `bb2d763` | refactor: rename weather.py → bootstrap.py; consolidate wifi.connect into fetch() |
| *(this commit)* | docs(quick-260718-rename-bootstrap): PROJECT + CLAUDE patches; PLAN + SUMMARY; STATE update |

## Human-Verify Recommendation

Full v1 human-verify batch is already approved (Phases 1..4). This refactor preserves behavior — Weather / Clock / System views all read from the same cache state populated by the same 6-tuple, now via `bootstrap.fetch()`. Recommended spot-check on the Pico:

1. `mpremote fs rm :weather.py :wifi.py` (clean up stale files)
2. `mpremote cp bootstrap.py weather_view.py :`
3. `mpremote reset`
4. Confirm Weather view shows icon + temp; Clock shows local time (after ~10 min for first fetch); System shows SSID + WAN IP + bars.

If everything works: reply `re-verified` and confirm packaging choice.

## Packaging Decision (pending)

Two options for how to wrap this into the milestone archive:

- **(A) Fold into v1.0** — this refactor is included in the v1.0 git tag. Simplest, but the v1.0 tag will point at code that wasn't in the shipped-on-device state at the moment of the human-verify approval.
- **(B) Patch v1.0.1** — tag v1.0 at commit `9cce78e` (Phase 4 closeout — the state operator verified). This refactor becomes v1.0.1, tagged after operator's re-verify. Cleaner history: v1.0 tag = verified-on-device state; v1.0.1 = refactor patch.

Operator to decide before archiving.
