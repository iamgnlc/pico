---
status: complete
commit: ca9d37f
followup_commit: b678517
date: 2026-07-19
phase: quick-260719-n1b
plan: 01
requirements: [QUICK-260719-n1b]
files_modified: [main.py]
on_device_verified: true
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

## On-Device Validation

Initial smoke test surfaced a boot-ROM mode-selection trap not caught by the automated gate:

**Symptom:** Pressing BOOTSEL blanked the OLED but the device never rebooted into `main.py`. A `RPI-RP2` USB drive appeared on the host laptop instead.

**Root cause:** BOOTSEL is dual-purpose on RP2040 — readable at runtime via `rp2.bootsel_button()` (the runtime path we added), but ALSO checked by the Pico's boot ROM at reset time. When `machine.reset()` fired while the operator was still holding the button, the boot ROM saw BOOTSEL held and diverted into USB mass-storage mode instead of rebooting into MicroPython.

**Fix (commit `b678517`):** Busy-wait for BOOTSEL release before calling `reset()`:

```python
        # BOOTSEL short-press = hard reset. Wait-for-release avoids the boot-ROM mass-storage trap.
        if rp2.bootsel_button():
            # BOOTSEL is also read by the boot ROM at reset time — if still held
            # when reset() fires, the Pico enters USB mass-storage mode instead
            # of rebooting into main.py. Wait for release before resetting.
            while rp2.bootsel_button():
                pass
            reset()
```

The release-wait is NOT a debounce — the locked "any press = hard reset" semantics from the original plan still hold. It's strictly boot-ROM-mode avoidance.

**Post-fix validation:** Operator re-flashed and confirmed the intended behaviour:
- BOOTSEL press → OLED blanks briefly → Pico reboots → normal boot flow resumes (boot render → `_refresh_all` → weather view)
- No `RPI-RP2` drive appears on the host
- KEY0/KEY1 (view carousel) still work after the reboot
- No regression in weather refresh / clock tick / system view rendering

## Self-Check: PASSED

- Modified file exists: `display/main.py` — FOUND
- Original commit: `ca9d37f` (`feat(260719-n1b): BOOTSEL short-press hard reset in scheduler tick`)
- Follow-up fix commit: `b678517` (`fix(bootsel): wait for BOOTSEL release before reset() to avoid boot-ROM mass-storage trap`)
- On-device verified: yes (operator, 2026-07-19)
