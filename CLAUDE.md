# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**OM Toolkit** — a Streamlit web app of interactive Operations Management solvers (the folder name `GO_ToolKit` is "Gestão de Operações", Portuguese for Operations Management), built as a learning + portfolio project by a 3rd-year Industrial & Management Engineering student (beginner-to-intermediate Python). Full brief: `claude-code-kickoff-prompt.md`.

The two goals, in priority order:
1. **Learning** — the user must understand every algorithm well enough to explain it in a job interview. Code the user can't explain is a failure even if it works.
2. **Portfolio** — a deployed app other IEM students can use, with a clean GitHub repo and commit history.

### Roadmap (build one module at a time)
1. **Assembly Line Balancing** ← Phase 1, current focus
2. Process analysis & bottleneck (capacity, utilization, Little's Law)
3. Scheduling (Johnson's rule, dispatching rules, Gantt charts)
4. MRP & lot-sizing (EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin)
5. Cellular manufacturing (rank order clustering)
6. Productivity metrics

Only build the current phase, but structure code so future modules plug in cleanly.

## Tech stack

Python 3.11+, Streamlit (UI), Plotly (charts), NetworkX (precedence diagrams), pytest (tests).

## Commands

```
pip install -r requirements.txt    # install dependencies
streamlit run app/Home.py          # run the app locally
pytest                             # run all tests
pytest tests/test_<module>.py -k <test_name>   # run a single test
```

## Architecture

**Strict separation of algorithm logic and UI:**
- `core/` — all solver/algorithm logic as pure Python with **zero Streamlit imports**, independently testable.
- `app/` — Streamlit UI only.
- `tests/` — pytest tests for `core/`.

## The quality rule that overrides everything

Solvers are validated against **exercises the user solved by hand in their course**:
- Before implementing each heuristic, **ask the user for 1–2 hand-solved exercises** (task data, cycle time, step-by-step solution) and encode them as pytest test cases.
- A solver is only "done" when it reproduces the user's hand-calculated solutions.
- If code output differs from the hand solution, do **not** silently change the code or assume the user is wrong. Walk through the algorithm step by step together until you find whether the bug is in the code or in the hand calculation.
- Textbook conventions vary (tie-breaking rules, smoothness index definitions, etc.). When a convention could differ between textbooks, **ask what the user's course used** instead of assuming.

## Phase 1 scope: Assembly Line Balancing

- **Inputs:** task table (task ID, duration, immediate predecessors) + either (demand + available production time) or a cycle time given directly.
- **Solvers (three heuristics, results comparable side by side):** Largest Candidate Rule, Ranked Positional Weight (Helgeson–Birnie), Kilbridge–Wester.
- **Metrics:** cycle time, theoretical minimum stations, station assignments, line efficiency, balance delay, idle time per station, smoothness index.
- **UI:** editable task table, precedence diagram, station-grouping visual, side-by-side heuristic comparison, 2–3 preloaded example datasets.

## Working style (teaching mode)

- **Plan before code.** Present plan and open questions; wait for approval before writing anything.
- **Small steps with checkpoints.** After each milestone, stop and walk the user through what was written and why, file by file. Don't move on until they confirm understanding.
- **Explain algorithms in plain language first**, before implementing; have the user confirm the logic matches what they learned in class.
- When the user asks questions about code, answer by teaching, not just fixing.
- The user may write in Portuguese; all code, comments, commit messages, and documentation stay in English.
- Simple, readable code over clever code. Comment the *engineering reasoning*, not obvious syntax.
- Small, frequent git commits with clear messages — the commit history is part of the portfolio.
