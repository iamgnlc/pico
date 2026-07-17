# Phase 2: Carousel + Weather - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-07-17
**Phase:** 02-carousel-+-weather
**Areas discussed:** Main-loop + button-input model, View module layout, Page-dot geometry, On-view-switch refresh policy (WEATHER-04) + boot visuals

---

## Main-loop + button-input model

### Q1: Button input model

| Option | Description | Selected |
|--------|-------------|----------|
| Pin.irq() → sets flag | Each button gets `Pin.irq(trigger=Pin.IRQ_FALLING)` setting a module-level flag. Main loop reads and clears. Cannot miss presses during blocking fetches. | ✓ |
| Tight polling loop | Main loop calls `pin.value()` every N ms. Presses missed during blocking urequests. | |
| Hybrid: IRQ + polling | Both mechanisms, redundant. | |

**Rationale:** Weather fetch is blocking urequests — polling would drop presses that arrive during a 1-2 s fetch. IRQ is the only correct choice given the existing architecture.

### Q2: Debounce approach

| Option | Description | Selected |
|--------|-------------|----------|
| Software ticks_ms threshold | IRQ handler compares `time.ticks_ms()` to last-fire timestamp; ignores under ~50 ms. | ✓ |
| machine.Timer callback | One-shot Timer samples the pin after 20-50 ms. More complex state machine. | |
| Assume hardware RC filter | Trust the HAT's on-board debounce. Undocumented, risky. | |

**Rationale:** Zero-hardware, deterministic, idiomatic. Threshold tunable via one constant.

### Q3: Main-loop scheduler

| Option | Description | Selected |
|--------|-------------|----------|
| ticks_ms() poll loop | Single-threaded loop: check flag → check per-view refresh timers → sleep ~50-100 ms → repeat. | ✓ |
| machine.Timer for periodic refresh + button IRQ | Hardware Timer triggers refresh. Callback context restrictions conflict with urequests. | |
| asyncio event loop | Adds async paradigm; nothing else in codebase uses it. | |

**Rationale:** Fully synchronous codebase; adding Timer callbacks or asyncio is a paradigm shift for one screen. Poll loop is deterministic and all state stays in one place.

---

## View module layout

### Q1: File organization

| Option | Description | Selected |
|--------|-------------|----------|
| Three flat files at repo root | `weather_view.py`, `clock_view.py`, `system_view.py` alongside existing modules. Matches CLAUDE.md flat-namespace convention. | ✓ |
| Single `views.py` with three functions | Bundles three unrelated concerns; edits create cross-view diff churn. | |
| Views live in `main.py` | main.py would balloon from 57 lines to ~200+; mixes carousel state with view rendering. | |

**Rationale:** CLAUDE.md explicitly favors flat namespace. Three files stay self-contained and let each view own its module-level cache/timing state.

### Q2: View function signature

| Option | Description | Selected |
|--------|-------------|----------|
| `render(oled)` — stateless | Each view module owns its own state at module level. Carousel just calls `views[idx].render(oled)`. | ✓ |
| `render(oled, state)` — state passed in | Carousel owns a dict per view. Explicit but over-engineered without tests. | |
| Class-based `WeatherView().render(oled)` | RAM overhead; culture mismatch (codebase has zero classes except `OLED`). | |

**Rationale:** No cross-view shared state; caller shouldn't know view internals. Matches existing `_render(oled)` shape in main.py.

### Q3: Carousel state machine location

| Option | Description | Selected |
|--------|-------------|----------|
| In `main.py` | Owns `VIEWS` tuple, `_current_idx`, dispatch. Three lines of logic. | ✓ |
| Separate `carousel.py` module | New module for trivially small logic. Over-engineered. | |

**Rationale:** Orchestration is main.py's job per existing PROJECT.md architecture layer. Trivial state, doesn't merit a new file.

---

## Page-dot geometry

### Q1: Position on 128×64 display

| Option | Description | Selected |
|--------|-------------|----------|
| Bottom edge, y=60 | Rows 54-63 reserved for dots; view content in rows 0-53. Standard convention. | ✓ |
| Top edge, y=3 | Would displace the existing weather icon at y=16. | |
| No page dots — status line | Violates NAV-05 wording ("page-dot indicator"). | |

**Rationale:** Bottom placement is the conventional mobile page-indicator location. Existing Weather layout (icon at y=16, temp at y=32) fits within the reserved 0-53 rows without shifting.

### Q2: Active vs inactive style

| Option | Description | Selected |
|--------|-------------|----------|
| Filled active, hollow inactive | `fb.ellipse(cx, cy, 2, 2, 1, is_active)`. Highest contrast on monochrome OLED. | ✓ |
| Same-fill, size-based | Subtle difference on a small OLED, non-idiomatic. | |
| Filled active, line inactive | Two idioms to maintain, less readable. | |

**Rationale:** Reuses existing `fb.ellipse` idiom from `icons.py`. Filled vs hollow is the clearest binary signal on 1-bit display.

### Q3: Dot size + spacing

| Option | Description | Selected |
|--------|-------------|----------|
| r=2, 12px spacing (centers at x=52, 64, 76) | Comfortable air, clearly distinguishable. | ✓ |
| r=2, 8px spacing | Tighter, risks looking like decoration. | |
| r=3, 14px spacing | Bigger and further apart; uses more of the reserved band. | |

**Rationale:** Balanced visibility vs canvas budget. Centered on 128 px, distinct from other decorative ellipses.

---

## On-view-switch refresh policy (WEATHER-04) + boot visuals

### Q1: What does "refresh immediately on view-switch" mean?

| Option | Description | Selected |
|--------|-------------|----------|
| Redraw cached data instantly, fetch on cadence | View draws from module cache in <1 tick. 600 s cadence runs in the scheduler. | ✓ |
| Blocking re-fetch on every view-switch | Guarantees fresh data but adds 1-2 s of frozen screen — violates NAV-06. | |
| Redraw cached, then trigger fetch soon | "Nudge" pattern. Best of both but adds edge cases to the scheduler. | |

**Rationale:** NAV-06 says "redraws within one frame". Blocking on network I/O during a button press violates that requirement.

### Q2: Pre-first-fetch visual

| Option | Description | Selected |
|--------|-------------|----------|
| "..." or blank + dots | Simplest, matches existing fallback pattern. (Recommended) | |
| Show "loading" text | Static string during boot. | |
| Show a spinner/animation | Rotating shape to indicate activity. | ✓ |

**Rationale:** User picked non-recommended option. Follow-up Q4 constrained where the spinner can actually animate given `wifi.connect()` blocking.

### Q3: Clock and System stub content

| Option | Description | Selected |
|--------|-------------|----------|
| Just view name centered | "Clock", "System" text. (Recommended) | |
| View name + "coming soon" | More informative, adds dead copy for Phase 3/4. | |
| Fully blank (page dots only) | Extremely minimal. | ✓ |

**Rationale:** User picked non-recommended option. No dead copy to remove later; page dots + button response are sufficient signal that carousel works.

### Q4: Spinner visibility — follow-up on Q2

| Option | Description | Selected |
|--------|-------------|----------|
| Static "connecting..." during wifi + spinner during fetch | Two states: text while wifi.connect() blocks, spinner during weather fetch. | ✓ |
| One-frame "loading" screen, then blank until data | No animation; simpler. | |
| Spinner only during weather API fetch | Skips animation during wifi.connect() where it'd be most useful. | |

**Rationale:** Honest split between "loop is blocked in wifi.connect()" (static text only) and "loop is running the fetch state machine" (spinner can animate).

---

## Claude's Discretion

- Exact debounce ms threshold (30-80 ms band; recommend 50 ms starting point)
- Exact poll tick interval (50-100 ms band; recommend 100 ms starting point)
- Spinner shape and animation frame rate (planner + on-device visual verification)
- Whether views call `oled.show()` themselves or the main loop calls it once after page dots (recommended: main loop centralizes `show()` so dots always render on top)
- Whether the two button IRQ handlers share one debounce timestamp or each has its own (recommended: one shared, since two buttons on the same HAT won't fire within the debounce window physically)
- Weather-view refactor shape (does `weather_view` expose `tick(oled, now_ms)` or separate `should_refresh()` + `render()` — planner picks whichever fits the scheduler shape best)
- Whether to shift the Weather temp anchor from y=32 to y=26 to visually re-center within the reserved 0-53 rows (visual verify on-device)

## Deferred Ideas

- Long-press semantics (NAV-07 v2)
- Persistence of last view across reboots (NAV-08 v2 + Out of Scope)
- Distinguished error reasons in weather.py (`timeout` vs `no_connection` vs `api_error`) — future improvement per CONCERNS.md
- Response caching with age indicator ("2 hrs old") — future improvement
- Battery monitoring / power-down mode — v2, only if battery-deployed
- Non-blocking weather fetch (chunked urequests) — potential Phase 2 sub-decision if the naive approach makes the spinner too janky; fallback is a two-frame animation between fetch attempts
