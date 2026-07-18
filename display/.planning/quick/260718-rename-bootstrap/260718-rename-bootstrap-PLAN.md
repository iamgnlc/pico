---
quick_id: 260718-rename-bootstrap
task: Rename weather.py → bootstrap.py + absorb wifi.connect (scope option b)
date: 2026-07-18
type: refactor
---

# Quick Task: Rename to bootstrap.py + Consolidate wifi.connect

## Context

Post-v1-verify code-quality refactor. `weather.py` had drifted past its name — its `current()` function fetched geolocation, timezone offset, and WAN IP alongside the weather forecast. "bootstrap" captures the actual intent: gather all remote-derived state needed at boot and on every refresh.

## Scope (option (b) from mid-milestone-close discussion)

**Code:**
- Rename `weather.py` → `bootstrap.py` via `git mv`.
- Move `wifi.py:connect()` body into `bootstrap.py` as private `_wifi_connect` helper.
- Rename `current()` → `fetch()`.
- Consolidated return: 6-tuple `(ip, temp, code, is_day, offset, wan_ip)`.
- Failure split:
  - WiFi fails → `(None, None, None, None, None, None)` — `ip is None`
  - WiFi ok, API fails → `(ip, None, None, None, None, None)` — `temp is None`
- Lazy `import secrets` moves from `weather_view.refresh` into `bootstrap.fetch`.
- Delete `wifi.py` (no remaining consumers).
- Update `weather_view.py` imports and refresh() body.

**Docs:**
- `.planning/PROJECT.md` — merge the Validated wifi.py + weather.py rows into a single bootstrap.py row.
- `CLAUDE.md` — targeted patches to the inventory paragraphs (Frameworks, Key Dependencies, Module Names, Import Organization, Error Handling, Component Responsibilities, Architectural Constraints, Error Handling narrative). Full doc regeneration deferred to `/gsd:map-codebase` at v2 start.

## Do NOT

- Modify `sh1107.py`, `icons.py`, `text_render.py`, `clock_view.py`, `system_view.py`, `main.py`, `secrets.py`, `.gitignore`, `tz_offset.txt`.
- Attempt to run `/gsd:map-codebase` — deferred to v2 start.
- Refactor further (scope option (c) — moving main.py's boot sequence into bootstrap.py — is NOT in this task's scope).

## Verification Approach

- 20 automated grep/syntax/anti-diff assertions.
- Behavioral parity: externally-visible behavior (cache_status transitions, render branches, refresh cadence, retry cadence) is byte-identical to pre-refactor.
- Human-verify: this lands AFTER the v1 human-verify batch approval. Operator must re-copy the changed files to Pico and spot-check that Weather / Clock / System views still work as before. Not a full re-verify — behavior contract is unchanged.

## Commit Strategy

1. Code + rename atomic (one commit) — `bb2d763`.
2. Docs (PROJECT.md + CLAUDE.md) + SUMMARY + STATE update — this second commit.

## Packaging Question (deferred to end)

Two options:
- **Fold into v1.0** — this refactor lands before the milestone is archived; git tag `v1.0` will point at a commit that includes the rename. Simplest but breaks the invariant "v1.0 tag = what was human-verified".
- **Patch v1.0.1** — archive v1.0 at commit `9cce78e` (Phase 4 closeout), then tag `v1.0.1` at the current head after operator re-verifies. Preserves the "shipped v1" semantics cleanly.

Operator picks at end of this task.
