# Design: Assembly Line Balancing module (Phase 1)

**Date:** 2026-06-10
**Status:** Approved pending user review

## Goal

The first module of OM Toolkit: a Streamlit page where a user enters an assembly
line balancing problem (task table + cycle time or demand data), runs three
classic heuristics, and compares the resulting line balances side by side.

Built in teaching mode: the project owner must be able to explain every
algorithm in a job interview. Solvers are validated against the owner's
hand-solved course exercises (see CLAUDE.md "quality rule").

## Architecture

Strict core/UI separation (`core/` has zero Streamlit imports):

```
core/line_balancing/
    models.py             # Task, Station, BalancingResult dataclasses
    precedence.py         # build precedence graph; validate input; shared
                          #   helpers: eligibility check, station-fit check
    metrics.py            # cycle time, theoretical min stations, efficiency,
                          #   balance delay, idle time per station, smoothness
    lcr.py                # Largest Candidate Rule
    rpw.py                # Ranked Positional Weight (Helgeson–Birnie)
    kilbridge_wester.py   # Kilbridge–Wester
app/
    Home.py               # landing page + module roadmap
    pages/1_Line_Balancing.py
    examples.py           # 2–3 preset datasets for instant demo
tests/                    # pytest; heuristic tests come from hand-solved
                          #   course exercises
```

**Heuristic structure decision (approved):** hybrid approach. Shared low-level
helpers (eligibility, station fit) live in `precedence.py`; each heuristic
keeps its own readable top-level loop that mirrors the textbook procedure.
Rejected: a single generic "engine" with pluggable priority rules — Kilbridge–
Wester is column-based, not score-based, so the abstraction would leak and
hide the distinction the owner needs to explain in interviews.

## Course conventions (confirmed by owner, 2026-06-10)

| Topic | Convention |
|---|---|
| Tie-breaking (LCR equal times, RPW equal weights) | lower task ID/letter wins |
| Smoothness index | measured against cycle time: `SI = sqrt(Σ (CT − STi)²)` |
| Cycle time from demand | `CT = available time / demand`, **rounded down** (guarantees demand is met) |
| Efficiency | `Σt / (n · CT)` |
| Balance delay | `1 − efficiency` |
| Theoretical min stations | `ceil(Σt / CT)` |

## Open items (resolve at the relevant milestone, never assume)

- **Kilbridge–Wester within-column ordering:** owner answered "most efficient
  way possible"; confirm the exact course procedure (likely largest task time
  first) against the hand-solved KW exercise at milestone 4.
- **Hand-solved exercises:** collect 1–2 per heuristic from the owner before
  implementing each (milestones 2–4). A heuristic is done only when it
  reproduces the owner's hand solutions.
- **Time units:** confirm with the first exercise (question went unanswered).

## Input validation (in `precedence.py`)

Reject with clear messages: duplicate task IDs, unknown predecessor references,
circular precedence, non-positive durations, any task duration > cycle time
(task can never fit in a station).

## UI (milestone 5)

Editable task table (`st.data_editor`), cycle time entered directly or derived
from demand + available time, rendered precedence diagram (NetworkX + Plotly),
visual of tasks grouped into stations per heuristic, side-by-side metrics
comparison table, preset example selector.

## Testing

- `tests/test_precedence.py`, `tests/test_metrics.py`: cases constructed
  during milestone 1, conventions above encoded as tests.
- `tests/test_lcr.py`, `tests/test_rpw.py`, `tests/test_kilbridge_wester.py`:
  one test per hand-solved course exercise, asserting exact station
  assignments and metrics.
- On any mismatch between code and hand solution: walk through the algorithm
  step by step with the owner; never silently change either side.

## Milestones (checkpoint + walkthrough after each)

1. Scaffold (`requirements.txt`, `.venv`, `.gitignore`) + models, precedence
   validation, metrics, with tests.
2. Largest Candidate Rule (explain → confirm → exercises → tests → implement).
3. Ranked Positional Weight (same cycle).
4. Kilbridge–Wester (same cycle; resolve column-ordering convention).
5. Streamlit UI + preset examples.
6. README skeleton (vision, roadmap, run instructions; deployment listed as
   roadmap item only).

## Environment

Python 3.11+ (already installed), `.venv/` in project root (gitignored),
dependencies: streamlit, plotly, networkx, pytest.
