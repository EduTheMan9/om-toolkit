# Design: Scheduling module (Phase 3)

**Date:** 2026-06-11
**Status:** Implementing (per the amended direct-implementation workflow)

## Goal

Third OM Toolkit module, two classic scheduling settings:

1. **Single machine, dispatching rules** — sequence n jobs (processing time +
   due date) by FCFS, SPT, EDD, LPT and compare the resulting performance.
2. **Two-machine flow shop, Johnson's rule** — minimize makespan; show the
   optimal sequence on a two-row Gantt chart.

## Definitions and conventions

| Quantity | Definition |
|---|---|
| Completion time Cj | cumulative finish time of job j in sequence |
| Flow time (here) | = completion time (all jobs available at t = 0) |
| Tardiness Tj | `max(0, Cj − due date)` (never negative, unlike lateness) |
| Rule metrics | average completion time, average tardiness, max tardiness, number of tardy jobs |
| Makespan (Johnson) | completion of the last job on machine 2 |

**Tie conventions** (consistent with Phase 1: lower job ID wins):
- SPT/LPT/EDD ties → lower job ID first.
- Johnson's rule, tie for the smallest remaining time between an M1-side and
  an M2-side candidate → the M1-side job (front placement) wins, then lower ID.
- A job whose own M1 time equals its M2 time counts as M1-side (front).

## Architecture

```
core/scheduling/
    __init__.py      # public API
    models.py        # Job (id, processing_time, due_date),
                     #   FlowShopJob (id, time_m1, time_m2),
                     #   ScheduledJob (id, start, end)
    dispatching.py   # validation; fcfs/spt/edd/lpt orderings; build_schedule;
                     #   schedule_metrics
    johnson.py       # validation; johnson_sequence; flow_shop_schedule
                     #   (per-machine ScheduledJobs + makespan)
app/
    pages/3_Scheduling.py     # two tabs: dispatching / Johnson
    scheduling_charts.py      # rule-comparison Gantt (tardy jobs highlighted),
                              #   two-machine Gantt (idle gaps visible)
```

`app/examples.py` gains dispatching and flow-shop presets. Roadmaps in
`Home.py`, `README.md`, `CLAUDE.md` flip module 3 to available.

## Amendment (2026-06-11): exact optimizers

Added on user request ("optimize to the most efficient way possible").
"Most efficient" depends on the objective, so `core/scheduling/optimal.py`
adds the two objectives the rules don't already solve optimally:

- **Moore–Hodgson** — provably minimal number of tardy jobs, O(n log n).
  Ejected jobs are appended after the on-time jobs in ejection order; the
  ejection tie (equal longest processing time) keeps the earliest in EDD order.
- **min_total_tardiness** — exact subset DP (the problem is NP-hard); capped
  at `MAX_OPTIMAL_JOBS = 15` jobs. dp[S] chooses the last job of subset S,
  which always completes at sum(processing times of S).

Both appear as extra rows in the UI comparison table; the comparison gains a
"Total tardiness" column (also added to `schedule_metrics`).

## Hand-traced validation examples

**Dispatching** — jobs (p, due): A(6,8) B(2,6) C(8,18) D(3,15) E(9,23).
- FCFS A,B,C,D,E: C = 6,8,16,19,28 → avg completion 15.4; tardiness
  0,2,0,4,5 → avg 2.2, max 5, tardy 3.
- SPT B,D,A,C,E: C = 2,5,11,19,28 → avg 13.0; tardiness 0,0,3,1,5 →
  avg 1.8, max 5, tardy 3.
- EDD B,A,D,C,E: C = 2,8,11,19,28 → tardiness 0,0,0,1,5 → avg 1.2, max 5, tardy 2.
- LPT E,C,A,D,B: C = 9,17,23,26,28 → avg 20.6; tardiness 0,0,15,11,22 →
  avg 9.6, max 22, tardy 3.

**Johnson** — jobs (M1, M2): J1(3,6) J2(5,2) J3(1,2) J4(6,6) J5(7,5).
Sequence J3, J1, J4, J5, J2. Machine 1 runs 0–22 back to back;
machine 2: J3 1–3, J1 4–10, J4 10–16, J5 17–22, J2 22–24. **Makespan 24.**

## Testing

One pytest per rule asserting sequence + metrics from the traces above;
Johnson tests assert sequence, per-machine start/end times, and makespan;
validation tests for duplicate/blank IDs, non-positive times, missing due dates.
