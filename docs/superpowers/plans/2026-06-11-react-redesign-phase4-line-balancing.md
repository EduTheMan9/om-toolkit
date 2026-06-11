# React Redesign Phase 4: Line Balancing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Line Balancing module in the React app: all three heuristics (LCR, RPW, Kilbridge–Wester) compared side by side, a precedence diagram, a station-grouping chart, demand-derived cycle time, and a teaching drawer that narrates Ranked Positional Weight.

**Architecture:** A new `api/routers/line_balancing.py` wraps the untouched `core/line_balancing` solvers in one `/api/line-balancing/solve` endpoint (3 heuristics + metrics + Kilbridge columns as the diagram layout + RPW steps). `core/` gains step-recording via the shared greedy loop: `assign_in_order_with_steps` plus `ranked_positional_weight_with_steps`, both preserving current behavior by delegation. The frontend gains a `/line-balancing` page with a tasks table (ID + duration + predecessors), cycle-time source pills (direct / from demand), hero + comparison cards, two Plotly cards (precedence diagram, station Gantt reusing `ganttTraces`), and an `RpwDrawer` on the shared `StepPlayer`.

**Tech Stack:** Python 3.11+, FastAPI, pytest; React 18 + TypeScript, Plotly, Vitest, Playwright. No new dependencies.

**Context for the engineer:** Operations Management teaching toolkit; solver math lives in `core/` with hand-traced tests in `tests/` — never change solver behavior (delegation refactors proven by existing tests are fine). Specs: `docs/superpowers/specs/2026-06-11-react-redesign-design.md` (UI pattern) and `docs/superpowers/specs/2026-06-10-line-balancing-design.md` (math + course conventions). Copy the pattern of the shipped Scheduling module (`api/routers/scheduling.py`, `web/src/pages/scheduling/`). Python runs via `.\.venv\Scripts\python.exe`; frontend commands run in `web/`.

**Reference — hand-traced example used everywhere below (already encoded in `tests/example_problem.py` and the three heuristic test files):**

Tasks (duration, predecessors): A(5,—) B(3,A) C(4,A) D(2,B) E(6,C) F(4,D+E). Cycle time **10**. Total work **24**, theoretical minimum **3** stations.
- LCR stations: **[A,C] [E,B] [D,F]** — RPW: same grouping — Kilbridge–Wester: **[A,C] [B,E] [D,F]**.
- All three: 3 stations, efficiency **0.8**, balance delay 0.2, smoothness index **√18 ≈ 4.243** (station times 9, 9, 6).
- RPW weights: A 24, C 14, E 10, B 9, D 6, F 4 → rank A, C, E, B, D, F.
- Kilbridge columns: A1, B2, C2, D3, E3, F4.
- RPW assignment trace (from `tests/test_rpw.py`): St1 assign A (5 left) → assign C (1 left) → E no-fit, B no-fit, D blocked(B), F blocked(D,E) → close {A,C}=9, idle 1. St2 assign E (4 left) → assign B (1 left) → D no-fit, F blocked(D) → close {E,B}=9, idle 1. St3 assign D (8 left) → assign F → close {D,F}=6, idle 4.
- Demand mode: 480 time available / demand 70 → CT = floor(6.857) = **6** (course convention, from `tests/test_metrics.py`).

---

### Task 1: RPW step trace in core/

**Files:**
- Modify: `core/line_balancing/assignment.py`, `core/line_balancing/rpw.py`, `core/line_balancing/__init__.py`
- Test: `tests/test_rpw.py` (append)

The narration backbone is the shared greedy loop: every scan either assigns
the first eligible-and-fitting task or closes the station, and the tasks it
skipped on the way down (blocked by precedence / doesn't fit) are exactly the
hand-trace reasoning. Record those events; `assign_in_order` and
`ranked_positional_weight` keep their behavior by delegation.

Step schema:
- `{"kind": "rank", "order": ["A","C","E","B","D","F"], "weights": {"A": 24.0, ...}}` — RPW opening card.
- `{"kind": "assign", "station": 1, "task": "A", "duration": 5.0, "remaining": 5.0}` — `remaining` is station capacity left AFTER the assignment.
- `{"kind": "skip", "station": 1, "task": "D", "reason": "blocked", "missing": ["B"]}`
- `{"kind": "skip", "station": 1, "task": "E", "reason": "no_fit", "duration": 6.0, "remaining": 1.0}` — `remaining` is capacity left BEFORE (why it doesn't fit).
- `{"kind": "close", "station": 1, "tasks": ["A","C"], "total": 9.0, "idle": 1.0}` — also emitted for the final station.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_rpw.py`:

```python
def test_rpw_with_steps_narrates_the_worked_example():
    """The docstring trace above, as recorded steps: every scan's skips
    (blocked / doesn't fit) land just before the assign or close they led to."""
    from core.line_balancing.rpw import ranked_positional_weight_with_steps

    stations, steps = ranked_positional_weight_with_steps(TASKS, CYCLE_TIME)
    assert station_ids(stations) == [["A", "C"], ["E", "B"], ["D", "F"]]

    assert steps[0]["kind"] == "rank"
    assert steps[0]["order"] == ["A", "C", "E", "B", "D", "F"]
    assert steps[0]["weights"]["A"] == pytest.approx(24.0)

    assigns = [(s["station"], s["task"]) for s in steps if s["kind"] == "assign"]
    assert assigns == [(1, "A"), (1, "C"), (2, "E"), (2, "B"), (3, "D"), (3, "F")]

    skips = [(s["station"], s["task"], s["reason"]) for s in steps if s["kind"] == "skip"]
    assert skips == [
        (1, "E", "no_fit"),
        (1, "B", "no_fit"),
        (1, "D", "blocked"),
        (1, "F", "blocked"),
        (2, "D", "no_fit"),
        (2, "F", "blocked"),
    ]
    blocked_d = next(s for s in steps if s["kind"] == "skip" and s["task"] == "D")
    assert blocked_d["missing"] == ["B"]

    closes = [
        (s["station"], s["tasks"], s["total"], s["idle"])
        for s in steps
        if s["kind"] == "close"
    ]
    assert closes == [
        (1, ["A", "C"], 9.0, 1.0),
        (2, ["E", "B"], 9.0, 1.0),
        (3, ["D", "F"], 6.0, 4.0),
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_rpw.py -q`
Expected: FAIL — `ImportError: cannot import name 'ranked_positional_weight_with_steps'`.

- [ ] **Step 3: Implement by refactoring the shared loop**

In `core/line_balancing/assignment.py`, REPLACE `assign_in_order` with:

```python
def assign_in_order_with_steps(
    ordered_tasks: list[Task], cycle_time: float
) -> tuple[list[Station], list[dict]]:
    """The greedy loop, recording its decisions so the UI can replay them:
    each scan walks the priority list, skipping tasks that are precedence-
    blocked or don't fit, until it assigns one or closes the station."""
    stations = [Station(index=1)]
    steps: list[dict] = []
    assigned: set[str] = set()
    while len(assigned) < len(ordered_tasks):
        station = stations[-1]
        remaining = cycle_time - station.total_time
        pick = None
        for t in ordered_tasks:
            if t.id in assigned:
                continue
            missing = [p for p in t.predecessors if p not in assigned]
            if missing:
                steps.append(
                    {"kind": "skip", "station": station.index, "task": t.id,
                     "reason": "blocked", "missing": missing}
                )
                continue
            if not fits_in_station(t, station, cycle_time):
                steps.append(
                    {"kind": "skip", "station": station.index, "task": t.id,
                     "reason": "no_fit", "duration": t.duration,
                     "remaining": remaining}
                )
                continue
            pick = t
            break
        if pick is None:
            steps.append(_close_step(station, cycle_time))
            stations.append(Station(index=len(stations) + 1))
        else:
            station.tasks.append(pick)
            assigned.add(pick.id)
            steps.append(
                {"kind": "assign", "station": station.index, "task": pick.id,
                 "duration": pick.duration,
                 "remaining": cycle_time - station.total_time}
            )
    steps.append(_close_step(stations[-1], cycle_time))
    return stations, steps


def _close_step(station: Station, cycle_time: float) -> dict:
    return {
        "kind": "close",
        "station": station.index,
        "tasks": [t.id for t in station.tasks],
        "total": station.total_time,
        "idle": station.idle_time(cycle_time),
    }


def assign_in_order(ordered_tasks: list[Task], cycle_time: float) -> list[Station]:
    stations, _ = assign_in_order_with_steps(ordered_tasks, cycle_time)
    return stations
```

(Keep the module docstring; the comment about "cannot loop forever" moves
implicitly — a valid task always fits an empty station because
`validate_tasks` guarantees duration ≤ cycle time.)

In `core/line_balancing/rpw.py`, REPLACE `ranked_positional_weight` with:

```python
def ranked_positional_weight_with_steps(
    tasks: list[Task], cycle_time: float
) -> tuple[list[Station], list[dict]]:
    """RPW that records its ranking and every assignment decision, so the UI
    can replay the heuristic step by step on the user's data."""
    validate_tasks(tasks, cycle_time)  # also guarantees the recursion terminates
    weights = positional_weights(tasks)
    candidates = sorted(tasks, key=lambda t: (-weights[t.id], t.id))
    steps: list[dict] = [
        {"kind": "rank", "order": [t.id for t in candidates], "weights": weights}
    ]
    stations, assign_steps = assign_in_order_with_steps(candidates, cycle_time)
    return stations, steps + assign_steps


def ranked_positional_weight(tasks: list[Task], cycle_time: float) -> list[Station]:
    stations, _ = ranked_positional_weight_with_steps(tasks, cycle_time)
    return stations
```

and change the import at the top to `from .assignment import assign_in_order_with_steps` (drop `assign_in_order` if now unused in this file).

In `core/line_balancing/__init__.py`, add to the `.rpw` import and `__all__` (alphabetical): `ranked_positional_weight_with_steps`.

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 130 passed — the existing LCR/RPW/KW hand-trace tests prove the loop refactor preserved behavior for all three heuristics.

- [ ] **Step 5: Commit**

```bash
git add core/line_balancing tests/test_rpw.py
git commit -m "feat: record rpw ranking and assignment steps for the teaching drawer"
```

---

### Task 2: Line-balancing solve endpoint

**Files:**
- Create: `api/routers/line_balancing.py`
- Modify: `api/main.py`
- Test: `tests/test_api_line_balancing.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_line_balancing.py`:

```python
"""Line-balancing API endpoint, validated against the shared hand-traced
example (see tests/example_problem.py and the three heuristic test files)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SOLVE_REQUEST = {
    "tasks": [
        {"id": "A", "duration": 5},
        {"id": "B", "duration": 3, "predecessors": ["A"]},
        {"id": "C", "duration": 4, "predecessors": ["A"]},
        {"id": "D", "duration": 2, "predecessors": ["B"]},
        {"id": "E", "duration": 6, "predecessors": ["C"]},
        {"id": "F", "duration": 4, "predecessors": ["D", "E"]},
    ],
    "cycle_time": 10,
}


def test_solve_endpoint_worked_example():
    response = client.post("/api/line-balancing/solve", json=SOLVE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["cycle_time"] == 10.0
    assert body["total_work"] == 24.0
    assert body["min_stations"] == 3
    # layout data for the precedence diagram + RPW teaching numbers
    assert body["columns"] == {"A": 1, "B": 2, "C": 2, "D": 3, "E": 3, "F": 4}
    assert body["weights"]["A"] == pytest.approx(24.0)
    h = body["heuristics"]
    assert [s["task_ids"] for s in h["lcr"]["stations"]] == [
        ["A", "C"], ["E", "B"], ["D", "F"],
    ]
    assert [s["task_ids"] for s in h["kilbridge_wester"]["stations"]] == [
        ["A", "C"], ["B", "E"], ["D", "F"],
    ]
    assert h["rpw"]["num_stations"] == 3
    assert h["rpw"]["efficiency"] == pytest.approx(0.8)
    assert h["rpw"]["balance_delay"] == pytest.approx(0.2)
    assert h["rpw"]["smoothness_index"] == pytest.approx(4.2426, abs=1e-3)
    assert h["lcr"]["stations"][0]["total_time"] == pytest.approx(9.0)
    assert h["lcr"]["stations"][0]["idle_time"] == pytest.approx(1.0)
    # RPW narration for the teaching drawer
    assert body["steps"][0]["kind"] == "rank"
    assert body["steps"][0]["order"] == ["A", "C", "E", "B", "D", "F"]


def test_solve_derives_cycle_time_from_demand():
    request = {k: v for k, v in SOLVE_REQUEST.items() if k != "cycle_time"}
    request["available_time"] = 480
    request["demand"] = 70
    response = client.post("/api/line-balancing/solve", json=request)
    assert response.status_code == 200
    # course convention: floor(480/70) = 6, so demand is always met
    assert response.json()["cycle_time"] == 6.0


def test_solve_requires_a_cycle_time_or_demand_pair():
    request = {"tasks": SOLVE_REQUEST["tasks"]}
    response = client.post("/api/line-balancing/solve", json=request)
    assert response.status_code == 422
    assert "cycle time" in response.json()["detail"].lower()


def test_solve_rejects_unknown_predecessor_with_core_message():
    bad = {
        "tasks": [{"id": "A", "duration": 5, "predecessors": ["Z"]}],
        "cycle_time": 10,
    }
    response = client.post("/api/line-balancing/solve", json=bad)
    assert response.status_code == 422
    assert "unknown predecessor" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_line_balancing.py -q`
Expected: FAIL — 404, route does not exist.

- [ ] **Step 3: Implement the router**

Create `api/routers/line_balancing.py`:

```python
"""Line-balancing endpoint: all three heuristics, metrics, and diagram layout."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.line_balancing import (
    Station,
    Task,
    balance_delay,
    cycle_time_from_demand,
    kilbridge_columns,
    kilbridge_wester,
    largest_candidate_rule,
    line_efficiency,
    ranked_positional_weight_with_steps,
    smoothness_index,
    theoretical_min_stations,
)

router = APIRouter(prefix="/api/line-balancing", tags=["line-balancing"])


class TaskIn(BaseModel):
    id: str
    duration: float
    predecessors: list[str] = []


class SolveRequest(BaseModel):
    tasks: list[TaskIn]
    cycle_time: float | None = None
    available_time: float | None = None
    demand: int | None = None


class StationOut(BaseModel):
    index: int
    task_ids: list[str]
    total_time: float
    idle_time: float


class HeuristicResult(BaseModel):
    stations: list[StationOut]
    num_stations: int
    efficiency: float
    balance_delay: float
    smoothness_index: float


class SolveResponse(BaseModel):
    cycle_time: float
    total_work: float
    min_stations: int
    columns: dict[str, int]
    weights: dict[str, float]
    heuristics: dict[str, HeuristicResult]
    steps: list[dict]


def _resolve_cycle_time(req: SolveRequest) -> float:
    if req.cycle_time is not None:
        return req.cycle_time
    if req.available_time is not None and req.demand is not None:
        if req.available_time <= 0 or req.demand <= 0:
            raise ValueError("Available time and demand must be positive.")
        # course convention: floor, so the line is fast enough to meet demand
        return float(cycle_time_from_demand(req.available_time, req.demand))
    raise ValueError("Provide a cycle time, or available time and demand.")


def _result(stations: list[Station], cycle_time: float) -> HeuristicResult:
    return HeuristicResult(
        stations=[
            StationOut(
                index=s.index,
                task_ids=[t.id for t in s.tasks],
                total_time=s.total_time,
                idle_time=s.idle_time(cycle_time),
            )
            for s in stations
        ],
        num_stations=len(stations),
        efficiency=line_efficiency(stations, cycle_time),
        balance_delay=balance_delay(stations, cycle_time),
        smoothness_index=smoothness_index(stations, cycle_time),
    )


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    if not req.tasks:
        raise ValueError("Provide at least one task.")
    cycle_time = _resolve_cycle_time(req)
    tasks = [Task(t.id, t.duration, tuple(t.predecessors)) for t in req.tasks]
    # RPW runs first: its validate_tasks call is the input gate for all three
    rpw_stations, steps = ranked_positional_weight_with_steps(tasks, cycle_time)
    from core.line_balancing import positional_weights  # noqa: PLC0415

    solutions = {
        "lcr": largest_candidate_rule(tasks, cycle_time),
        "rpw": rpw_stations,
        "kilbridge_wester": kilbridge_wester(tasks, cycle_time),
    }
    return SolveResponse(
        cycle_time=cycle_time,
        total_work=sum(t.duration for t in tasks),
        min_stations=theoretical_min_stations(tasks, cycle_time),
        columns=kilbridge_columns(tasks),
        weights=positional_weights(tasks),
        heuristics={
            name: _result(stations, cycle_time)
            for name, stations in solutions.items()
        },
        steps=steps,
    )
```

Cleanup note: move the `positional_weights` import to the top-level import
block (it is in `core.line_balancing.__all__`); the inline form above is only
to show where it's used. Final import block adds `positional_weights` between
`line_efficiency` and `ranked_positional_weight_with_steps`.

In `api/main.py`, change the routers import to:

```python
from api.routers import line_balancing, lot_sizing, scheduling
```

and add with the other two:

```python
app.include_router(line_balancing.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 134 passed, none broken.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api_line_balancing.py
git commit -m "feat: add line-balancing solve endpoint with three heuristics"
```

---

### Task 3: Frontend lib — API types and balancing URL state

**Files:**
- Modify: `web/src/lib/api.ts`, `web/src/lib/urlState.ts`
- Test: `web/src/lib/urlState.test.ts` (append)

- [ ] **Step 1: Write the failing tests**

Append to `web/src/lib/urlState.test.ts` (merge the new names into the
existing `./urlState` import):

```ts
describe("line balancing URL state", () => {
  it("round-trips tasks with predecessors and a direct cycle time", () => {
    const inputs = {
      tasks: [
        { id: "A", duration: 5, predecessors: [] },
        { id: "F", duration: 4, predecessors: ["D", "E"] },
      ],
      cycleTime: 10,
      availableTime: null,
      demand: null,
    };
    expect(decodeBalancing("?" + encodeBalancing(inputs))).toEqual(inputs);
  });

  it("round-trips demand-mode inputs", () => {
    const inputs = {
      tasks: [{ id: "A", duration: 5, predecessors: [] }],
      cycleTime: null,
      availableTime: 480,
      demand: 70,
    };
    expect(decodeBalancing("?" + encodeBalancing(inputs))).toEqual(inputs);
  });

  it("returns null for malformed task strings or missing cycle info", () => {
    expect(decodeBalancing("")).toBeNull();
    expect(decodeBalancing("?t=A,5,&ct=abc")).toBeNull();
    expect(decodeBalancing("?t=A,x,&ct=10")).toBeNull();
    expect(decodeBalancing("?t=A,5,")).toBeNull(); // no ct and no at+dm
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — `encodeBalancing` / `decodeBalancing` not exported.

- [ ] **Step 3: Implement**

Append to `web/src/lib/api.ts`:

```ts
export type HeuristicName = "lcr" | "rpw" | "kilbridge_wester";

export interface BalancingStation {
  index: number;
  task_ids: string[];
  total_time: number;
  idle_time: number;
}

export interface HeuristicResult {
  stations: BalancingStation[];
  num_stations: number;
  efficiency: number;
  balance_delay: number;
  smoothness_index: number;
}

export interface RpwStep {
  kind: "rank" | "assign" | "skip" | "close";
  order?: string[];
  weights?: Record<string, number>;
  station?: number;
  task?: string;
  duration?: number;
  remaining?: number;
  reason?: "blocked" | "no_fit";
  missing?: string[];
  tasks?: string[];
  total?: number;
  idle?: number;
}

export interface BalancingResponse {
  cycle_time: number;
  total_work: number;
  min_stations: number;
  columns: Record<string, number>;
  weights: Record<string, number>;
  heuristics: Record<HeuristicName, HeuristicResult>;
  steps: RpwStep[];
}
```

Append to `web/src/lib/urlState.ts`:

```ts
export interface BalancingTask {
  id: string;
  duration: number;
  predecessors: string[];
}

export interface BalancingInputs {
  tasks: BalancingTask[];
  cycleTime: number | null; // direct mode...
  availableTime: number | null; // ...or demand mode (both null-able, one set)
  demand: number | null;
}

// Tasks encode as t=id,duration,pred.pred;... (predecessors joined by ".").
// Cycle time is ct=10 (direct) or at=480&dm=70 (derived, floored server-side).
export function encodeBalancing(inputs: BalancingInputs): string {
  const params = new URLSearchParams();
  params.set(
    "t",
    inputs.tasks
      .map((t) => [t.id, t.duration, t.predecessors.join(".")].join(","))
      .join(";"),
  );
  if (inputs.cycleTime !== null) {
    params.set("ct", String(inputs.cycleTime));
  } else {
    params.set("at", String(inputs.availableTime));
    params.set("dm", String(inputs.demand));
  }
  return params.toString();
}

export function decodeBalancing(search: string): BalancingInputs | null {
  const params = new URLSearchParams(search);
  const raw = params.get("t");
  if (!raw) return null;
  const tasks: BalancingTask[] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const duration = Number(fields[1]);
    if (Number.isNaN(duration)) return null;
    tasks.push({
      id: fields[0],
      duration,
      predecessors: fields[2] ? fields[2].split(".").filter(Boolean) : [],
    });
  }
  const ct = params.get("ct");
  if (ct !== null) {
    const cycleTime = Number(ct);
    if (Number.isNaN(cycleTime)) return null;
    return { tasks, cycleTime, availableTime: null, demand: null };
  }
  const at = params.get("at");
  const dm = params.get("dm");
  if (at === null || dm === null) return null;
  const availableTime = Number(at);
  const demand = Number(dm);
  if (Number.isNaN(availableTime) || Number.isNaN(demand)) return null;
  return { tasks, cycleTime: null, availableTime, demand };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 13 passed. Also `npm run build` — clean.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib
git commit -m "feat: add line-balancing api types and url state"
```

---

### Task 4: Precedence-diagram trace helper

**Files:**
- Create: `web/src/pages/line-balancing/diagram.ts`
- Test: `web/src/pages/line-balancing/diagram.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/pages/line-balancing/diagram.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { precedenceTraces } from "./diagram";

const TASKS = [
  { id: "A", duration: 5, predecessors: [] },
  { id: "B", duration: 3, predecessors: ["A"] },
  { id: "C", duration: 4, predecessors: ["A"] },
];
const COLUMNS = { A: 1, B: 2, C: 2 };

describe("precedenceTraces", () => {
  it("positions nodes by kilbridge column and spreads within a column", () => {
    const [, nodes] = precedenceTraces(TASKS, COLUMNS) as any[];
    expect(nodes.text).toEqual(["A", "B", "C"]);
    expect(nodes.x).toEqual([1, 2, 2]); // x = column
    expect(nodes.y[1]).not.toEqual(nodes.y[2]); // B and C spread apart
  });

  it("draws one edge per predecessor link, null-separated", () => {
    const [edges] = precedenceTraces(TASKS, COLUMNS) as any[];
    // A->B and A->C: 2 links x (from, to, null) = 6 points
    expect(edges.x).toHaveLength(6);
    expect(edges.x[2]).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (in `web/`): `npm test`
Expected: FAIL — module `./diagram` doesn't exist.

- [ ] **Step 3: Implement**

Create `web/src/pages/line-balancing/diagram.ts`:

```ts
import type { Data } from "plotly.js";
import type { BalancingTask } from "../../lib/urlState";

/** Lay the precedence diagram out on the Kilbridge grid: x = column
 * (precedence depth), y spreads the tasks within a column around 0.
 * Returns [edge trace, node trace] for a Plotly scatter. */
export function precedenceTraces(
  tasks: BalancingTask[],
  columns: Record<string, number>,
): Data[] {
  const byColumn = new Map<number, string[]>();
  for (const t of tasks) {
    const col = columns[t.id];
    if (!byColumn.has(col)) byColumn.set(col, []);
    byColumn.get(col)!.push(t.id);
  }
  const pos = new Map<string, { x: number; y: number }>();
  for (const [col, ids] of byColumn) {
    ids.forEach((id, i) => pos.set(id, { x: col, y: i - (ids.length - 1) / 2 }));
  }

  const edgeX: (number | null)[] = [];
  const edgeY: (number | null)[] = [];
  for (const t of tasks) {
    for (const p of t.predecessors) {
      const from = pos.get(p);
      const to = pos.get(t.id);
      if (!from || !to) continue;
      edgeX.push(from.x, to.x, null); // null breaks the line between edges
      edgeY.push(from.y, to.y, null);
    }
  }

  const durations = new Map(tasks.map((t) => [t.id, t.duration]));
  const ids = tasks.map((t) => t.id);
  return [
    {
      type: "scatter",
      mode: "lines",
      x: edgeX,
      y: edgeY,
      line: { color: "#cbd5e1", width: 1.5 },
      hoverinfo: "skip",
      showlegend: false,
    },
    {
      type: "scatter",
      mode: "markers+text",
      x: ids.map((id) => pos.get(id)!.x),
      y: ids.map((id) => pos.get(id)!.y),
      text: ids,
      textposition: "middle center",
      textfont: { color: "#ffffff", size: 11, family: "Inter, sans-serif" },
      marker: { size: 30, color: "#0d9488" },
      hovertext: ids.map((id) => `${id}: ${durations.get(id)} time units`),
      hoverinfo: "text",
      showlegend: false,
    },
  ];
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 15 passed.

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/line-balancing
git commit -m "feat: add precedence diagram traces on the kilbridge grid"
```

---

### Task 5: Tasks table and RPW teaching drawer

**Files:**
- Create: `web/src/pages/line-balancing/TasksTable.tsx`, `web/src/pages/line-balancing/RpwDrawer.tsx`

- [ ] **Step 1: TasksTable**

Create `web/src/pages/line-balancing/TasksTable.tsx` (reuses the
`DemandTable.css` table styling like JobsTable does; predecessors edit as
free text, parsed on every keystroke — separators: comma, space, dot):

```tsx
import "../../components/DemandTable.css";
import type { BalancingTask } from "../../lib/urlState";

const parsePreds = (text: string): string[] =>
  text.split(/[\s,.;]+/).filter((p) => p.length > 0);

export function TasksTable({
  tasks,
  onChange,
}: {
  tasks: BalancingTask[];
  onChange: (next: BalancingTask[]) => void;
}) {
  const setTask = (i: number, patch: Partial<BalancingTask>) => {
    const next = [...tasks];
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };

  const addTask = () => {
    const used = new Set(tasks.map((t) => t.id));
    let id = `T${tasks.length + 1}`;
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode(65 + i);
      if (!used.has(letter)) {
        id = letter;
        break;
      }
    }
    onChange([...tasks, { id, duration: 1, predecessors: [] }]);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        Tasks (duration, predecessors)
      </div>
      <table className="demand-table">
        <thead>
          <tr>
            <th>task</th>
            <th>time</th>
            <th>preds</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t, i) => (
            <tr key={i}>
              <td style={{ width: 48 }}>
                <input value={t.id} onChange={(e) => setTask(i, { id: e.target.value })} />
              </td>
              <td style={{ width: 64 }}>
                <input
                  type="number"
                  step="any"
                  min={0}
                  value={Number.isNaN(t.duration) ? "" : t.duration}
                  onChange={(e) => setTask(i, { duration: e.target.valueAsNumber })}
                />
              </td>
              <td>
                <input
                  value={t.predecessors.join(",")}
                  placeholder="—"
                  onChange={(e) => setTask(i, { predecessors: parsePreds(e.target.value) })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={addTask}>+ task</button>
        <button onClick={() => tasks.length > 1 && onChange(tasks.slice(0, -1))}>
          − task
        </button>
      </div>
      <div className="demand-table-hint">preds: comma-separated task IDs</div>
    </div>
  );
}
```

- [ ] **Step 2: RpwDrawer**

Create `web/src/pages/line-balancing/RpwDrawer.tsx`:

```tsx
import type { RpwStep } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: RpwStep) {
  if (step.kind === "rank") {
    return (
      <>
        <b>Rank by positional weight</b> — each task's own time plus everything
        downstream of it:{" "}
        <span className="mono">
          {step.order!.map((id) => `${id} (${formatNumber(step.weights![id])})`).join(" → ")}
        </span>
        . Heavy weights head long chains of work, so they go first.
      </>
    );
  }
  if (step.kind === "assign") {
    return (
      <>
        <b>{step.task}</b> is the highest-ranked task that is unblocked and
        fits — assign it to station {step.station}.{" "}
        <span className="step-good">
          {formatNumber(step.remaining!)} time left in the station.
        </span>
      </>
    );
  }
  if (step.kind === "skip") {
    if (step.reason === "blocked") {
      return (
        <>
          <b>{step.task}</b> can't start yet — predecessor
          {step.missing!.length > 1 ? "s" : ""} {step.missing!.join(", ")} not
          assigned. Skip it for now.
        </>
      );
    }
    return (
      <>
        <b>{step.task}</b> is unblocked but needs {formatNumber(step.duration!)}{" "}
        with only {formatNumber(step.remaining!)} left in station {step.station}.{" "}
        <span className="step-bad">Doesn't fit — skip.</span>
      </>
    );
  }
  return (
    <>
      <b>Station {step.station} closes</b> with {step.tasks!.join(", ")}:{" "}
      {formatNumber(step.total!)} used, {formatNumber(step.idle!)} idle.
    </>
  );
}

export function RpwDrawer({ steps }: { steps: RpwStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Ranked Positional Weight, narrated by the solver"
      question="Why these stations?"
      teaser="watch RPW rank the tasks and fill each station, on this exact data"
      describe={describe}
    />
  );
}
```

- [ ] **Step 3: Build check and commit**

Run (in `web/`): `npm run build` — clean (components are not yet wired into a
page, but must compile).

```bash
git add web/src/pages/line-balancing
git commit -m "feat: add tasks table and rpw drawer components"
```

---

### Task 6: Line Balancing page — view, route, module flip

**Files:**
- Create: `web/src/pages/line-balancing/presets.ts`, `web/src/pages/line-balancing/LineBalancingPage.tsx`, `web/src/pages/line-balancing/BalancingView.tsx`
- Modify: `web/src/App.tsx`, `web/src/modules.ts`

- [ ] **Step 1: Presets**

Create `web/src/pages/line-balancing/presets.ts`:

```ts
import type { BalancingInputs } from "../../lib/urlState";

export const BALANCING_PRESETS: Record<string, BalancingInputs> = {
  "Six-task demo": {
    tasks: [
      { id: "A", duration: 5, predecessors: [] },
      { id: "B", duration: 3, predecessors: ["A"] },
      { id: "C", duration: 4, predecessors: ["A"] },
      { id: "D", duration: 2, predecessors: ["B"] },
      { id: "E", duration: 6, predecessors: ["C"] },
      { id: "F", duration: 4, predecessors: ["D", "E"] },
    ],
    cycleTime: 10,
    availableTime: null,
    demand: null,
  },
  "From demand (480 min, 70 units)": {
    tasks: [
      { id: "A", duration: 3, predecessors: [] },
      { id: "B", duration: 4, predecessors: ["A"] },
      { id: "C", duration: 2, predecessors: ["A"] },
      { id: "D", duration: 5, predecessors: ["B", "C"] },
      { id: "E", duration: 3, predecessors: ["D"] },
    ],
    cycleTime: null,
    availableTime: 480,
    demand: 70,
  },
};
```

- [ ] **Step 2: BalancingView**

Create `web/src/pages/line-balancing/BalancingView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { BalancingResponse, HeuristicName } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { BalancingInputs } from "../../lib/urlState";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { precedenceTraces } from "./diagram";
import { BALANCING_PRESETS } from "./presets";
import { RpwDrawer } from "./RpwDrawer";
import { TasksTable } from "./TasksTable";

const LABELS: Record<HeuristicName, string> = {
  lcr: "LCR",
  rpw: "RPW",
  kilbridge_wester: "Kilbridge–Wester",
};
const ORDER: HeuristicName[] = ["lcr", "rpw", "kilbridge_wester"];

export function BalancingView({
  inputs,
  onInputs,
}: {
  inputs: BalancingInputs;
  onInputs: (next: BalancingInputs) => void;
}) {
  const [result, setResult] = useState<BalancingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HeuristicName>("rpw");
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<BalancingResponse>("/line-balancing/solve", {
      tasks: debounced.tasks.map((t) => ({
        id: t.id,
        duration: t.duration,
        predecessors: t.predecessors,
      })),
      cycle_time: debounced.cycleTime,
      available_time: debounced.availableTime,
      demand: debounced.demand,
    })
      .then((res) => {
        if (!cancelled) {
          setResult(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Request failed");
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  const demandMode = inputs.cycleTime === null;
  // best = fewest stations, then smoothest; ties keep the earlier heuristic
  const bestName = result
    ? ORDER.reduce((a, b) => {
        const ra = result.heuristics[a];
        const rb = result.heuristics[b];
        const better =
          rb.num_stations < ra.num_stations ||
          (rb.num_stations === ra.num_stations &&
            rb.smoothness_index < ra.smoothness_index);
        return better ? b : a;
      })
    : null;
  const best = bestName ? result!.heuristics[bestName] : null;
  const plan = result?.heuristics[selected];

  const durations = new Map(inputs.tasks.map((t) => [t.id, t.duration]));
  const stationRows = (plan?.stations ?? []).map((s) => {
    let clock = 0;
    return {
      label: `Station ${s.index}`,
      jobs: s.task_ids.map((id) => {
        const d = durations.get(id) ?? 0;
        const segment = { id, start: clock, end: clock + d };
        clock += d;
        return segment;
      }),
    };
  });

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Line Balancing</h1>
          <div className="subtitle module-sub">
            Split assembly work into stations that keep pace with demand.
          </div>
        </div>
        <TasksTable tasks={inputs.tasks} onChange={(tasks) => onInputs({ ...inputs, tasks })} />
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Cycle time</div>
          <div className="mode-pills">
            <button
              className={demandMode ? "" : "active"}
              onClick={() =>
                onInputs({ ...inputs, cycleTime: 10, availableTime: null, demand: null })
              }
            >
              Given
            </button>
            <button
              className={demandMode ? "active" : ""}
              onClick={() =>
                onInputs({ ...inputs, cycleTime: null, availableTime: 480, demand: 60 })
              }
            >
              From demand
            </button>
          </div>
        </div>
        {demandMode ? (
          <div className="row">
            <NumberField
              label="Available time"
              value={inputs.availableTime ?? 0}
              onChange={(availableTime) => onInputs({ ...inputs, availableTime })}
            />
            <NumberField
              label="Demand"
              value={inputs.demand ?? 0}
              onChange={(demand) => onInputs({ ...inputs, demand })}
            />
          </div>
        ) : (
          <NumberField
            label="Cycle time CT"
            value={inputs.cycleTime ?? 0}
            onChange={(cycleTime) => onInputs({ ...inputs, cycleTime })}
          />
        )}
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = BALANCING_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(BALANCING_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && best && bestName && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Best balance — {LABELS[bestName]}
              </div>
              <div className="hero-value">
                {best.num_stations} stations{" "}
                <span className="hero-detail">
                  efficiency {formatNumber(best.efficiency * 100)}% · theoretical
                  minimum {result.min_stations} · CT {formatNumber(result.cycle_time)}
                  {demandMode ? " (from demand, rounded down)" : ""}
                </span>
              </div>
            </div>
            <div className="hero-orders">
              {best.stations.map((s) => s.task_ids.join(" ")).join("  ·  ")}
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            {ORDER.map((name) => (
              <MetricCard
                key={name}
                label={LABELS[name]}
                value={`${result.heuristics[name].num_stations} stations`}
                detail={`${formatNumber(result.heuristics[name].efficiency * 100)}% efficient · SI ${formatNumber(result.heuristics[name].smoothness_index)}`}
                selected={selected === name}
                onClick={() => setSelected(name)}
              />
            ))}
          </div>
        )}
        {result && (
          <PlotCard
            label="Precedence diagram — columns are Kilbridge levels"
            data={precedenceTraces(inputs.tasks, result.columns)}
            layout={{
              xaxis: { dtick: 1, title: { text: "column" }, zeroline: false },
              yaxis: { visible: false },
            }}
            height={220}
          />
        )}
        {plan && result && (
          <PlotCard
            label={`${LABELS[selected]} stations — dotted line is the cycle time`}
            data={ganttTraces(stationRows)}
            layout={{
              barmode: "overlay",
              xaxis: { title: { text: "time in station" } },
              yaxis: { autorange: "reversed" },
              shapes: [
                {
                  type: "line",
                  x0: result.cycle_time,
                  x1: result.cycle_time,
                  yref: "paper",
                  y0: 0,
                  y1: 1,
                  line: { color: "#dc2626", width: 1.5, dash: "dot" },
                },
              ],
            }}
            height={200}
          />
        )}
        {result && <RpwDrawer steps={result.steps} />}
      </div>
    </>
  );
}
```

- [ ] **Step 3: Page wrapper with URL state**

Create `web/src/pages/line-balancing/LineBalancingPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeBalancing, encodeBalancing } from "../../lib/urlState";
import type { BalancingInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { BALANCING_PRESETS } from "./presets";
import { BalancingView } from "./BalancingView";

export default function LineBalancingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputs, setInputs] = useState<BalancingInputs>(
    () =>
      decodeBalancing("?" + searchParams.toString()) ??
      BALANCING_PRESETS["Six-task demo"],
  );

  const update = (next: BalancingInputs) => {
    setInputs(next);
    setSearchParams(encodeBalancing(next), { replace: true });
  };

  return (
    <div className="workbench">
      <BalancingView inputs={inputs} onInputs={update} />
    </div>
  );
}
```

- [ ] **Step 4: Route and module flip**

In `web/src/App.tsx`, add the import:

```tsx
import LineBalancingPage from "./pages/line-balancing/LineBalancingPage";
```

and add this route directly above the `/lot-sizing` route:

```tsx
<Route path="/line-balancing" element={<LineBalancingPage />} />
```

In `web/src/modules.ts`, replace the line-balancing entry with:

```ts
  { path: "/line-balancing", name: "Line Balancing", decision: "How do I split assembly work into balanced stations?", icon: Scale, ready: true, exampleSearch: "?t=A,5,;B,3,A;C,4,A;D,2,B;E,6,C;F,4,D.E&ct=10" },
```

- [ ] **Step 5: Verify in the browser**

Run uvicorn (repo root): `.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000` after `npm run build` (in `web/`), open `http://localhost:8000/line-balancing` and check: hero shows **3 stations**, efficiency **80%**, groupings `A C · E B · D F`; three comparison cards (KW selected shows `[A,C] [B,E] [D,F]` in its station chart); precedence diagram lays A→(B,C)→(D,E)→F left to right; station chart bars stop at the dotted CT line; switching the cycle-time pills to "From demand" with 480/70 recomputes with CT 6; emptying a predecessor field recovers; an unknown predecessor shows the inline core message; presets and the Home example link work. Stop the server.

- [ ] **Step 6: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src
git commit -m "feat: add line balancing view with heuristic comparison and diagrams"
```

---

### Task 7: Playwright smoke, docs, final verification

**Files:**
- Create: `web/e2e/line-balancing.spec.ts`
- Modify: `README.md`

- [ ] **Step 1: Write the smoke spec**

Create `web/e2e/line-balancing.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

// Hand-traced ground truth: A(5) B(3,A) C(4,A) D(2,B) E(6,C) F(4,DE), CT 10
// -> all three heuristics: 3 stations, efficiency 80%; RPW weights A=24...
test("line balancing solves the shared-link example with all three heuristics", async ({ page }) => {
  await page.goto("/line-balancing?t=A,5,;B,3,A;C,4,A;D,2,B;E,6,C;F,4,D.E&ct=10");
  await expect(page.getByText("3 stations").first()).toBeVisible();
  await expect(page.getByText("80%").first()).toBeVisible();
  await expect(page.getByText("Kilbridge–Wester")).toBeVisible();
});

test("teaching drawer narrates the rpw ranking", async ({ page }) => {
  await page.goto("/line-balancing?t=A,5,;B,3,A;C,4,A;D,2,B;E,6,C;F,4,D.E&ct=10");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/positional weight/i).first()).toBeVisible();
  await expect(page.getByText(/A \(24\)/).first()).toBeVisible();
});
```

- [ ] **Step 2: Run the smoke tests**

Run (in `web/`): `npm run e2e`
Expected: 7 passed (2 new + 5 existing).

- [ ] **Step 3: Update the README roadmap line**

In `README.md`, replace

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅ — remaining modules rolling out one by one
```

with

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅, Line Balancing ✅ — remaining modules rolling out one by one
```

- [ ] **Step 4: Full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -q` — 134 passed.
Run (in `web/`): `npm test` (15 passed), `npm run build` (clean), `npm run e2e` (7 passed).

- [ ] **Step 5: Commit**

```bash
git add web/e2e README.md
git commit -m "test: add playwright smoke for line balancing; update roadmap"
```

---

## Self-review notes

- **Spec coverage:** `/api/line-balancing/solve` with 3 heuristics + metrics + precedence layout ✓ (Task 2, columns double as diagram coordinates); teaching steps recorded in core with TDD ✓ (Task 1 — the shared loop records, so LCR/KW narration is a later one-liner); Phase-1 scope items in the React UI — editable task table ✓, cycle time direct or from demand (floored) ✓, precedence diagram ✓, station-grouping visual ✓, side-by-side comparison ✓, presets ✓ (Tasks 5–6); ergonomics — debounce, sharable URLs, inline 422 errors ✓; Playwright smoke on hand-traced numbers ✓ (Task 7).
- **Type consistency:** `StationOut` (API) ↔ `BalancingStation` (TS) fields match (`index`, `task_ids`, `total_time`, `idle_time`) ✓; heuristic keys `lcr/rpw/kilbridge_wester` consistent across router dict, `HeuristicName`, `LABELS`, `ORDER` ✓; `RpwStep` TS fields match the core step dicts ✓; `BalancingTask`/`BalancingInputs` used by urlState, presets, TasksTable, diagram, view ✓; `precedenceTraces(tasks, columns)` signature identical in test and view ✓.
- **Conventions:** untouched — floor CT from demand, tie-breaks, SI vs CT all stay in core; the API only forwards. The hero "best" rule (fewest stations, then lowest SI, earlier heuristic wins ties) is a UI presentation choice, not a course convention.
- **Known limitation:** task IDs containing `,` `;` or `.` break the URL encoding (decode → null → preset fallback) — same trade-off as the scheduling module, fine for course-style IDs.
