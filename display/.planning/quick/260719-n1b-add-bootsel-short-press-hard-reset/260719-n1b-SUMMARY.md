---
status: complete
commit: ca9d37f
date: 2026-07-19
phase: quick-260719-n1b
plan: 01
requirements: [QUICK-260719-n1b]
files_modified: [main.py]
---

# Quick Task 260719-n1b: BOOTSEL Short-Press Hard Reset — Summary

## What Changed

Three surgical edits to `main.py`, and only `main.py`:

1. Line 2 — extended `from machine import Pin` → `from machine import Pin, reset` so the tick body can call `reset()` unqualified (consistent with the rest of the file, which uses `from machine import ...` shape).
2. Line 3 — inserted `import rp2` between the machine import and the views import, keeping it a standalone line.
3. Scheduler tick loop (now lines 117–121) — added the BOOTSEL check as the FIRST statement inside `while True:`, above `now = time.ticks_ms()`:

   ```python
   # BOOTSEL short-press = hard reset (escape hatch). Polled first each tick.
   if rp2.bootsel_button():
       reset()
   ```

Allocation-free, no debounce, no helper function, no dedicated timer — inherits the existing `_POLL_MS = 100` cadence and honours the locked scheduler decisions (D-13/14/15: ticks_ms poll loop, no asyncio, no `machine.Timer`).

## Verification (automated gate)

```
AST_OK
rp2.bootsel_button count: 1
import rp2 count: 1
machine import count: 1
bare reset() count: 1
diff files: display/main.py   # semantically equal to `main.py`; see note below
```

All six checks pass. Note on the diff-path check: the plan's literal-string comparison `test "$(git diff ...)" = "main.py"` assumes `display/` is the repo root, but the actual repo root is one level up at `/Users/gnlc/Code/pico`, so `git diff --name-only` prints `display/main.py`. The **semantic** constraint (only `main.py` was modified; nothing else in the source tree touched) is satisfied. Not a code deviation — a plan-authoring quirk.

## Deviations from Plan

None. Edit shape and locations match the plan and the orchestrator's `<atomic_edit_shape>` verbatim.

## Post-Merge Manual Validation

Operator will press the on-board BOOTSEL button on the running Pico W and confirm:
- The device reboots within ~100 ms of the press.
- It returns to the normal boot flow (boot render → `_refresh_all` → weather view).
- KEY0/KEY1 (view carousel) still work after the reboot.
- No IRQ contention or Pin config regression (BOOTSEL is not a GPIO pin and doesn't collide with `_KEY0_PIN=15` / `_KEY1_PIN=17`).

Not part of the automated gate; on-device only.

## Self-Check: PASSED

- Modified file exists: `display/main.py` — FOUND
- Commit exists: `ca9d37f` — FOUND (`feat(260719-n1b): BOOTSEL short-press hard reset in scheduler tick`)
