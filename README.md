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
| 4 | MRP & lot-sizing — EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin | planned |
| 5 | Cellular manufacturing — rank order clustering | planned |
| 6 | Productivity metrics | planned |

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

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (use source .venv/bin/activate elsewhere)
pip install -r requirements.txt
streamlit run app/Home.py
```

## Tests

All solver logic lives in `core/` as pure Python (no Streamlit imports) and is
validated against worked examples traced by hand, documented next to the tests.

```bash
pytest
```

## Project structure

```
core/   pure algorithm logic (importable, testable, UI-free)
app/    Streamlit UI
tests/  pytest suite with hand-traced validation examples
docs/   design specs and implementation plans
```

## Roadmap

- Deploy to Streamlit Community Cloud once Phase 1 is polished
- Build modules 2–6, one at a time, on the same core/UI separation
