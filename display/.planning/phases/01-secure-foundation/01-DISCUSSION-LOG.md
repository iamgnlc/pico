# Phase 1: Secure Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 1-Secure Foundation
**Areas discussed:** secrets.py shape, Missing-secrets behavior, Degree symbol drawing, Git history cleanup

---

## secrets.py shape

| Option | Description | Selected |
|--------|-------------|----------|
| Flat constants | `WIFI_SSID = "..."`, `WIFI_PASSWORD = "..."` — mirrors main.py idiom, dead-simple import. Only WiFi keys for now. | ✓ |
| Flat constants + forward-declare | Include WIFI_* plus placeholder TZ_OFFSET and REFRESH_SECONDS — all config in one file even if not yet used | |
| `get_config()` function | Returns a dict/namedtuple; caller pattern like `cfg = secrets.get_config()` — more ceremony, easier to add validation later | |

**User's choice:** Flat constants (Recommended)
**Notes:** Only WiFi keys go into `secrets.py` this phase. Non-secret config (TZ, refresh cadence) stays in `main.py`.

---

## Missing-secrets behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Render "missing secrets" on OLED | Catch ImportError in main.py, draw a clear on-screen message, halt loop — device is standalone so serial isn't always attached | ✓ |
| Hard crash with traceback | Let ImportError propagate — traceback visible via mpremote/Thonny, but blank OLED. Simpler code. | |
| Halt with LED blink | Use onboard LED to signal error — different failure mode, needs Pin("LED") pattern | |

**User's choice:** Render "missing secrets" on OLED (Recommended)
**Notes:** OLED is the only reliable failure channel on standalone hardware. Halt after render — no reboot loop.

---

## Degree symbol drawing

| Option | Description | Selected |
|--------|-------------|----------|
| `fb.ellipse` ring in main.py render | Draw a small hollow ring next to the temperature via `fb.ellipse(x, y, 2, 2, 1, False)`. Matches icons.py idiom. All rendering stays in main.py's weather-view code. | ✓ |
| Extend text_render with a ° glyph | Add a `degree(fb, x, y, scale)` helper alongside `text()` — reusable for future views. More code, better factoring. | |
| New views/weather.py module | Extract Weather rendering into its own module now, with the ° as part of that. Sets up the modular structure Phase 2 will need anyway. | |

**User's choice:** `fb.ellipse` ring in main.py render (Recommended)
**Notes:** Minimal change; deferred the module extraction and text_render helper to Phase 2 where they'll actually pay off.

---

## Git history cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-safe only | Rotate the router password (or note if it's already been rotated), untrack, .gitignore — done. History still contains old creds but they're no longer valid. | |
| Also rewrite history | Use `git filter-repo` to expunge WIFI_PASSWORD from all history + force-push. Cleaner, but rewrites shared history for the outer pico/ repo — destructive if anyone else has clones. | ✓ |
| Leave as-is (creds are fake / private) | The exposed creds aren't a real concern (personal network, or already rotated) — just add .gitignore for future safety, don't touch what's committed | |

**User's choice:** Also rewrite history
**Notes:** Chose the aggressive option. Follow-up questions locked details below.

---

## Repo scope (follow-up to git history cleanup)

| Option | Description | Selected |
|--------|-------------|----------|
| Local only, never pushed | History rewrite is completely safe — no shared history to break | |
| Pushed to my private remote, solo | Only I have clones; force-push is fine but I'll need to re-pull on other machines | ✓ |
| Shared with others / public | Force-push breaks other people's clones — need to coordinate or reconsider | |

**User's choice:** Pushed to my private remote, solo
**Notes:** Force-push safe; user will re-pull on other machines.

---

## Scrub target (follow-up to git history cleanup)

| Option | Description | Selected |
|--------|-------------|----------|
| Password only | Replace the WIFI_PASSWORD string with a placeholder across all commits — SSID stays (not sensitive on its own) | |
| Password + SSID | Scrub both credential strings — more paranoid | ✓ |
| Delete main.py from history entirely | Nuclear — remove every version of main.py that ever contained creds. Loses non-cred history too. | |

**User's choice:** Password + SSID
**Notes:** Both strings get replaced with placeholders like `REDACTED_SSID` / `REDACTED_PASSWORD`.

---

## Claude's Discretion

- Exact pixel offset of the degree ring relative to the last digit — determined empirically during implementation (roughly a 2-3px gap right of text, ring center a few pixels above the baseline). Adjust after visual review on the actual panel.
- Choice of `git filter-repo` vs BFG vs `git filter-branch` for the history rewrite — planner picks based on tool availability; all three achieve the same result.
- Exact placeholder string used in `secrets.py.example` — planner picks reasonable values (e.g. `"your-ssid"`, `"your-password"`).

## Deferred Ideas

- Extract Weather rendering into `views/weather.py` — deferred to Phase 2 when the carousel needs multiple view modules.
- Add a `degree()` helper to `text_render.py` — deferred; revisit if a second view also needs it.
- Include `TZ_OFFSET` / `REFRESH_SECONDS` in `secrets.py` — deferred; not secrets, belong in `main.py` config.
