# Plan: Professional extensions to the OM solvers (2026-06-13)

## Goal & theme

Every solver today is **deterministic and frictionless** — no shortages,
infinite capacity, no job priorities, no equipment-loss accounting. This batch
relaxes those idealizations toward what a planner actually accounts for:
**costs, constraints, priorities, and recognized industry KPIs.** Four features,
one per module that benefits most, each built full-stack (core → hand-traced
tests → API → React view) like the rest of the app.

Priority order #1 is still **learning**: each algorithm must stay explainable in
an interview. So every feature gets a worked hand-trace in the test docstring
(the project validation rule), and we prefer exact, narratable methods over
black-box optimization.

## Features

### 1. OEE — Overall Equipment Effectiveness (Productivity)
The most recognized KPI in operations. `OEE = Availability × Performance × Quality`.
- **Inputs:** planned production time, downtime, ideal cycle time, total count, good count.
- **Derived:** run time = planned − downtime; Availability = run/planned;
  Performance = (ideal cycle × total count) / run time; Quality = good/total.
- **core/productivity/oee.py** — `overall_equipment_effectiveness(...) -> dict`
  with the three factors + OEE, plus `oee_steps(...)` narrating each factor.
  Validation: each input positive, downtime < planned, good ≤ total,
  performance ≤ 1 (ideal cycle can't beat run time unless data is wrong → clamp? no,
  surface it: if performance > 1 the ideal cycle time is too low for the count).
- **Hand trace:** planned 420 min, downtime 30 → run 390; ideal cycle 1.0 min,
  total 360 → performance 360/390 = 0.9231; good 340/360 = 0.9444;
  availability 390/420 = 0.9286; OEE = 0.9286·0.9231·0.9444 = 0.8095.
- **API:** `POST /api/productivity/oee`.
- **UI:** new `OeeView.tsx` tab on ProductivityPage + a small drawer narrating
  the three factors; preset from the hand trace.

### 2. WSPT + Moore's algorithm (Scheduling)
Tardiness metrics already exist; the gap is **priorities** and a **due-date-exact** rule.
- **Job weights:** add optional `weight: float = 1.0` to `Job` (models.py).
- **WSPT rule:** sort by `processing_time / weight` ascending — minimizes total
  weighted completion time (Smith's rule). Add to `RULES`.
- **Moore's algorithm:** `moore_sequence(jobs) -> list[Job]` — minimizes the
  NUMBER of tardy jobs. Schedule in EDD order; whenever the running job would be
  late, remove the longest-processing job seen so far and set it aside; append the
  set-aside jobs at the end. Exact, classic, very explainable.
- **Metrics:** add `max_lateness` (L_max, can be negative — distinct from
  tardiness) and `weighted_completion_time` to `schedule_metrics`.
- **Hand trace (Moore):** jobs (p,d): A(1,3) B(2,5) C(3,4) D(4,8). EDD: A,C,B,D.
  Completions 1,4,6,10 vs due 3,4,5,8 → B and D late. Remove longest among
  {A,C,B}=B(2)? walk it carefully in the test. Result: minimal tardy count.
- **API:** extend `/api/scheduling/dispatch` to accept weights and return the new
  metrics + a `moore` result block (sequence + which jobs end up tardy).
- **UI:** weight column in the DispatchView job table (optional, defaults 1),
  WSPT in the rule comparison, a Moore card showing the on-time set & tardy set.

### 3. TOC product mix (Process Analysis)
Theory-of-Constraints: with a shared bottleneck, the profit-max mix ranks
products by **contribution margin per bottleneck-minute**, not by margin alone.
- **core/process_analysis/product_mix.py** — products each with
  `contribution_margin`, `bottleneck_time` (min/unit on the constrained resource),
  `demand` (max sellable). Given total bottleneck minutes available:
  rank by margin/bottleneck-time desc, greedily allocate capacity to demand,
  return per-product units made + contribution, total profit, and steps.
- **Hand trace:** bottleneck 2400 min. P1 margin 30, 10 min/u, demand 100 →
  3/min·... rank ratio 3.0; P2 margin 24, 6 min/u → 4.0; P3 margin 20, 4 min/u → 5.0.
  Order P3,P2,P1. Allocate: P3 100u·4=400min (demand 100), P2 100u·6=600, P1 …
  remaining 1400/10=140 but demand 100 → 1000 min, slack left. Total contribution
  computed in test.
- **API:** `POST /api/process-analysis/product-mix`.
- **UI:** new `ProductMixView.tsx` tab on ProcessAnalysisPage + drawer narrating
  the ratio ranking and greedy fill; preset from the hand trace.

### 4. Backlog cost (Lot Sizing) — the requested headliner
Today shortages are forbidden. Allow demand to be met **late** at a penalty
`b` per unit per period backordered.
- **core/lot_sizing/dynamic.py:**
  - `evaluate_plan(..., backlog_cost=0.0)` — negative running inventory is a
    backorder; charge `b · |inventory|` per period instead of raising. Shortages
    only allowed when `backlog_cost > 0`; otherwise keep today's hard error.
  - `wagner_whitin_backlog(demands, setup_cost, holding_cost, backlog_cost)` —
    exact DP. Partition periods into intervals; each interval is served by ONE
    production period `p` inside it. Demand before `p` is backordered, after `p`
    is held: `block(a,p,b) = setup + Σ_{k<p} b·(p−k)·d_k + Σ_{k>p} h·(k−p)·d_k`.
    `f(b) = min_{a≤b} [ f(a−1) + min_{a≤p≤b} block(a,p,b) ]`. O(n³), narratable:
    "each demand is served by exactly one run — held if the run is earlier,
    backordered if later — pick the runs and boundaries that cost least."
- **Hand trace:** demands [10,0,30], S=50, h=1, b=2. Compare: one run period 1
  covers all (holds 30 for 2 periods = 60 → 110) vs run period 3 backorders 10
  for 2 periods (40) + setup 50 = 90 vs two runs (50+50=100). Best = 90 (produce
  once in period 3, backorder period-1 demand). Lock exact numbers in the test.
- **API:** optional `backlog_cost` on `/api/lot-sizing/dynamic`; when > 0, add a
  `wagner_whitin_backlog` plan to the comparison and cost all plans with backlog.
- **UI:** optional backlog-cost input in DynamicView; when set, show the extra
  plan column and allow negative (backordered) inventory in the inventory chart.

## Execution order (low-risk first, headliner last) — ALL DONE 2026-06-13
1. ✅ OEE — core/productivity/oee.py + tab + drawer (hand trace 17/21 = 81.0%).
2. ✅ Job weights + WSPT + L_max / weighted-completion metrics. (Moore–Hodgson
   already existed in core/scheduling/optimal.py, so we added the weighted side.)
3. ✅ TOC product mix — core/process_analysis/product_mix.py + tab + drawer.
4. ✅ Backlog cost — evaluate_plan backlog + wagner_whitin_backlog DP + UI.

All shipped full-stack with hand-traced tests and Playwright smokes; 193
backend + 33 unit + 20 e2e green.

## Per-feature checklist (the project's established rhythm)
- [ ] Hand-trace the example in the test docstring, then write the failing test.
- [ ] Implement core (pure Python, zero UI imports) until green.
- [ ] Add the thin API endpoint / extend the existing one.
- [ ] Wire the React view + teaching drawer + preset; reuse StepPlayer.
- [ ] Playwright smoke on the hand-traced numbers.
- [ ] `pytest`, `npm test`, `npm run e2e` green; commit.

## Out of scope (deferred backlog, from the idea menu)
EOQ backorders/quantity-discounts/EPQ, capacitated lot sizing, CDS m-machine
flow shop, queueing/VUT variability, line-balancing cost/parallel/zoning,
cellular exceptional-elements & similarity-coefficient, learning curves,
price-deflated productivity. Pick up later if these four land well.
