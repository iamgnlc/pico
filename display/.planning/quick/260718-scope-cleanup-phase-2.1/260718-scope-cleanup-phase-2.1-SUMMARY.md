---
quick_id: 260718-scope-cleanup-phase-2.1
task: Narrow Phase 2.1 scope to retry-only after Plan 02.1-01 revert
date: 2026-07-18
status: complete
type: docs
---

# Quick Task Summary: Phase 2.1 Scope Cleanup

## Outcome

Phase 2.1 was renamed from "Location Label + Fetch Retry" to "Fetch Retry" across
all planning artifacts. WEATHER-08 (location label) was dropped from the v1
requirement set. Phase 2.1 now covers WEATHER-09 (60s fetch retry) only, with
a single plan (02.1-02) ready to execute.

## Files Modified

| File | Change |
|------|--------|
| `.planning/REQUIREMENTS.md` | Removed `WEATHER-08` from Weather View list, Traceability table, and coverage count (25 → 24) |
| `.planning/ROADMAP.md` | Renamed Phase 2.1, removed WEATHER-08 from Requirements + Success Criterion #1, dropped `02.1-01-PLAN.md` reference, updated plan count (0/2 → 0/1), added a footnote explaining why `02.1-02` was NOT renumbered |
| `.planning/phases/02.1-location-label-+-fetch-retry/02.1-CONTEXT.md` | Trimmed domain/decisions/canonical_refs/code_context/specifics/deferred sections; dropped D-26..D-30; kept D-31..D-33; added Historical note pointing at revert `b8823ab` |
| `.planning/phases/02.1-location-label-+-fetch-retry/02.1-02-PLAN.md` | Removed `depends_on: 02.1-01`; wave 2 → wave 1; rewrote `<interfaces>` to describe Phase 2 baseline (no `_cached_location`); updated action + verify narrative to say "Phase 2 baseline" instead of "state after Plan 02.1-01" |
| `.planning/STATE.md` | Updated frontmatter, Current focus/Position lines, dropped D-26..D-30 from decisions list, added Quick Tasks Completed table, updated Session Continuity |

## Files NOT Modified

- Source code (`weather.py`, `weather_view.py`, all others) — the revert `b8823ab` already handled these.
- `.planning/PROJECT.md` — the numbered D-26..D-33 decisions live in phase CONTEXT.md, not PROJECT.md's Key Decisions table, so nothing there was stale.
- Phase directory name (`02.1-location-label-+-fetch-retry`) — deliberately kept for git-history continuity per the plan's Do-NOT list.

## Commits

Five atomic commits under the `quick-260718-scope-cleanup` scope, one per task:

| Commit | Task |
|--------|------|
| `05113c0` | Task 1: drop WEATHER-08 from REQUIREMENTS.md |
| `f4438db` | Task 2: narrow Phase 2.1 in ROADMAP.md |
| `6f31909` | Task 3: trim CONTEXT.md to retry-only |
| `d787dd4` | Task 4: refresh 02.1-02-PLAN.md interfaces |
| *(this commit)* | Task 5 + docs: STATE.md update, PLAN.md, SUMMARY.md |

## Verification

- `grep -n "WEATHER-08" .planning/**/*.md` → no matches in REQUIREMENTS.md, ROADMAP.md, STATE.md, 02.1-CONTEXT.md, 02.1-02-PLAN.md (historical footnote references in CONTEXT.md and SUMMARY.md are intentional).
- `grep -n "_cached_location" .planning/**/*.md` → only the intentional "does NOT exist" note in 02.1-02-PLAN.md's `<interfaces>` section and this SUMMARY.
- `grep -n "Location Label" .planning/**/*.md` → only appears in historical/footnote context.
- `git status` → working tree clean after final commit.

## Next Action

Execute Plan 02.1-02 (Wave 1 — the only wave now): adds `_RETRY_MS = 60_000` to
`weather_view.py` and updates `should_refresh(now_ms)` to select the interval by
inline-reading `_cache_status`.

Command: `/gsd:execute-phase 02.1`
