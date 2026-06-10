# Design: Process Analysis & Bottleneck module (Phase 2)

**Date:** 2026-06-11
**Status:** Implementing (per the amended direct-implementation workflow)

## Goal

Second OM Toolkit module: enter a process as a sequence of resources
(processing time + number of servers each), and get capacity analysis —
bottleneck identification, flow rate, utilization per resource — plus a
Little's Law calculator.

## Concepts implemented (standard process-analysis definitions)

| Quantity | Definition |
|---|---|
| Resource capacity | `servers / processing_time` (units per time unit) |
| Process capacity | minimum resource capacity |
| Bottleneck | the resource with minimum capacity (tie: first in process order) |
| Flow rate | `min(demand, process capacity)`; just process capacity if no demand given |
| Utilization | `flow rate / resource capacity` (≤ 100%) |
| Implied utilization | `demand / resource capacity` (can exceed 100%) |
| Flow time (unloaded) | sum of processing times — no queueing model |
| Little's Law | `I = R × T`; given any two of inventory, flow rate, flow time, solve the third |

**Units:** the core is unit-agnostic — capacity comes out in units per the
same time unit as processing time. The UI takes processing times in
minutes/unit and displays capacities in units/hour (×60).

## Architecture

Same pattern as Phase 1 (`core/` pure Python, UI in `app/`):

```
core/process_analysis/
    __init__.py        # public API
    models.py          # Resource dataclass (name, processing_time, servers)
    capacity.py        # validation, bottleneck, process capacity, flow rate,
                       #   utilization, implied utilization, unloaded flow time
    littles_law.py     # solve I = R*T for whichever variable is missing
app/
    pages/2_Process_Analysis.py
    process_charts.py  # capacity bar chart (bottleneck highlighted, demand
                       #   line) + utilization bar chart; no Streamlit imports
```

`app/examples.py` gains process-analysis presets (sandwich line, clinic,
3-step demo). `Home.py` and `README.md` roadmaps flip module 2 to available.

## Validation (in `capacity.py`)

Reject with clear messages: empty resource list, blank or duplicate names,
non-positive processing times, servers < 1. Little's Law solver requires
exactly one unknown and positive known values.

## Testing

Hand-traced example (times in minutes): A = 10 min × 2 servers → 0.2/min,
B = 6 min × 1 → 0.1667/min, C = 4 min × 1 → 0.25/min. Bottleneck B; process
capacity 1/6 per min (10/hr). Demand 0.15/min → flow rate 0.15; utilizations
A 75%, B 90%, C 60%. Implied utilization at demand 0.2/min: B = 120%.
Little's Law cases solve each variable from the other two.
