---
phase: 01-secure-foundation
plan: 03
wave: 3
status: complete
requirements:
  - SEC-03
files_modified: []
completed: 2026-07-16
---

# 01-03 Git History Remediation — Summary

## What Was Built

`git filter-repo` scrubbed both credential strings from every commit in the outer `/Users/gnlc/Code/pico` repo, replacing them with `REDACTED_SSID` and `REDACTED_PASSWORD`. Local reflog and gc were expired. All branches were force-pushed to origin. No file changes — the artifact is a rewritten commit graph.

## Requirements Coverage

| REQ | Delivered by |
|-----|--------------|
| SEC-03 | Router-side rotation confirmed (out-of-band); `git filter-repo --replace-text` scrubbed history; force-push updated remote |

## Commits

No new commits — this plan mutates history rather than adding to it. Post-rewrite HEAD is `b80a9a7` (was `5060476` before rewrite; all pre-existing SHAs are also rewritten one-to-one).

## Pre-Rewrite Blast Radius

Old strings appeared in **4 commits** across the outer repo:
- `16e3a3e chore: add temperature` — original commit that introduced the creds
- `b42ca4a docs: map existing codebase` — CONCERNS.md referenced the creds
- `5b2dd06 docs(01): create phase plan` — plans referenced the scrub target
- `4af5346 feat(01-01): rewire main.py to import secrets with ImportError fallback` — removal diff still contained the strings

Total: 23 SSID hits + 21 password hits across all patch content before rewrite.

## Execution

**Tool:** `git-filter-repo 2.47.0` (installed via `brew install git-filter-repo`)

**Command:**

```bash
cd /Users/gnlc/Code/pico
git filter-repo --replace-text /tmp/pico-redact.txt --force
```

Replacements file contents (deleted after use):

```
[old SSID]==>REDACTED_SSID
[old password]==>REDACTED_PASSWORD
```

**Post-rewrite cleanup:**

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
rm /tmp/pico-redact.txt
```

**Force-push:**

Filter-repo removed the origin remote as a safety default. Re-added with:

```bash
git remote add origin https://github.com/iamgnlc/pico.git
git fetch origin
git push --force-with-lease origin --all
git push --force-with-lease origin --tags
git branch --set-upstream-to=origin/main main
```

## Verification

Local:
- `git log --all -S '[old SSID]' --oneline` → empty
- `git log --all -S '[old password]' --oneline` → empty
- `git log --all -p | grep -c '[old SSID]'` → 0
- `git log --all -p | grep -c '[old password]'` → 0
- `git log --all -p | grep -c 'REDACTED_SSID'` → 30
- `git log --all -p | grep -c 'REDACTED_PASSWORD'` → 27
- `git status` → clean, up to date with origin/main
- `/tmp/pico-redact.txt` deleted

Remote (after `git fetch origin`):
- `git log origin/main -S '[old SSID]' --oneline` → empty
- `git log origin/main -S '[old password]' --oneline` → empty
- Remote `main` at `b80a9a7`, matching local

## Notable Deviations from Plan

- **Repo was public, not private.** During Phase 1 discussion the user said the outer repo was "private, solo" — during execution it was confirmed to be a **public** repo (`github.com/iamgnlc/pico`). This means the credentials were indexed by GitHub for some period before rotation. The router-side rotation (completed before this plan ran) was the actual security mitigation; the history rewrite is cleanup for future clones and casual browsers. The old strings may still exist in GitHub's search cache and downstream mirrors — those are outside the scope of what a repo owner can control.
- **No pre-flight backup.** The plan recommended creating `/tmp/pico-pre-rewrite.bundle`; the operator chose to skip the backup and proceed. Recovery path in case of a bad rewrite would have been re-cloning from origin (before push).
- **Origin remote was removed and re-added.** `git filter-repo` removes the `origin` remote by design to prevent accidental force-push. It was re-added manually and upstream tracking was re-established after the push.

## Handoff

Phase 1 (Secure Foundation) is complete. The codebase is safe to push publicly and the temperature renders with a degree symbol. Next: Phase 2 — two-button carousel and polished Weather view (NAV-01..06, WEATHER-02..05).
