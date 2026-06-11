# Design: OM Toolkit React redesign

**Date:** 2026-06-11
**Status:** Approved (brainstormed with visual companion; user selected each
direction explicitly)

## Goal

Replace the generic Streamlit UI with a distinctive, ergonomic web app while
keeping `core/` — the pure-Python solvers — untouched. The redesign optimizes,
in order: **understanding the method** and **fast problem solving**.

The rebuild is itself a portfolio artifact: it proves the core/UI separation
was real, and adds a typed API + modern frontend to the stack story.

## Decisions made (with the user, in order)

1. **Tech scope:** full new frontend; `core/` stays. Old Streamlit `app/`
   remains until feature parity, then is retired.
2. **Stack:** React + TypeScript + Vite frontend; FastAPI backend wrapping
   `core/` as a JSON API; Plotly via react-plotly for charts (configs port
   from the existing `*_charts.py` nearly 1:1).
3. **Priorities:** teaching-first + fast solving (not demo flash, not mobile).
4. **Visual identity:** **Clean Lab** — light `#fafbfc` background, white
   cards (1px `#e6eaee` border, 12px radius, faint shadow), one teal accent
   (`#0d9488` / dark-panel variant `#2dd4bf`), near-black ink `#101418`,
   muted gray `#8a94a0`. Type: Space Grotesk (display/numbers), Inter (body),
   JetBrains Mono (data/tables). Friendly plain-language subtitles under
   every module title.
5. **Layout:** **Workbench** — dark icon rail (60px, all 6 modules + home),
   pinned input panel (~290px, white, bordered), results pane filling the
   rest. No page scrolling to re-tweak inputs.

## Architecture

```
GO_ToolKit/
├── core/                  # UNTOUCHED pure-Python solvers
├── api/                   # FastAPI
│   ├── main.py            #   mounts /api routers + serves web/dist
│   └── routers/           #   one per module (lot_sizing.py, scheduling.py, …)
├── web/                   # React + TS + Vite
│   └── src/
│       ├── modules/       #   one folder per solver module
│       ├── components/    #   DataTable, MetricCard, StepPlayer, Chart, …
│       └── lib/api.ts     #   typed API client
├── app/                   # legacy Streamlit — retired at parity
└── tests/                 # core tests (unchanged) + api/ tests
```

- **One deployable:** FastAPI serves both the API and the built React bundle;
  single uvicorn process (Render/Railway free tier). No CORS in production.
- **Thin API:** Pydantic shapes the JSON; `core/` `validate_*` functions stay
  the single source of validation truth — a handler maps `ValueError` to
  HTTP 422 with the human message, which the UI shows inline.

## Module page anatomy (validated mockup)

1. **Icon rail** — current module highlighted (teal pill). Home at top.
2. **Input panel (left, pinned):** module title + one-line plain-language
   subtitle; mode pills where a module has two tools (e.g. Dynamic / EOQ);
   editable data table; scalar inputs; example presets at the bottom.
3. **Results pane:** answer-first hero card (best result, biggest element,
   teal-tinted) → method comparison cards with % gap to best → charts →
   **teaching drawer** trigger ("Walk me through it ▶").
4. **Teaching drawer:** dark panel rendering structured solver steps as a
   navigable player (◀ ▶ buttons + keyboard arrows), highlighting affected
   chart elements per step.

## Teaching steps come from core/

Each solver gains an optional `explain=True` mode that records its own
decisions while running (e.g. Silver–Meal:
`{lot: 2, trying_period: 4, avg_before: 110, avg_after: 93.3, decision:
"extend"}`). Steps are structured data, rendered by the UI; added per module
with TDD like all core work. "Algorithms that narrate themselves" is the
teaching backbone.

## Input ergonomics

- Tables: arrow-key navigation, Tab extends rows, paste a column/range
  straight from Excel/Sheets, inline per-cell validation (red cell +
  message). No page-level error walls.
- **Live recompute** debounced ~300 ms — no Solve button.
- **Sharable URLs:** inputs serialize to the query string
  (`?d=50,60,90&s=150&h=1`) so a solved problem is a link.
- Home page = launcher: six module cards (name, the decision it answers,
  tiny preview) each with a "load example" shortcut.

## API design

One router per module; 9 endpoints total, mirroring `core/`'s public API:

```
POST /api/lot-sizing/eoq        → result + cost-curve points
POST /api/lot-sizing/dynamic    → plans, costs, steps (all 3 methods)
POST /api/line-balancing/solve  → 3 heuristics + metrics + precedence layout
POST /api/process-analysis/solve
POST /api/process-analysis/littles-law
POST /api/scheduling/dispatch   → schedules per rule + exact optimizers
POST /api/scheduling/johnson
POST /api/cellular/solve        → ROC orders, cells, efficacy
POST /api/productivity/compare
```

Each endpoint: validate via Pydantic → call core → return JSON (~10 lines).

## Testing

- `core/` tests: unchanged ground truth; new `explain` steps TDD'd the same way.
- API: FastAPI TestClient — happy path + one validation case per endpoint.
- Frontend: Vitest for data-shaping helpers; Playwright smoke per module
  (load example preset → assert the hand-traced number renders, e.g. $640).

## Rollout (one phase per PR-sized chunk)

1. **Scaffold:** web/ + api/ skeletons, shell (rail, theme, Home), deploy pipeline.
2. **Lot Sizing** end-to-end (incl. first teaching drawer) — sets the pattern.
3. **Scheduling**, 4. **Line Balancing**, 5. **Process Analysis**,
   6. **Cellular**, 7. **Productivity** — same pattern each.
8. **Retire `app/`**, update README/CLAUDE.md, redeploy.

Streamlit app keeps working until step 8.

## Out of scope

Mobile-first layouts, auth/accounts, saving problems server-side, i18n
(English only, as the course convention).
