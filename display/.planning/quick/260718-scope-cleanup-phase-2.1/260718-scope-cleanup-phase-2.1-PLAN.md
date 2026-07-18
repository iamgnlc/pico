---
quick_id: 260718-scope-cleanup-phase-2.1
task: Narrow Phase 2.1 scope to retry-only after Plan 02.1-01 revert
date: 2026-07-18
type: docs
---

# Quick Task: Phase 2.1 Scope Cleanup

## Context

Plan 02.1-01 (location label) was reverted in commit `b8823ab` after user judgment that
the layout regressed. The revert restored `weather.py` and `weather_view.py` to Phase 2
state, but planning artifacts still describe Phase 2.1 as covering BOTH the location
label (WEATHER-08) AND the 60s fetch-retry (WEATHER-09). This cleanup narrows the phase
to just retry so Wave 2 (Plan 02.1-02) can proceed cleanly.

## Scope

Doc-only. No source-code changes (the revert handled those).

## Tasks

### Task 1 — Drop WEATHER-08 from `.planning/REQUIREMENTS.md`
- Remove the `WEATHER-08` line from the Weather View section.
- Remove the `WEATHER-08` row from the Traceability table.
- Update coverage count: `25 total → 24 total`.
- Update the footer note reflecting Phase 2.1 now covers only WEATHER-09.

### Task 2 — Narrow Phase 2.1 in `.planning/ROADMAP.md`
- Rename phase title: `Location Label + Fetch Retry` → `Fetch Retry`.
- Update Goal to describe retry only.
- Update Requirements: `WEATHER-08, WEATHER-09` → `WEATHER-09`.
- Remove Success Criterion #1 (location visible); renumber remaining.
- Delete the Wave 1 plan entry (`02.1-01-PLAN.md`).
- Promote Wave 2 to Wave 1 (or keep Wave 2 for filename stability — decide during execution).
- Update Plans count `0/2 → 0/1`.
- Update Progress table row similarly.

### Task 3 — Trim `.planning/phases/02.1-.../02.1-CONTEXT.md` to retry-only
- Drop D-26..D-30 (location decisions).
- Keep D-31..D-33 (retry decisions).
- Trim domain, canonical_refs, code_context, specifics, deferred sections to remove
  location content.
- Update phase-title header.

### Task 4 — Update `02.1-02-PLAN.md` `<interfaces>` section
- Remove `depends_on: - 02.1-01` from frontmatter (no longer valid; 02.1-01 reverted).
- Rewrite `<interfaces>` section to describe state after PLAIN Phase 2 (no `_cached_location`).
- Update mentions of "state after Plan 02.1-01" to "state after Phase 2".

### Task 5 — Update `.planning/STATE.md`
- Remove D-26..D-30 references from decisions list; keep D-31..D-33.
- Update `stopped_at` frontmatter.
- Update Phase 2.1 name in "Current focus" and "Current Position".
- Update Plans total: `8 → 7` (dropped 02.1-01).
- Update `completed_plans` if needed; recompute percent.
- Append quick task to `Quick Tasks Completed` table (create the section if missing).

## Do NOT

- Rename the phase directory (`02.1-location-label-+-fetch-retry`) — cosmetic and would
  break git blame.
- Touch `weather.py`, `weather_view.py`, or any other source file — the revert already
  handled those.
- Modify `PROJECT.md` Key Decisions table — the numbered D-26..D-33 decisions live in
  the phase CONTEXT.md, not in PROJECT.md, so nothing there is stale.

## Commit Strategy

One atomic commit per task (Tasks 1–5), then a final SUMMARY commit.
