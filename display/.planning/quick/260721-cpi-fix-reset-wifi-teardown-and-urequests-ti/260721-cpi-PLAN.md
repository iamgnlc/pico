---
phase: quick-260721-cpi
plan: 01
quick_id: 260721-cpi
type: execute
wave: 1
depends_on: []
files_modified:
  - main.py
  - bootstrap.py
autonomous: true
requirements:
  - QUICK-260721-cpi
tags:
  - bootstrap
  - main
  - reset
  - wifi
  - reliability

must_haves:
  truths:
    - "After a BOOTSEL short-press, the post-reset boot no longer hangs on 'connecting...' — the CYW43 wireless chip is torn down cleanly before machine.reset() so the next boot's _wifi_connect starts from a known-good state."
    - "The BOOTSEL wait-for-release loop from quick 260719-n1b is preserved unchanged, and machine.reset() is always called after the button release even if the WLAN teardown itself raises."
    - "Both urequests.get() calls in bootstrap.fetch() carry a bounded socket-level timeout (recommended 10 s each) so a wedged DNS / TCP / TLS / recv can no longer block the render loop forever."
    - "A urequests timeout falls into the existing outer `except Exception:` in fetch() and returns the (ip, None, None, None, None, None) shape — the caller sees the same 'no_data' / 'stale' semantics as any other API failure (per the 260720-x55 stale-cache fix)."
    - "No file outside main.py and bootstrap.py changes. sh1107.py, icons.py, text_render.py, and every view module stay byte-identical."
    - "Public function signatures are unchanged: bootstrap.fetch() still returns a 6-tuple, bootstrap._wifi_connect(ssid, password, timeout=30) still returns str-or-None, and no new public helpers are added."
  artifacts:
    - path: "main.py"
      provides: "BOOTSEL branch now performs WLAN.disconnect() + WLAN.active(False) inside a try/except before calling reset()"
      contains: "wlan.disconnect"
    - path: "bootstrap.py"
      provides: "Both urequests.get() calls carry a socket-level timeout (kwarg or setdefaulttimeout fallback)"
      contains: "timeout"
  key_links:
    - from: "main.py BOOTSEL branch"
      to: "bootstrap._wifi_connect on next boot"
      via: "post-reset CYW43 comes up in a clean not-associated state"
      pattern: "wlan.active\\(False\\)"
    - from: "bootstrap.fetch urequests calls"
      to: "views/weather_view.set_data (via main._refresh_all)"
      via: "bounded exception on timeout → (ip, None, ...) → set_data flips _cache_status to 'no_data' or 'stale'"
      pattern: "_cache_status = \"stale\""
---

<objective>
Fix the "post-BOOTSEL boot hangs forever on 'connecting...'" bug. Two surgical, additive changes:

1. **main.py BOOTSEL branch** — before calling `machine.reset()`, tear the CYW43 station interface down cleanly (`disconnect()` + `active(False)`) so the post-reset boot does not inherit a half-alive association state that later wedges `urequests`.

2. **bootstrap.py `urequests.get()` calls** — add a bounded socket-level timeout (recommended **10 s** per call, sanctioned band 5-15 s) to both `urequests.get()` sites so a hung DNS / TCP / TLS handshake / recv can no longer block the render loop indefinitely. The existing outer `except Exception:` inside `fetch()` already turns any resulting timeout into the standard `(ip, None, ...)` return, which downstream reaches `views/weather_view.set_data` and flips `_cache_status` to `"no_data"` (cold cache) or `"stale"` (warm cache, per 260720-x55) — a bounded, recoverable failure instead of an unbounded hang.

Purpose: Operator reports that after pressing BOOTSEL (which invokes `machine.reset()` via 260719-n1b), the display sometimes stays on "connecting..." **forever** — not the ~41 s worst case introduced by 260721-c43. Root cause is a soft-reset on the RP2040 with the CYW43 wireless chip on a separate power/reset domain: the chip retains association state across the RP2040 reset, `_wifi_connect`'s fast-path `if wlan.isconnected(): return` returns immediately with a truthy IP, and `urequests.get()` — which has no default socket timeout in MicroPython — then blocks forever waiting on a wedged socket.

Output: A modified `main.py` and `bootstrap.py`. Every other file in the repo is byte-identical.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md
@main.py
@bootstrap.py
@views/weather_view.py

<interfaces>
<!-- Contracts the executor must preserve. Extracted verbatim from the codebase. -->

Current main.py BOOTSEL branch (lines 117-125) — the ONLY block in main.py that changes:
```python
while True:
    # BOOTSEL short-press = hard reset. Wait-for-release avoids the boot-ROM mass-storage trap.
    if rp2.bootsel_button():
        # BOOTSEL is also read by the boot ROM at reset time — if still held
        # when reset() fires, the Pico enters USB mass-storage mode instead
        # of rebooting into main.py. Wait for release before resetting.
        while rp2.bootsel_button():
            pass
        reset()
```

Current main.py imports (lines 1-7) — `network` is NOT currently imported here; it must be added:
```python
from sh1107 import OLED, WIDTH, HEIGHT
from machine import Pin, reset
import rp2
from views import weather_view, clock_view, system_view
import text_render
import bootstrap
import time
```

Current bootstrap.py urequests call sites (lines 51-69) — the ONLY block in bootstrap.py that changes:
```python
try:
    # ip-api's default response omits `offset` and `query`; request both
    # explicitly along with lat/lon. Without ?fields=..., the extended
    # fields come back as None and downstream setters no-op.
    r = urequests.get("http://ip-api.com/json/?fields=lat,lon,offset,query")   # line 55 — needs timeout
    loc = r.json()
    r.close()
    offset = loc.get("offset")
    wan_ip = loc.get("query")
    url = ("https://api.open-meteo.com/v1/forecast"
           "?latitude={}&longitude={}"
           "&current=temperature_2m,weather_code,is_day").format(
        loc["lat"], loc["lon"])
    r = urequests.get(url)                                                       # line 64 — needs timeout
    cur = r.json()["current"]
    r.close()
    return ip, cur["temperature_2m"], cur["weather_code"], cur["is_day"], offset, wan_ip
except Exception:
    return ip, None, None, None, None, None
```

The outer `except Exception:` at line 68 is the safety net that will catch any timeout — do NOT change it.

Consumer of the (ip, None, ...) shape (views/weather_view.py:47-60):
```python
def set_data(ip, temp, code, is_day):
    ...
    if not ip:
        _cache_status = "no_wifi"
        return
    if temp is None:
        _cache_status = "no_data" if _cached_temp is None else "stale"
        return
```

Coexistence with 260720-x55 (stale-cache fallback) — any timeout that fires now becomes
`(ip, None, ...)` → `set_data(ip, None, ...)` → `_cache_status = "stale"` if warm cache OR
`"no_data"` if cold. The stack degrades gracefully instead of hanging.

Coexistence with 260721-c43 — this plan does NOT change `_wifi_connect`. Post-fix worst case
for a full failed fetch: 30 s (wifi initial) + 1 s (settle) + 10 s (wifi retry) + 10 s (ip-api
timeout) + 10 s (open-meteo timeout) = **61 s**. Bounded and acceptable. Pre-fix: unbounded.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Clean CYW43 teardown in BOOTSEL branch + bounded urequests timeouts</name>
  <files>main.py, bootstrap.py</files>
  <action>
Both edits are trivially small and are grouped into one atomic task. Keep the diff surgical — only the two blocks called out below change; the rest of both files stays byte-identical.

**Edit A — main.py (BOOTSEL branch, currently lines 117-125):**

1. Add `import network` to the imports at the top of main.py. Place it alongside the other stdlib imports — for example on its own line after `import time`, or grouped with `from machine import Pin, reset` and `import rp2`. This is the smallest possible diff to make WLAN available at the reset site; `network` is already imported by `bootstrap.py` and `views/system_view.py`, so the marginal RAM/import cost is essentially zero.

2. Inside the existing BOOTSEL branch, AFTER the wait-for-release loop (`while rp2.bootsel_button(): pass`) and BEFORE `reset()`, insert a WLAN teardown wrapped in a `try/except Exception: pass`. Semantics required:
   - Get a handle: `wlan = network.WLAN(network.STA_IF)` (local variable — do NOT introduce a module-level global).
   - Call `wlan.disconnect()` to clear any queued/in-flight association.
   - Call `wlan.active(False)` to power the interface down cleanly.
   - Wrap the whole three-line teardown inside `try: ... except Exception: pass`. Rationale: if the WLAN interface is in a weird state (mid-transition, driver error), the teardown itself might raise. We MUST still call `reset()` afterwards — never let a shutdown-time exception stall the reset the operator asked for.

3. The `reset()` call MUST remain UNCONDITIONAL after the try/except block. Do NOT gate it behind teardown success. Do NOT move it inside the try. Do NOT add an `else` branch.

4. The wait-for-release loop from quick 260719-n1b (`while rp2.bootsel_button(): pass`) MUST remain unchanged — it prevents the boot-ROM USB mass-storage trap and is not the subject of this fix.

5. Add a one- to three-line inline comment above the try block explaining WHY: "Clean CYW43 shutdown so the post-reset boot's _wifi_connect starts from a known-good state, not a retained-associated wedge that hangs urequests." (Executor may paraphrase; the point is future readers understand the intent — this is not a common idiom.)

6. Do NOT modify any other part of main.py. Do NOT touch `_refresh_all`, the IRQ handlers, the scheduler tick body, `_center_text`, or the `if __name__ == "__main__":` boot sequence. `git diff main.py` should show only the import addition and the BOOTSEL branch body.

Referential shape (semantics only — executor writes actual code following existing style):
```
if rp2.bootsel_button():
    while rp2.bootsel_button():
        pass
    # Clean CYW43 shutdown so the post-reset boot's _wifi_connect starts from a
    # known-good state, not a retained-associated wedge that hangs urequests forever.
    try:
        _wlan = network.WLAN(network.STA_IF)
        _wlan.disconnect()
        _wlan.active(False)
    except Exception:
        pass
    reset()
```

**Edit B — bootstrap.py (both `urequests.get()` calls):**

**Primary path (strongly preferred):** Add a `timeout=10` kwarg to BOTH `urequests.get()` calls inside `fetch()`:
- Line 55: `r = urequests.get("http://ip-api.com/json/?fields=lat,lon,offset,query", timeout=10)`
- Line 64: `r = urequests.get(url, timeout=10)`

Numeric value: **10 seconds** for each call. Sanctioned band: 5-15 s. Rationale — both ip-api.com and api.open-meteo.com normally respond in well under 2 s; 10 s comfortably covers pathological latency without freezing the UI, and the resulting bounded exception path is already handled by the outer `try/except Exception:` at line 68.

**Fallback path (only if primary rejected by the runtime):** MicroPython's `urequests` accepts `timeout=` as a kwarg on modern builds (roughly MP ≥ v1.20). If for any reason the executor observes on-device that `timeout=` is not accepted (`TypeError` on `urequests.get(..., timeout=10)`), do NOT silently drop the timeout — the fix would be defeated. Instead, apply the fallback:

- At the top of `fetch()`, BEFORE the `import secrets` line but AFTER the function header, add:
  ```python
  import socket
  socket.setdefaulttimeout(10)
  ```
- Remove the `timeout=10` kwarg from both `urequests.get()` calls (they revert to their current form).
- Leave a one- to two-line inline comment noting that this is a socket-level fallback because the local urequests build did not accept `timeout=`.

DEFAULT DECISION for the executor: use the **primary path** (the `timeout=10` kwarg). Only switch to the fallback if the executor has direct evidence — either from a runtime error on-device or from checking the local MicroPython urequests source — that the kwarg is rejected. Do NOT preemptively use the fallback.

Preserved behaviors (do NOT regress ANY of these):
- `bootstrap.fetch()` still returns a 6-tuple `(ip, temp, code, is_day, offset, wan_ip)`.
- The outer `except Exception:` at line 68 still catches every failure and returns `(ip, None, None, None, None, None)`. Do NOT tighten this to a specific exception class — it MUST continue to catch timeout exceptions (which in MicroPython land can be `OSError`, `socket.timeout`, or a `urequests`-specific error depending on the build).
- The `_wifi_connect` fast path is untouched (this task does not modify `_wifi_connect`).
- `secrets` lazy-import behavior is untouched.
- The 6-tuple field ordering, JSON keys, URL strings, and `r.close()` calls are all preserved.
- The `?fields=lat,lon,offset,query` querystring on the ip-api URL is preserved.

Structural notes:
- Do NOT add any print / log / debug statement.
- Do NOT introduce a new module-level constant for the timeout — inline `10` is fine and matches the file's existing style (see `time.sleep(1)` and the raw `range(10)` in `_wifi_connect`).
- Do NOT touch the module-level imports (`network`, `time`, `urequests`) unless using the fallback, in which case exactly one added import inside `fetch()` (`import socket`) is permitted.
- Do NOT touch anything in `_wifi_connect`.

**Combined scope guard:** After both edits, `git diff --name-only` MUST show exactly `bootstrap.py` and `main.py` — nothing else. sh1107.py, icons.py, text_render.py, and every file under views/ must be byte-identical.
  </action>
  <verify>
    <automated>
# 1. Both edited files still parse as valid Python.
python3 -c "import ast, pathlib; ast.parse(pathlib.Path('main.py').read_text()); ast.parse(pathlib.Path('bootstrap.py').read_text())"

# 2. main.py now imports network (checked outside comments so header prose can't self-invalidate the gate).
grep -v '^\s*#' main.py | grep -c "^import network"                 # expect >= 1

# 3. main.py BOOTSEL branch contains the WLAN teardown sequence.
grep -v '^\s*#' main.py | grep -c "network.WLAN(network.STA_IF)"    # expect >= 1
grep -v '^\s*#' main.py | grep -c "wlan.disconnect"                 # expect >= 1  (case-insensitive-friendly local var still contains 'wlan')
grep -v '^\s*#' main.py | grep -c "wlan.active(False)"              # expect >= 1

# 4. Teardown MUST be wrapped in try/except so reset() is guaranteed.
grep -v '^\s*#' main.py | grep -cE "except Exception:"              # expect >= 1

# 5. reset() is still called from the BOOTSEL branch.
grep -v '^\s*#' main.py | grep -c "reset()"                         # expect >= 1 (imported from machine)

# 6. BOOTSEL wait-for-release loop from 260719-n1b is still present (regression guard).
grep -v '^\s*#' main.py | grep -cE "while rp2\.bootsel_button\(\):" # expect >= 2 (outer test + wait-for-release)

# 7. bootstrap.py: both urequests.get() calls carry a bounded timeout (5-15 s band).
#    Primary path: kwarg on the call itself.
#    Fallback path: socket.setdefaulttimeout(...) at the top of fetch().
#    At least ONE of the two patterns MUST match — otherwise the fix is missing.
PRIMARY=$(grep -v '^\s*#' bootstrap.py | grep -cE "urequests\.get\([^)]*timeout=(5|6|7|8|9|1[0-5])[^0-9]")
FALLBACK=$(grep -v '^\s*#' bootstrap.py | grep -cE "socket\.setdefaulttimeout\((5|6|7|8|9|1[0-5])\)")
test "$PRIMARY" -ge 2 || test "$FALLBACK" -ge 1

# 8. Regardless of which path the executor picked, BOTH urequests.get() call sites must still exist.
grep -c "urequests.get(" bootstrap.py                               # expect >= 2

# 9. bootstrap.fetch() shape untouched — outer except and both failure returns still present.
grep -c "except Exception:" bootstrap.py                            # expect >= 1
grep -c "return ip, None, None, None, None, None" bootstrap.py      # expect >= 1
grep -c "return None, None, None, None, None, None" bootstrap.py    # expect >= 1
grep -c "if not ip:" bootstrap.py                                   # expect >= 1

# 10. _wifi_connect signature unchanged (regression guard against accidentally editing 260721-c43's work).
grep -v '^\s*#' bootstrap.py | grep -cE "def _wifi_connect\(ssid, password, timeout=30\):"   # expect exactly 1

# 11. bootstrap.py module-level imports untouched except (fallback path) an in-function `import socket` inside fetch().
grep -cE "^import (network|time|urequests)$" bootstrap.py           # expect exactly 3

# 12. Scope guard: only main.py and bootstrap.py touched. Nothing else.
DIFF="$(git diff --name-only | sort | tr '\n' ' ' | sed 's/ *$//')"
test "$DIFF" = "bootstrap.py main.py"
    </automated>
    <human-check>
On-device verification (operator, after re-flashing BOTH main.py and bootstrap.py to the Pico):

1. **The bug this fix targets — post-BOOTSEL hang (the critical scenario):**
   - Boot the Pico normally and let it reach the Weather view with a real temperature + icon.
   - Press and release the BOOTSEL button (short press, well under 1 s).
   - Expected: display briefly clears, "connecting..." shows for a few seconds, then the Weather view repaints with fresh data. Total time from press to paint: comparable to a cold boot on a healthy network (well under 30 s), NOT forever.
   - Regression check (this is the actual bug): the "connecting..." screen must NOT stay up indefinitely. If it does, the WLAN teardown did not execute or urequests is still hanging.

2. **Repeated BOOTSEL cycles (soak test):**
   - Press BOOTSEL 5-10 times in a row (waiting for each cycle to complete). This exercises the teardown-then-reset path many times over.
   - Expected: every cycle recovers to a real Weather view. No cycle should hang on "connecting...".

3. **urequests timeout path (deliberately induce a network stall):**
   - With the Pico running, briefly block outbound HTTP on the router (or unplug the router's WAN uplink) so DNS/TCP still work locally but external requests can't complete.
   - Wait through one refresh cycle (up to 60 s while `_cache_status != "ok"`).
   - Expected: display shows "stale" (if a previous fetch had populated the cache — icon + old temp remain visible) or "no data" (cold cache), within roughly 10-20 s of the fetch starting. The display MUST NOT hang forever on "connecting..." after a scheduler-tick refresh.
   - After restoring uplink, the next refresh cycle should return the display to "ok".

4. **Cold-boot happy path (regression guard — should be unchanged):**
   - Power-cycle the Pico with a healthy WiFi environment.
   - Expected: "connecting..." → weather view with real data within seconds (well under 30 s), same as before this fix.

5. **Mid-session refresh happy path (regression guard — should be unchanged):**
   - Watch the display through 2-3 scheduled 600 s refresh cycles.
   - Expected: refreshes remain near-instant. No "connecting..." flash. The `_wifi_connect` fast path (already-connected) is untouched by this plan.

6. **View carousel (KEY0/KEY1) sanity:**
   - Cycle through Weather → Clock → System with KEY0/KEY1.
   - Expected: all three views render correctly. No regression in view-switch responsiveness.
    </human-check>
  </verify>
  <done>
- main.py has `import network` in its module-level imports.
- main.py BOOTSEL branch contains a `try: wlan = network.WLAN(network.STA_IF); wlan.disconnect(); wlan.active(False) except Exception: pass` block after the wait-for-release loop and BEFORE the unconditional `reset()` call.
- The 260719-n1b wait-for-release loop is present and unchanged.
- bootstrap.py has bounded socket-level timeouts on BOTH urequests.get() calls — either via `timeout=10` kwarg (primary, preferred) or via `socket.setdefaulttimeout(10)` inside `fetch()` (fallback, only if the kwarg is rejected on-device).
- bootstrap._wifi_connect from 260721-c43 is byte-identical.
- bootstrap.fetch() 6-tuple contract and outer `except Exception:` are byte-identical.
- All automated `verify` grep + syntax + scope gates pass.
- `git diff --name-only` returns exactly `bootstrap.py main.py` (sorted).
- Operator confirms on-device that BOOTSEL short-press no longer produces the forever-"connecting..." hang, and that all four regression scenarios in `<human-check>` pass.
  </done>
</task>

</tasks>

<verification>
Static/byte-level checks the executor MUST run before declaring done:

- `python3 -c "import ast, pathlib; ast.parse(pathlib.Path('main.py').read_text()); ast.parse(pathlib.Path('bootstrap.py').read_text())"` — both files parse.
- All 12 grep + test gates from Task 1 `<verify><automated>` pass.
- `git diff --name-only | sort` returns exactly `bootstrap.py\nmain.py`.

On-device verification is the operator's responsibility per the `<human-check>` block above. This repo has no host-side runtime tests (CLAUDE.md is explicit: everything runs on the Pico via `mpremote`/Thonny).
</verification>

<success_criteria>
- Two edits land as one atomic commit: (a) main.py BOOTSEL branch cleanly tears down the CYW43 interface before calling `reset()`, and (b) bootstrap.py's two `urequests.get()` calls carry a bounded socket-level timeout (10 s recommended, 5-15 s sanctioned).
- The primary path (kwarg on `urequests.get()`) is preferred; the `socket.setdefaulttimeout()` fallback is used only if the kwarg is demonstrably rejected on-device.
- All automated grep + syntax + scope-guard checks pass.
- No file outside `main.py` and `bootstrap.py` is modified.
- Public function signatures are untouched: `bootstrap.fetch()` still returns a 6-tuple; `bootstrap._wifi_connect(ssid, password, timeout=30)` still has its 260721-c43 signature.
- Operator, after re-flashing, confirms:
  - BOOTSEL short-press no longer produces the forever-"connecting..." hang (the target bug).
  - Cold-boot on a healthy network is not slower than before this fix.
  - Mid-session refreshes remain near-instant.
  - Deliberate network stalls now degrade gracefully to "stale" or "no data" instead of hanging.
- Coexistence with 260720-x55 and 260721-c43 is preserved: `_cache_status` transitions still produce "no_wifi" on true WiFi failure, "no_data" on cold-cache API failure, and "stale" on warm-cache API failure. Post-fix worst-case wall-clock for a full failed refresh is bounded at ~61 s (30 s wifi initial + 1 s settle + 10 s wifi retry + 10 s ip-api + 10 s open-meteo). Pre-fix: unbounded.
</success_criteria>

<output>
Create `.planning/quick/260721-cpi-fix-reset-wifi-teardown-and-urequests-ti/260721-cpi-SUMMARY.md` when done, capturing:
- Which urequests timeout path was used (primary `timeout=` kwarg, or fallback `socket.setdefaulttimeout`).
- The numeric timeout value chosen (recommended 10 s; sanctioned band 5-15 s).
- Confirmation that the WLAN teardown lives inside a `try/except Exception: pass` and that `reset()` is still unconditional.
- Confirmation of every automated verify gate.
- Operator's on-device outcome from the six `<human-check>` scenarios.
</output>
