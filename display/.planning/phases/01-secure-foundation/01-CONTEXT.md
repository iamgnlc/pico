# Phase 1: Secure Foundation - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Land the smallest safe ship: (a) move WiFi credentials out of `main.py` into a gitignored `secrets.py`, ship a committed `secrets.py.example`, rotate exposed creds AND scrub them from git history, and (b) render the current temperature as `19°` instead of `19C`. No new views, no button handling, no clock or system view. After this phase the repo can be pushed publicly and the visible rendering nit is fixed.

**Covers:** SEC-01, SEC-02, SEC-03, WEATHER-01 (4 requirements)

</domain>

<decisions>
## Implementation Decisions

### secrets.py contract
- **D-01:** `secrets.py` is a flat-constants module — module-level assignments mirroring the current `main.py` idiom. Import pattern: `import secrets; wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)`.
- **D-02:** Only WiFi keys in v1 of `secrets.py`: `WIFI_SSID` and `WIFI_PASSWORD`. Do NOT forward-declare TZ_OFFSET or REFRESH_SECONDS — those live in `main.py` config where they already are; adding them to `secrets.py` now would be premature.
- **D-03:** `secrets.py.example` is committed with placeholder values (e.g. `WIFI_SSID = "your-ssid"`, `WIFI_PASSWORD = "your-password"`) and a short header comment pointing to the setup step.

### Missing-secrets behavior
- **D-04:** On boot, `main.py` wraps `import secrets` in a try/except ImportError. On failure, initialize the OLED and render a two-line "missing secrets" message on-screen, then halt (no infinite crash loop, no retry). Rationale: the Pico is standalone hardware — serial output isn't always attached, so the OLED is the only reliable failure channel.
- **D-05:** The halt behavior is a simple infinite `time.sleep()` loop after the error render — do NOT reset the Pico or blink the LED. Screen stays on with the message until powered off.

### Degree-symbol rendering
- **D-06:** Render `°` by drawing a small hollow ring via `fb.ellipse(x, y, 2, 2, 1, False)` — same idiom used in `icons.py:22, 27, 32`. Positioned to the top-right of the temperature digits at scale 2.
- **D-07:** The ellipse draw call lives inline in `main.py`'s existing `_render()` function, right after the `text_render.text()` call that draws the digits. Do NOT extract to `text_render.py` or create a new `views/` module in this phase — that refactor is Phase 2's job when the carousel arrives.
- **D-08:** The temperature format string changes from `"{:.0f}C".format(temp)` to `"{:.0f}".format(temp)` — the "C" is removed and replaced by the drawn ring. Ring position: to the right of the last digit, slightly above baseline, with a small horizontal gap.

### Git history remediation
- **D-09:** The outer `/Users/gnlc/Code/pico` repo is pushed to a private remote, solo — force-push is safe. `git filter-repo` (or an equivalent tool) rewrites history to scrub BOTH the WIFI_SSID string and the WIFI_PASSWORD string across all commits, replacing each with a placeholder like `REDACTED_SSID` / `REDACTED_PASSWORD`.
- **D-10:** After the rewrite, force-push all branches to the remote. User will need to re-clone or re-pull on any other machines. This should be the LAST step of the phase — everything else (secrets.py extraction, degree symbol, .gitignore updates) commits normally first, THEN history is rewritten to expunge everything in one pass.
- **D-11:** Sequence discipline: (1) confirm current WiFi credentials are already rotated / no longer valid on the router (out-of-band step the user handles), (2) commit the code changes, (3) then run the history rewrite. Never rewrite while creds are still active.

### `.gitignore` scope
- **D-12:** Since `display/` is a nested subdir inside the `pico/` worktree, add `display/secrets.py` to the OUTER `/Users/gnlc/Code/pico/.gitignore` (not a new `display/.gitignore`). Keeps ignore rules centralized where the actual `.git` directory lives.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core Value, Constraints, Key Decisions (see esp. "Move WiFi creds to gitignored secrets.py" and "Render ° via custom draw (not font swap)")
- `.planning/REQUIREMENTS.md` — SEC-01/02/03 and WEATHER-01 exact wording
- `.planning/ROADMAP.md` §"Phase 1: Secure Foundation" — Success Criteria

### Hardware and driver constraints (do not modify — read before touching any render code)
- `CLAUDE.md` §"Non-obvious SH1107 gotchas" — Four hardware traps that must be respected on any render change
- `.planning/codebase/CONCERNS.md` — Duplicates the four SH1107 gotchas plus lists WiFi-credential handling as an active concern this phase fixes

### Source files to read (Phase 1 will only modify a subset)
- `main.py` — Where WiFi creds live now (lines 9-10) and where the render happens (line 33 has the `"{:.0f}C"` format string). This is the primary file Phase 1 modifies.
- `wifi.py` — `connect(ssid, password, timeout=20)` signature — unchanged in this phase, but `main.py` needs the imported values to feed in.
- `weather.py` — Weather fetch API surface. Unchanged in this phase.
- `icons.py:22` (also `:27`, `:32`) — Canonical `fb.ellipse(...)` example patterns. The degree ring uses this same idiom.
- `sh1107.py` — Do NOT modify. Reference only for understanding what `fb.ellipse` etc. actually resolve to.
- `text_render.py` — Do NOT modify. Reference for the scale=2 rendering path the temperature text already uses.

### External
- Waveshare official SPI demo (link in `CLAUDE.md` §Reference) — Only relevant if the driver behaves unexpectedly during testing; not otherwise touched.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fb.ellipse(cx, cy, rx, ry, color, fill)`: Proven pattern in `icons.py:22, 27, 32` — used for sun body, moon body, cloud puffs. The degree ring is a direct application (`rx=ry=2`, `fill=False`).
- `_center_text(oled, s, x_center, y_center, scale)` in `main.py:16-19`: Existing helper — the current temperature text is drawn via this at `main.py:33`. It computes an `x_center - w // 2` offset; the degree ring must be placed relative to the drawn text's right edge, not the center, so it may need a companion helper or an inline computation.
- `wifi.connect(ssid, password, timeout=20)` in `wifi.py:5`: The interface Phase 1 will feed `secrets.WIFI_SSID` / `secrets.WIFI_PASSWORD` into. No changes to `wifi.py` required.

### Established Patterns
- Module-level UPPER_SNAKE_CASE constants at the top of a file (see `main.py:9-13`, `sh1107.py:6-10`, `sh1107.py:12-13` for WIDTH/HEIGHT). `secrets.py` follows this exact pattern.
- Private/internal functions prefixed with `_` (`_center_text`, `_render`, `_cmd`, `_kind`, `_sun`, ...). Any new helpers introduced in `main.py` should follow this.
- No type hints anywhere — MicroPython idiom. Do NOT introduce them.
- Format strings via `.format()` (see `main.py:33`, `weather.py:9-11`). Do NOT use f-strings — MicroPython supports them but the codebase style is `.format()`.

### Integration Points
- `main.py` imports become: `import secrets` added; `WIFI_SSID` / `WIFI_PASSWORD` module constants removed from `main.py`; call sites at `main.py:24` (`wifi.connect(WIFI_SSID, WIFI_PASSWORD)`) update to `wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)`.
- The degree ring draw happens in `main.py:_render()` immediately after the `_center_text(oled, "{:.0f}".format(temp), 88, HEIGHT // 2, scale=2)` call. Coordinates are relative to the same 88, HEIGHT//2 anchor the text uses.
- The outer `.gitignore` at `/Users/gnlc/Code/pico/.gitignore` currently contains only `.DS_Store` and `__pycache__/`. Add a `display/secrets.py` line.

</code_context>

<specifics>
## Specific Ideas

- User referenced "instead of showing temperature in format 19C I want 19 and the degree symbol". Interpretation locked: format string drops the `C`, ring symbol is drawn separately via `fb.ellipse`. Do NOT render `°C` — the C stays gone.
- Ring size: 2×2 (rx=ry=2), matching the "small dot" scale used in `icons.py`. Adjust if visual review of the physical panel shows it's too small or bleeding into the digits.
- Position: to the immediate right of the last digit, slightly above baseline (top-right superscript position). Exact offset determined empirically during implementation — a 2-3px gap right of the text, ring center a few pixels above the text baseline.

</specifics>

<deferred>
## Deferred Ideas

- Extracting the Weather rendering into its own module (`views/weather.py`) — deferred to Phase 2 when the carousel needs multiple view modules anyway.
- Extending `text_render.py` with a `degree()` helper — deferred to Phase 2 or later if a second view also needs the ring. Premature abstraction otherwise.
- Adding `TZ_OFFSET`, `REFRESH_SECONDS`, or other config to `secrets.py` — deferred. Those aren't secrets and belong in `main.py` config where they already are. Revisit only if we ever need a "config.py" split.
- Persisting the current view across reboots — already listed as Out of Scope in PROJECT.md. Not in v1 at all.

</deferred>

---

*Phase: 1-Secure Foundation*
*Context gathered: 2026-07-15*
