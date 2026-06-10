# Project kickoff: OM Toolkit — Operations Management Solver Suite

## Who I am
I'm a 3rd-year Industrial & Management Engineering student. My Python is beginner-to-intermediate. This project has two goals, in this order:
1. **Learning.** I must understand every algorithm well enough to explain it in a job interview. If you write code I can't explain, the project has failed even if it works.
2. **Portfolio.** A deployed web app that other IEM students can actually use, with a clean GitHub repo.

## The vision
A web app with interactive solvers for the core Operations Management methods, built one module at a time:
1. **Assembly Line Balancing** ← PHASE 1, build this now
2. Process analysis & bottleneck (capacity, utilization, Little's Law)
3. Scheduling (Johnson's rule, dispatching rules, Gantt charts)
4. MRP & lot-sizing (EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin)
5. Cellular manufacturing (rank order clustering)
6. Productivity metrics

We only build Phase 1 in this session, but structure the code so future modules plug in cleanly.

## Tech stack and architecture
- Python 3.11+, Streamlit for the UI, Plotly for charts, NetworkX (+ Graphviz if needed) for precedence diagrams, pytest for tests.
- Strict separation: all algorithm logic lives in `core/` as pure Python with **zero Streamlit imports**, so it can be tested independently. UI lives in `app/`.
- Git from the very first commit. Small, frequent commits with clear messages — the commit history is part of my portfolio.
- Simple, readable code over clever code. Comment the *engineering reasoning*, not the obvious syntax.

## Phase 1 scope: Assembly Line Balancing
**Inputs:** a task table (task ID, duration, immediate predecessors), plus either (demand + available production time) or a cycle time given directly.

**Solvers:** implement these three heuristics so results can be compared:
- Largest Candidate Rule
- Ranked Positional Weight (Helgeson–Birnie)
- Kilbridge–Wester

**Outputs/metrics:** cycle time, theoretical minimum number of stations, station assignments per heuristic, line efficiency, balance delay, idle time per station, smoothness index.

**UI:** editable task table, rendered precedence diagram, visual of tasks grouped into stations, side-by-side metrics comparison of the three heuristics, and 2–3 preloaded example datasets so the app demos instantly.

## The quality rule that overrides everything: tests from my solved exercises
Before implementing each heuristic, **ask me for 1–2 exercises I solved by hand in my course** (task data, cycle time, and my step-by-step solution). Encode them as pytest test cases. A solver is only "done" when it reproduces my hand-calculated solutions.

If the code's result differs from my hand solution, do NOT silently change the code or assume I'm wrong. Walk through the algorithm with me step by step until we find whether the bug is in the code or in my hand calculation. Both happen, and finding out which is the whole point.

Textbook conventions vary (e.g., tie-breaking rules in heuristics, smoothness index definitions). When a convention could differ between textbooks, ask me what my course used instead of assuming.

## How I want you to work (teaching mode)
- **Plan before code.** Present your plan and your open questions, and wait for my approval before writing anything.
- **Small steps with checkpoints.** After each milestone, stop and walk me through what you wrote and why, file by file. Don't move on until I confirm I've understood.
- **Explain algorithms in plain language first**, before implementing, and have me confirm the logic matches what I learned in class.
- When I review code, expect questions. Answer them by teaching, not just fixing.
- I may sometimes write to you in Portuguese — that's fine. All code, comments, commit messages, and documentation stay in English.

## Deliverables for this first session
1. Repo scaffold + a concise `CLAUDE.md` (under ~150 lines) capturing the conventions in this document, so future sessions retain full context.
2. `core/` line balancing logic with pytest tests passing against my hand-solved exercises.
3. A minimal Streamlit page running locally for the line balancing module.
4. A `README.md` skeleton: project vision, roadmap of the six modules, how to run locally. (Deployment to Streamlit Community Cloud goes in the roadmap — we'll do it once Phase 1 is polished.)

Stop for my review after each deliverable.

**Start now by showing me your plan for this session and every question you need answered before writing any code.**
