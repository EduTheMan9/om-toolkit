# 🏭 OM Toolkit

Interactive solvers for core Operations Management methods, built as a
learning and portfolio project by an Industrial & Management Engineering
student. (`GO` = *Gestão de Operações*, Portuguese for Operations Management.)

## Modules

| # | Module | Status |
|---|--------|--------|
| 1 | **Assembly Line Balancing** — Largest Candidate Rule, Ranked Positional Weight, Kilbridge–Wester | ✅ available |
| 2 | **Process analysis & bottleneck** — capacity, utilization, implied utilization, Little's Law | ✅ available |
| 3 | **Scheduling** — dispatching rules (FCFS/SPT/EDD/LPT), Johnson's rule, Gantt charts | ✅ available |
| 4 | **MRP & lot-sizing** — EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin | ✅ available |
| 5 | **Cellular manufacturing** — rank order clustering, grouping efficacy | ✅ available |
| 6 | **Productivity metrics** — single-factor, multifactor, period-over-period change | ✅ available |

## Assembly Line Balancing

Enter a task table (durations + precedence), set the cycle time directly or
derive it from demand, and compare three classic balancing heuristics side by
side: station assignments, line efficiency, balance delay, idle times, and
smoothness index — with a rendered precedence diagram and preloaded example
datasets.

## Process Analysis & Bottleneck

Describe a process as a sequence of resources (processing time + number of
servers), optionally with demand: get the bottleneck, process capacity, flow
rate, utilization and implied utilization per resource, and unloaded flow
time — plus a Little's Law calculator (I = R × T).

## Scheduling

Sequence jobs on one machine with four dispatching rules (FCFS, SPT, EDD,
LPT) compared side by side — plus the exact optimizers Moore–Hodgson (fewest
tardy jobs) and a total-tardiness DP — or two machines with Johnson's rule,
all visualized as Gantt charts.

## MRP & Lot Sizing

EOQ with the ordering-vs-holding cost trade-off curve, and dynamic lot sizing
over period-by-period demand: lot-for-lot, the Silver–Meal heuristic, and the
provably optimal Wagner–Whitin dynamic program, compared on setups, holding,
and total cost with per-period order/inventory charts.

## Cellular Manufacturing

Rank Order Clustering on a machine–part incidence matrix: ROC sorts rows and
columns by binary value until the 1s form diagonal blocks, then an exact
search over consecutive machine splits picks the cells with the highest
grouping efficacy — shown as before/after heatmaps with exceptional elements
and voids highlighted.

## Productivity Metrics

Single-factor and multifactor productivity with a two-period comparison
table: see how one factor can look great (labor after automation) while
multifactor productivity — the honest aggregate — moves the other way.

## Run locally

**Classic app (Streamlit, all six modules):**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (use source .venv/bin/activate elsewhere)
pip install -r requirements.txt
streamlit run app/Home.py
```

**New app (React + FastAPI — being rolled out module by module):**

```bash
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
uvicorn api.main:app --port 8000     # serves API + UI at http://localhost:8000
```

Dev mode runs them separately: `uvicorn api.main:app --reload --port 8000`
in one terminal, `cd web && npm run dev` in another (Vite proxies /api).

## Tests

All solver logic lives in `core/` as pure Python (no UI imports) and is
validated against worked examples traced by hand, documented next to the tests.

```bash
pytest                  # core/ + api/ tests
cd web && npm test      # frontend unit tests (Vitest)
cd web && npm run e2e   # browser smoke tests (Playwright)
```

## Project structure

```
core/   pure algorithm logic (importable, testable, UI-free)
api/    FastAPI JSON layer over core/, serves the built frontend
web/    React + TypeScript + Vite frontend (Clean Lab design system)
app/    legacy Streamlit UI (kept until the React app reaches parity)
tests/  pytest suite with hand-traced validation examples
docs/   design specs and implementation plans
```

## Roadmap

- All six modules are built in the classic app ✅
- React redesign: Lot Sizing ✅ — remaining modules rolling out one by one
- Deploy the FastAPI + React app
