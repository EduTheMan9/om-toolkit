# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**OM Toolkit** — a React + FastAPI web app of interactive Operations Management solvers (the folder name `GO_ToolKit` is "Gestão de Operações", Portuguese for Operations Management), built as a learning + portfolio project by a 3rd-year Industrial & Management Engineering student (beginner-to-intermediate Python). Full brief: `claude-code-kickoff-prompt.md`. It started as a Streamlit app; the React redesign reached full parity and the legacy `app/` was retired on 2026-06-12.

The two goals, in priority order:
1. **Learning** — the user must understand every algorithm well enough to explain it in a job interview. Code the user can't explain is a failure even if it works.
2. **Portfolio** — a deployed app other IEM students can use, with a clean GitHub repo and commit history.

### Roadmap
All six modules (Assembly Line Balancing, Process Analysis, Scheduling,
MRP & Lot Sizing, Cellular Manufacturing, Productivity Metrics) are ✅ done
in core, API, and the React UI. Remaining: deploy the FastAPI + React app.

## Tech stack

Python 3.11+, FastAPI (API), pytest (tests); React 18 + TypeScript + Vite,
Plotly (charts), Vitest + Playwright (frontend tests).

## Commands

```
pip install -r requirements.txt    # install backend dependencies
cd web && npm install              # install frontend dependencies
uvicorn api.main:app --reload --port 8000   # run the API (serves web/dist if built)
cd web && npm run dev              # frontend dev server (Vite proxies /api)
pytest                             # run all backend tests
pytest tests/test_<module>.py -k <test_name>   # run a single test
cd web && npm test                 # frontend unit tests (Vitest)
cd web && npm run e2e              # browser smoke tests (Playwright)
```

## Architecture

**Strict separation of algorithm logic and UI:**
- `core/` — all solver/algorithm logic as pure Python with **zero Streamlit imports**, independently testable.
- `api/` — FastAPI JSON layer over `core/` (one thin router per module); serves the built frontend.
- `web/` — React + TypeScript + Vite frontend (Clean Lab design system, see `docs/superpowers/specs/2026-06-11-react-redesign-design.md`).
- `tests/` — pytest tests for `core/` and `api/`; `web/` has Vitest unit tests and Playwright smoke tests (`npm test`, `npm run e2e` in `web/`).

## Validation rule

(Amended 2026-06-10: the user dropped the original "tests from my hand-solved exercises" rule — do not ask for hand-solved exercises.)

- Each solver is validated against a **worked example traced step by step by hand** before the test is written; the trace lives in comments/docstrings near the test.
- Confirmed course conventions (encoded in `tests/test_metrics.py` — keep):
  tie-breaking by **lower task ID**; smoothness index **vs cycle time** `SI = sqrt(Σ(CT − STi)²)`; cycle time from demand **rounded down**; efficiency `Σt/(n·CT)`; balance delay `1 − efficiency`; min stations `ceil(Σt/CT)`; Kilbridge–Wester within-column order: **largest duration first**.

## Phase 1 scope: Assembly Line Balancing

- **Inputs:** task table (task ID, duration, immediate predecessors) + either (demand + available production time) or a cycle time given directly.
- **Solvers (three heuristics, results comparable side by side):** Largest Candidate Rule, Ranked Positional Weight (Helgeson–Birnie), Kilbridge–Wester.
- **Metrics:** cycle time, theoretical minimum stations, station assignments, line efficiency, balance delay, idle time per station, smoothness index.
- **UI:** editable task table, precedence diagram, station-grouping visual, side-by-side heuristic comparison, 2–3 preloaded example datasets.

## Working style

(Amended 2026-06-10: the user relaxed the original heavy teaching mode — "just do this project taking into account the best operation management ways and implement them." Implement directly; keep explanations brief and educational; don't block on confirmation gates.)

- When the user asks questions about code, answer by teaching, not just fixing.
- The user may write in Portuguese; all code, comments, commit messages, and documentation stay in English.
- Simple, readable code over clever code. Comment the *engineering reasoning*, not obvious syntax.
- Small, frequent git commits with clear messages — the commit history is part of the portfolio.
