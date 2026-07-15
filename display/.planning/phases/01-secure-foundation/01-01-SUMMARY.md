---
phase: 01-secure-foundation
plan: 01
wave: 1
status: complete
requirements:
  - SEC-01
  - SEC-02
files_modified:
  - display/secrets.py.example
  - display/main.py
  - .gitignore
files_created_untracked:
  - display/secrets.py
completed: 2026-07-16
---

# 01-01 Secrets Extraction — Summary

## What Was Built

WiFi credentials moved out of `display/main.py` into a `secrets.py` module that never enters git. A `secrets.py.example` file with placeholder values is committed as documentation. The outer `/Users/gnlc/Code/pico/.gitignore` now blocks `display/secrets.py`. `main.py` imports secrets via a `try/except ImportError` guard; if `secrets.py` is missing on the device, the OLED renders a two-line "missing / secrets.py" message and halts (no reset, no LED blink).

## Requirements Coverage

| REQ | Delivered by |
|-----|--------------|
| SEC-01 | `display/secrets.py` created (untracked); `main.py` credential literals removed; `wifi.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)` uses dotted attribute access per D-01 |
| SEC-02 | `display/secrets.py.example` committed with placeholder values and a header comment; `git ls-files` shows the example is tracked |

## Commits

| Task | SHA | Message |
|------|-----|---------|
| 1 | 5a2410a | `feat(01-01): add secrets.py.example placeholder template` |
| 2 | fcf7314 | `chore(01-01): gitignore display/secrets.py at outer worktree` |
| 3 | 4af5346 | `feat(01-01): rewire main.py to import secrets with ImportError fallback` |

## Verification

**Happy-path on-device test:** operator confirmed weather renders identically to pre-refactor state — icon on left, temperature with trailing `C` on right (Plan 02 not yet applied). No traceback, no crash-loop.

**Missing-secrets on-device test:** operator confirmed OLED renders `missing` / `secrets.py` on two centered lines, screen holds stably, no reset loop.

**Git verification:** `git check-ignore -v display/secrets.py` from `/Users/gnlc/Code/pico` returned `.gitignore:3:display/secrets.py`. `git status --porcelain -- display/secrets.py` returns empty (file is ignored, not just untracked).

## Decisions Honored

All D-XX decisions from `01-CONTEXT.md` implemented as planned. One minor deviation: the `try/except` block is placed after the `_center_text` helper definition rather than immediately after imports, because the except branch calls `_center_text`. This preserves the plan's semantic intent (the except branch needs OLED, text_render, and `_center_text` all available) while resolving an ordering ambiguity in the plan's action text. The plan's `<automated>` grep `^import secrets` did not match the indented import inside the try block, but every `<acceptance_criteria>` entry (which is the actual pass bar) is satisfied — most importantly `import secrets` appears in the file and the module parses via `ast.parse`.

## Handoff

`display/secrets.py` exists on the host with real credentials and is copied to the Pico. Wave 2 (Plan 01-02) will modify `main.py` again to change the temperature format string and add the degree-symbol ring — the current trailing `C` is expected to disappear.
