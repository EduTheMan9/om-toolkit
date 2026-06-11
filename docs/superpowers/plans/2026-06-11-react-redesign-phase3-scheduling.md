# React Redesign Phase 3: Scheduling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Scheduling module in the React app: single-machine dispatching rules (with the exact optimizers) compared side by side, and the two-machine Johnson flow shop with a Gantt chart and a self-narrating teaching drawer.

**Architecture:** A new `api/routers/scheduling.py` wraps the untouched `core/scheduling` solvers (`/api/scheduling/dispatch` and `/api/scheduling/johnson`). `core/` gains one function — `johnson_sequence_with_steps`, a Johnson variant that records each pick as a structured step (the same pattern as `silver_meal_with_steps`). The frontend gains a `/scheduling` page with two mode pills (single machine / flow shop), a shared `JobsTable` input component, a Plotly Gantt helper, and a generic `StepPlayer` extracted from the lot-sizing `TeachingDrawer`.

**Tech Stack:** Python 3.11+, FastAPI, pytest; React 18 + TypeScript, Plotly (react-plotly factory), Vitest, Playwright. All already installed — no new dependencies.

**Context for the engineer:** This repo is an Operations Management teaching toolkit. All solver math lives in `core/` as pure Python with hand-traced tests in `tests/` — never change solver *behavior* (refactoring that provably preserves it, like the delegation in Task 1, is fine because the existing hand-traced tests prove it). The design spec is `docs/superpowers/specs/2026-06-11-react-redesign-design.md`; the scheduling math/conventions spec is `docs/superpowers/specs/2026-06-11-scheduling-design.md`. The lot-sizing module (already shipped) is the pattern to copy: `api/routers/lot_sizing.py`, `web/src/pages/lot-sizing/`. Run Python via the project venv: `.\.venv\Scripts\python.exe`. The repo root is the pytest rootdir, so `import api` / `import core` work in tests. Frontend commands run in `web/`.

**Reference — hand-traced examples used everywhere below (already encoded in `tests/test_dispatching.py`, `tests/test_johnson.py`, `tests/test_optimal.py`):**

*Dispatching* — jobs (processing time, due date): A(6,8) B(2,6) C(8,18) D(3,15) E(9,23).
- FCFS A,B,C,D,E → avg completion **15.4**, avg tardiness 2.2, max 5, 3 tardy.
- SPT B,D,A,C,E → avg completion **13.0** (provably minimal), 3 tardy.
- EDD B,A,D,C,E → avg tardiness **1.2**, total tardiness 6, **2 tardy**.
- LPT E,C,A,D,B → avg completion **20.6**.
- Moore–Hodgson B,A,D,E,C → **1 tardy** (provably minimal).
- Exact min total tardiness → **6.0** (EDD happens to be optimal here).

*Johnson* — jobs (M1, M2): J1(3,6) J2(5,2) J3(1,2) J4(6,6) J5(7,5).
Pick order: 1 (J3 on M1)→front slot 1; 2 (J2 on M2)→back slot 5; 3 (J1 on M1)→front slot 2; 5 (J5 on M2)→back slot 4; 6 (J4, own-tie counts M1-side)→front slot 3.
Sequence **J3, J1, J4, J5, J2**, makespan **24**. The input order J1…J5 gives makespan **27** (M1: J1 0–3, J2 3–8, J3 8–9, J4 9–15, J5 15–22; M2: J1 3–9, J2 9–11, J3 11–13, J4 15–21, J5 22–27).

---

### Task 1: Johnson step trace in core/

**Files:**
- Modify: `core/scheduling/johnson.py`, `core/scheduling/__init__.py`
- Test: `tests/test_johnson.py` (append)

The teaching drawer replays Johnson's picks on the user's data. The solver
records its own decisions as structured dicts; `johnson_sequence` keeps its
exact current behavior by delegating (the existing hand-traced tests prove
the refactor preserved it).

Step schema (`slot` is the 1-based final position in the sequence):
- `{"kind": "pick", "job": "J3", "time": 1.0, "machine": 1, "placement": "front", "slot": 1}`
- `{"kind": "done", "sequence": ["J3", "J1", "J4", "J5", "J2"]}` — closing summary.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_johnson.py`:

```python
def test_johnson_with_steps_narrates_the_worked_example():
    """Hand trace of the picks: 1 (J3,M1)->front slot 1; 2 (J2,M2)->back slot 5;
    3 (J1,M1)->front slot 2; 5 (J5,M2)->back slot 4; 6 (J4, tie->M1)->front slot 3."""
    from core.scheduling.johnson import johnson_sequence_with_steps

    sequence, steps = johnson_sequence_with_steps(JOBS)
    assert [j.id for j in sequence] == ["J3", "J1", "J4", "J5", "J2"]

    picks = [
        (s["job"], s["machine"], s["placement"], s["slot"])
        for s in steps
        if s["kind"] == "pick"
    ]
    assert picks == [
        ("J3", 1, "front", 1),
        ("J2", 2, "back", 5),
        ("J1", 1, "front", 2),
        ("J5", 2, "back", 4),
        ("J4", 1, "front", 3),
    ]
    assert steps[0]["time"] == pytest.approx(1.0)
    assert steps[-1] == {"kind": "done", "sequence": ["J3", "J1", "J4", "J5", "J2"]}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_johnson.py -q`
Expected: FAIL — `ImportError: cannot import name 'johnson_sequence_with_steps'`.

- [ ] **Step 3: Implement by refactoring johnson_sequence**

In `core/scheduling/johnson.py`, REPLACE the existing `johnson_sequence` function with:

```python
def johnson_sequence_with_steps(
    jobs: list[FlowShopJob],
) -> tuple[list[FlowShopJob], list[dict]]:
    """Johnson's rule that records each pick while it runs, so the UI can
    replay the algorithm step by step on the user's data.
    Slots are the 1-based final positions in the sequence."""
    validate_flow_shop_jobs(jobs)
    n = len(jobs)
    front: list[FlowShopJob] = []
    back: list[FlowShopJob] = []  # built in reverse, flipped at the end
    steps: list[dict] = []
    remaining = list(jobs)
    while remaining:
        best = min(
            remaining,
            key=lambda j: (
                min(j.time_m1, j.time_m2),
                0 if j.time_m1 <= j.time_m2 else 1,  # M1-side wins ties
                j.id,
            ),
        )
        remaining.remove(best)
        m1_side = best.time_m1 <= best.time_m2
        if m1_side:
            front.append(best)
            slot = len(front)
        else:
            back.append(best)
            slot = n - len(back) + 1
        steps.append(
            {
                "kind": "pick",
                "job": best.id,
                "time": min(best.time_m1, best.time_m2),
                "machine": 1 if m1_side else 2,
                "placement": "front" if m1_side else "back",
                "slot": slot,
            }
        )
    sequence = front + back[::-1]
    steps.append({"kind": "done", "sequence": [j.id for j in sequence]})
    return sequence, steps


def johnson_sequence(jobs: list[FlowShopJob]) -> list[FlowShopJob]:
    sequence, _ = johnson_sequence_with_steps(jobs)
    return sequence
```

In `core/scheduling/__init__.py`, update the `.johnson` import block and `__all__` (keep both alphabetical):

```python
from .johnson import (
    TwoMachineSchedule,
    flow_shop_schedule,
    johnson_sequence,
    johnson_sequence_with_steps,
    validate_flow_shop_jobs,
)
```

and add `"johnson_sequence_with_steps",` to `__all__` right after `"johnson_sequence",`.

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 124 passed (the pre-existing Johnson hand-trace tests prove the refactor preserved behavior).

- [ ] **Step 5: Commit**

```bash
git add core/scheduling tests/test_johnson.py
git commit -m "feat: add johnson pick trace for the teaching drawer"
```

---

### Task 2: Dispatch endpoint (all rules + exact optimizers)

**Files:**
- Create: `api/routers/scheduling.py`
- Modify: `api/main.py`
- Test: `tests/test_api_scheduling.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_scheduling.py`:

```python
"""Scheduling API endpoints, validated against the hand-traced examples
(see tests/test_dispatching.py, tests/test_optimal.py, tests/test_johnson.py)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

DISPATCH_REQUEST = {
    "jobs": [
        {"id": "A", "processing_time": 6, "due_date": 8},
        {"id": "B", "processing_time": 2, "due_date": 6},
        {"id": "C", "processing_time": 8, "due_date": 18},
        {"id": "D", "processing_time": 3, "due_date": 15},
        {"id": "E", "processing_time": 9, "due_date": 23},
    ]
}


def test_dispatch_endpoint_worked_example():
    response = client.post("/api/scheduling/dispatch", json=DISPATCH_REQUEST)
    assert response.status_code == 200
    body = response.json()
    methods = body["methods"]
    assert methods["fcfs"]["avg_completion_time"] == pytest.approx(15.4)
    assert methods["spt"]["sequence"] == ["B", "D", "A", "C", "E"]
    assert methods["spt"]["avg_completion_time"] == pytest.approx(13.0)
    assert methods["edd"]["avg_tardiness"] == pytest.approx(1.2)
    assert methods["edd"]["num_tardy"] == 2
    assert methods["lpt"]["avg_completion_time"] == pytest.approx(20.6)
    assert methods["moore_hodgson"]["num_tardy"] == 1
    assert methods["min_total_tardiness"]["total_tardiness"] == pytest.approx(6.0)
    assert body["optimal_capped"] is False
    # timeline for the Gantt: back-to-back from t = 0
    assert methods["fcfs"]["schedule"][0] == {"id": "A", "start": 0.0, "end": 6.0}


def test_dispatch_skips_exact_dp_beyond_the_cap():
    jobs = [
        {"id": f"J{i:02d}", "processing_time": 1, "due_date": 5} for i in range(16)
    ]
    response = client.post("/api/scheduling/dispatch", json={"jobs": jobs})
    assert response.status_code == 200
    body = response.json()
    assert body["optimal_capped"] is True
    assert "min_total_tardiness" not in body["methods"]
    assert "moore_hodgson" in body["methods"]  # O(n log n), never capped


def test_dispatch_rejects_duplicate_ids_with_core_message():
    bad = {"jobs": [DISPATCH_REQUEST["jobs"][0], DISPATCH_REQUEST["jobs"][0]]}
    response = client.post("/api/scheduling/dispatch", json=bad)
    assert response.status_code == 422
    assert "Duplicate" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_scheduling.py -q`
Expected: FAIL — 404, route does not exist.

- [ ] **Step 3: Implement the router**

Create `api/routers/scheduling.py`:

```python
"""Scheduling endpoints: single-machine dispatching and Johnson flow shop."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.scheduling import (
    MAX_OPTIMAL_JOBS,
    RULES,
    Job,
    build_schedule,
    min_total_tardiness,
    moore_hodgson,
    schedule_metrics,
    validate_jobs,
)

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])


class DispatchJobIn(BaseModel):
    id: str
    processing_time: float
    due_date: float


class DispatchRequest(BaseModel):
    jobs: list[DispatchJobIn]


class ScheduledJobOut(BaseModel):
    id: str
    start: float
    end: float


class MethodResult(BaseModel):
    sequence: list[str]
    schedule: list[ScheduledJobOut]
    avg_completion_time: float
    avg_tardiness: float
    total_tardiness: float
    max_tardiness: float
    num_tardy: int


class DispatchResponse(BaseModel):
    methods: dict[str, MethodResult]
    optimal_capped: bool


@router.post("/dispatch", response_model=DispatchResponse)
def dispatch(req: DispatchRequest) -> DispatchResponse:
    jobs = [Job(j.id, j.processing_time, j.due_date) for j in req.jobs]
    # RULES are bare sort keys; validate explicitly so bad input fails fast
    # with core's human-readable message (the ValueError handler maps it to 422).
    validate_jobs(jobs)
    sequences = {name.lower(): rule(jobs) for name, rule in RULES.items()}
    sequences["moore_hodgson"] = moore_hodgson(jobs)
    capped = len(jobs) > MAX_OPTIMAL_JOBS  # the subset DP doubles per job
    if not capped:
        sequences["min_total_tardiness"], _ = min_total_tardiness(jobs)
    methods = {}
    for name, seq in sequences.items():
        schedule = build_schedule(seq)
        methods[name] = MethodResult(
            sequence=[j.id for j in seq],
            schedule=[
                ScheduledJobOut(id=s.id, start=s.start, end=s.end) for s in schedule
            ],
            **schedule_metrics(schedule, jobs),
        )
    return DispatchResponse(methods=methods, optimal_capped=capped)
```

In `api/main.py`, change the routers import to:

```python
from api.routers import lot_sizing, scheduling
```

and add directly under `app.include_router(lot_sizing.router)`:

```python
app.include_router(scheduling.router)
```

(Both must stay ABOVE the `/{path:path}` SPA catch-all at the bottom of the file — route order matters.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_scheduling.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api_scheduling.py
git commit -m "feat: add dispatching endpoint comparing rules and exact optima"
```

---

### Task 3: Johnson endpoint (schedule + steps + input-order baseline)

**Files:**
- Modify: `api/routers/scheduling.py`
- Test: `tests/test_api_scheduling.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_scheduling.py`:

```python
JOHNSON_REQUEST = {
    "jobs": [
        {"id": "J1", "time_m1": 3, "time_m2": 6},
        {"id": "J2", "time_m1": 5, "time_m2": 2},
        {"id": "J3", "time_m1": 1, "time_m2": 2},
        {"id": "J4", "time_m1": 6, "time_m2": 6},
        {"id": "J5", "time_m1": 7, "time_m2": 5},
    ]
}


def test_johnson_endpoint_worked_example():
    response = client.post("/api/scheduling/johnson", json=JOHNSON_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["sequence"] == ["J3", "J1", "J4", "J5", "J2"]
    assert body["makespan"] == pytest.approx(24.0)
    # baseline for the comparison card: run the jobs in the typed order
    assert body["input_order_makespan"] == pytest.approx(27.0)
    assert body["machine2"][0] == {"id": "J3", "start": 1.0, "end": 3.0}
    # pick narration is included for the teaching drawer
    assert body["steps"][0]["job"] == "J3"
    assert body["steps"][-1]["kind"] == "done"


def test_johnson_rejects_nonpositive_time_with_core_message():
    bad = {"jobs": [{"id": "A", "time_m1": 0, "time_m2": 2}]}
    response = client.post("/api/scheduling/johnson", json=bad)
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_scheduling.py -q`
Expected: the two new tests FAIL with 404.

- [ ] **Step 3: Implement the endpoint**

In `api/routers/scheduling.py`, extend the core import to:

```python
from core.scheduling import (
    MAX_OPTIMAL_JOBS,
    RULES,
    FlowShopJob,
    Job,
    build_schedule,
    flow_shop_schedule,
    johnson_sequence_with_steps,
    min_total_tardiness,
    moore_hodgson,
    schedule_metrics,
    validate_jobs,
)
```

and add below the dispatch endpoint:

```python
class FlowShopJobIn(BaseModel):
    id: str
    time_m1: float
    time_m2: float


class JohnsonRequest(BaseModel):
    jobs: list[FlowShopJobIn]


class JohnsonResponse(BaseModel):
    sequence: list[str]
    machine1: list[ScheduledJobOut]
    machine2: list[ScheduledJobOut]
    makespan: float
    input_order_makespan: float
    steps: list[dict]


@router.post("/johnson", response_model=JohnsonResponse)
def johnson(req: JohnsonRequest) -> JohnsonResponse:
    jobs = [FlowShopJob(j.id, j.time_m1, j.time_m2) for j in req.jobs]
    sequence, steps = johnson_sequence_with_steps(jobs)  # validates first
    schedule = flow_shop_schedule(sequence)
    # the "do nothing" baseline: run the jobs in the order they were typed
    input_order_makespan = flow_shop_schedule(jobs).makespan
    return JohnsonResponse(
        sequence=[j.id for j in sequence],
        machine1=[
            ScheduledJobOut(id=s.id, start=s.start, end=s.end)
            for s in schedule.machine1
        ],
        machine2=[
            ScheduledJobOut(id=s.id, start=s.start, end=s.end)
            for s in schedule.machine2
        ],
        makespan=schedule.makespan,
        input_order_makespan=input_order_makespan,
        steps=steps,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 129 passed, none broken.

- [ ] **Step 5: Commit**

```bash
git add api/routers/scheduling.py tests/test_api_scheduling.py
git commit -m "feat: add johnson endpoint with gantt timeline and pick narration"
```

---

### Task 4: Frontend lib — API types, job URL state, Gantt traces, number format

**Files:**
- Modify: `web/src/lib/api.ts`, `web/src/lib/urlState.ts`, `web/src/lib/format.ts`
- Create: `web/src/lib/gantt.ts`
- Test: `web/src/lib/urlState.test.ts` (append), `web/src/lib/format.test.ts` (append), `web/src/lib/gantt.test.ts`

- [ ] **Step 1: Write the failing tests**

Append to `web/src/lib/urlState.test.ts`:

```ts
import { decodeDispatch, decodeJohnson, encodeDispatch, encodeJohnson } from "./urlState";

describe("scheduling URL state", () => {
  it("round-trips dispatch jobs through the query string", () => {
    const jobs = [
      { id: "A", processingTime: 6, dueDate: 8 },
      { id: "B", processingTime: 2, dueDate: 6 },
    ];
    expect(decodeDispatch("?" + encodeDispatch(jobs))).toEqual(jobs);
  });

  it("round-trips johnson jobs and ignores extra params like mode", () => {
    const jobs = [{ id: "J1", timeM1: 3, timeM2: 6 }];
    expect(decodeJohnson("?mode=johnson&" + encodeJohnson(jobs))).toEqual(jobs);
  });

  it("returns null for missing or malformed job strings", () => {
    expect(decodeDispatch("")).toBeNull();
    expect(decodeDispatch("?j=A,1")).toBeNull(); // wrong arity
    expect(decodeDispatch("?j=A,x,2")).toBeNull(); // non-numeric
  });
});
```

(Keep the existing imports at the top of the file; merge the new named imports into the existing `import { ... } from "./urlState";` line.)

Append to `web/src/lib/format.test.ts` inside the existing `describe("formatting", ...)` block, and add `formatNumber` to the import:

```ts
  it("formats plain numbers without trailing zeros", () => {
    expect(formatNumber(15.4)).toBe("15.4");
    expect(formatNumber(24)).toBe("24");
    expect(formatNumber(1234.5)).toBe("1,234.5");
  });
```

Create `web/src/lib/gantt.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { ganttTraces } from "./gantt";

describe("ganttTraces", () => {
  it("converts scheduled jobs to positioned horizontal bars", () => {
    const traces = ganttTraces([
      {
        label: "M1",
        jobs: [
          { id: "A", start: 0, end: 6 },
          { id: "B", start: 6, end: 8 },
        ],
      },
    ]) as any[];
    expect(traces).toHaveLength(1);
    expect(traces[0].base).toEqual([0, 6]);
    expect(traces[0].x).toEqual([6, 2]); // bar lengths = durations
    expect(traces[0].y).toEqual(["M1", "M1"]);
    expect(traces[0].text).toEqual(["A", "B"]);
  });

  it("colors tardy jobs in the danger color", () => {
    const [trace] = ganttTraces(
      [
        {
          label: "Jobs",
          jobs: [
            { id: "A", start: 0, end: 2 },
            { id: "C", start: 2, end: 10 },
          ],
        },
      ],
      new Set(["C"]),
    ) as any[];
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — `./gantt` doesn't exist; `encodeDispatch` / `formatNumber` not exported.

- [ ] **Step 3: Implement the lib changes**

Append to `web/src/lib/api.ts`:

```ts
export interface ScheduledJob {
  id: string;
  start: number;
  end: number;
}

export type DispatchMethodName =
  | "fcfs"
  | "spt"
  | "edd"
  | "lpt"
  | "moore_hodgson"
  | "min_total_tardiness";

export interface DispatchMethodResult {
  sequence: string[];
  schedule: ScheduledJob[];
  avg_completion_time: number;
  avg_tardiness: number;
  total_tardiness: number;
  max_tardiness: number;
  num_tardy: number;
}

export interface DispatchResponse {
  // min_total_tardiness is omitted beyond 15 jobs, hence Partial
  methods: Partial<Record<DispatchMethodName, DispatchMethodResult>>;
  optimal_capped: boolean;
}

export interface JohnsonStep {
  kind: "pick" | "done";
  job?: string;
  time?: number;
  machine?: 1 | 2;
  placement?: "front" | "back";
  slot?: number;
  sequence?: string[];
}

export interface JohnsonResponse {
  sequence: string[];
  machine1: ScheduledJob[];
  machine2: ScheduledJob[];
  makespan: number;
  input_order_makespan: number;
  steps: JohnsonStep[];
}
```

Append to `web/src/lib/urlState.ts`:

```ts
export interface DispatchJob {
  id: string;
  processingTime: number;
  dueDate: number;
}

export interface JohnsonJob {
  id: string;
  timeM1: number;
  timeM2: number;
}

// Job lists encode as j=id,num,num;id,num,num — both scheduling modes share
// the shape (id + two numbers). IDs containing "," or ";" would break the
// format; decode returns null and the page falls back to a preset.
function encodeTriples(triples: [string, number, number][]): string {
  const params = new URLSearchParams();
  params.set("j", triples.map((t) => t.join(",")).join(";"));
  return params.toString();
}

function decodeTriples(search: string): [string, number, number][] | null {
  const raw = new URLSearchParams(search).get("j");
  if (!raw) return null;
  const triples: [string, number, number][] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const a = Number(fields[1]);
    const b = Number(fields[2]);
    if (Number.isNaN(a) || Number.isNaN(b)) return null;
    triples.push([fields[0], a, b]);
  }
  return triples;
}

export function encodeDispatch(jobs: DispatchJob[]): string {
  return encodeTriples(jobs.map((j) => [j.id, j.processingTime, j.dueDate]));
}

export function decodeDispatch(search: string): DispatchJob[] | null {
  const triples = decodeTriples(search);
  if (!triples) return null;
  return triples.map(([id, processingTime, dueDate]) => ({ id, processingTime, dueDate }));
}

export function encodeJohnson(jobs: JohnsonJob[]): string {
  return encodeTriples(jobs.map((j) => [j.id, j.timeM1, j.timeM2]));
}

export function decodeJohnson(search: string): JohnsonJob[] | null {
  const triples = decodeTriples(search);
  if (!triples) return null;
  return triples.map(([id, timeM1, timeM2]) => ({ id, timeM1, timeM2 }));
}
```

Append to `web/src/lib/format.ts`:

```ts
export function formatNumber(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}
```

Create `web/src/lib/gantt.ts`:

```ts
import type { Data } from "plotly.js";
import type { ScheduledJob } from "./api";

const ON_TIME = "#0d9488";
const TARDY = "#dc2626";

/** One horizontal bar trace per machine row, positioned with `base` so bars
 * start at each job's start time. Pair with layout barmode "overlay" and a
 * reversed y-axis (so the first row renders on top). */
export function ganttTraces(
  rows: { label: string; jobs: ScheduledJob[] }[],
  tardy: Set<string> = new Set(),
): Data[] {
  return rows.map((row) => ({
    type: "bar" as const,
    orientation: "h" as const,
    y: row.jobs.map(() => row.label),
    base: row.jobs.map((j) => j.start),
    x: row.jobs.map((j) => j.end - j.start),
    text: row.jobs.map((j) => j.id),
    textposition: "inside" as const,
    insidetextanchor: "middle" as const,
    hovertemplate: "%{text}<extra></extra>",
    marker: {
      color: row.jobs.map((j) => (tardy.has(j.id) ? TARDY : ON_TIME)),
      line: { color: "#ffffff", width: 1 },
    },
    showlegend: false,
  }));
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test`
Expected: 10 passed (4 existing + 6 new). Also `npm run build` — no TS errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib
git commit -m "feat: add scheduling api types, job url state, and gantt traces"
```

---

### Task 5: Shared components — JobsTable and generic StepPlayer

**Files:**
- Create: `web/src/components/JobsTable.tsx`, `web/src/components/StepPlayer.tsx`
- Move: `web/src/pages/lot-sizing/TeachingDrawer.css` → `web/src/components/StepPlayer.css` (content unchanged)
- Modify: `web/src/pages/lot-sizing/TeachingDrawer.tsx` (becomes a thin wrapper)

The spec's component list names a generic `StepPlayer`; the lot-sizing
`TeachingDrawer` currently owns that behavior. Extract it so the Johnson
drawer (Task 7) reuses the player instead of copying it. Pure refactor —
the existing lot-sizing Playwright test (run in Task 8) proves behavior held.

- [ ] **Step 1: Create JobsTable**

Create `web/src/components/JobsTable.tsx` (reuses `DemandTable.css` — the
table styling is identical, only the columns differ):

```tsx
import "./DemandTable.css";

export interface JobRow {
  id: string;
  a: number;
  b: number;
}

/** Editable job table: text ID + two numeric columns (headers via props).
 * Pasting a column from Excel/Sheets into a numeric cell fills downward,
 * same convention as DemandTable (capped at the existing rows — new jobs
 * need an ID, so paste can't invent them). */
export function JobsTable({
  label,
  columns,
  rows,
  onChange,
}: {
  label: string;
  columns: [string, string];
  rows: JobRow[];
  onChange: (next: JobRow[]) => void;
}) {
  const setRow = (i: number, patch: Partial<JobRow>) => {
    const next = [...rows];
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };

  const handlePaste = (i: number, key: "a" | "b", e: React.ClipboardEvent) => {
    const pasted = e.clipboardData
      .getData("text")
      .split(/[\s,;]+/)
      .filter((t) => t.length > 0)
      .map(Number);
    if (pasted.length < 2 || pasted.some(Number.isNaN)) return; // normal paste
    e.preventDefault();
    const next = [...rows];
    pasted.forEach((v, k) => {
      if (i + k < next.length) next[i + k] = { ...next[i + k], [key]: v };
    });
    onChange(next);
  };

  const addRow = () => {
    let n = rows.length + 1;
    while (rows.some((r) => r.id === `J${n}`)) n += 1;
    onChange([...rows, { id: `J${n}`, a: 1, b: 1 }]);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>{label}</div>
      <table className="demand-table">
        <thead>
          <tr>
            <th>job</th>
            <th>{columns[0]}</th>
            <th>{columns[1]}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td style={{ width: 56 }}>
                <input
                  value={row.id}
                  onChange={(e) => setRow(i, { id: e.target.value })}
                />
              </td>
              {(["a", "b"] as const).map((key) => (
                <td key={key}>
                  <input
                    type="number"
                    step="any"
                    min={0}
                    value={Number.isNaN(row[key]) ? "" : row[key]}
                    onChange={(e) => setRow(i, { [key]: e.target.valueAsNumber })}
                    onPaste={(e) => handlePaste(i, key, e)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={addRow}>+ job</button>
        <button onClick={() => rows.length > 1 && onChange(rows.slice(0, -1))}>
          − job
        </button>
      </div>
      <div className="demand-table-hint">tip: paste a column straight from Excel</div>
    </div>
  );
}
```

- [ ] **Step 2: Move the drawer CSS and create StepPlayer**

Run (repo root):

```bash
git mv web/src/pages/lot-sizing/TeachingDrawer.css web/src/components/StepPlayer.css
```

Create `web/src/components/StepPlayer.tsx` (the open/index/keyboard logic is
lifted verbatim from the current TeachingDrawer; only the texts become props):

```tsx
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import "./StepPlayer.css";

/** "Algorithms that narrate themselves": a collapsed teaser button that
 * opens a dark step-by-step player over structured solver steps
 * (◀ ▶ buttons + keyboard arrows). Each module supplies its own describe(). */
export function StepPlayer<T>({
  steps,
  title,
  question,
  teaser,
  describe,
}: {
  steps: T[];
  title: string;
  question: string;
  teaser: string;
  describe: (step: T) => ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => setIndex(0), [steps]); // new data -> restart the story

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, steps.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, steps.length]);

  if (!open) {
    return (
      <button className="drawer-trigger" onClick={() => setOpen(true)}>
        <span>
          💡 <b>{question}</b> <span className="subtitle">{teaser}</span>
        </span>
        <span className="go">Walk me through it ▶</span>
      </button>
    );
  }

  const step = steps[Math.min(index, steps.length - 1)];
  return (
    <div className="step-player">
      <div className="label">{title}</div>
      <div className="step-card">{describe(step)}</div>
      <div className="step-nav">
        <button onClick={() => setIndex((i) => Math.max(i - 1, 0))} disabled={index === 0}>
          ◀ Back
        </button>
        <button
          className="primary"
          onClick={() => setIndex((i) => Math.min(i + 1, steps.length - 1))}
          disabled={index === steps.length - 1}
        >
          Next ▶
        </button>
        <button onClick={() => setOpen(false)}>Close</button>
        <span className="count">
          step {index + 1} / {steps.length} · arrow keys work too
        </span>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Slim TeachingDrawer down to a describe() provider**

Replace `web/src/pages/lot-sizing/TeachingDrawer.tsx` with:

```tsx
import type { SilverMealStep } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: SilverMealStep) {
  if (step.kind === "open_lot") {
    return (
      <>
        <b>Lot {step.lot}</b> opens with an order in period {step.period}. One
        setup is now committed — every period this lot covers shares it.
      </>
    );
  }
  if (step.kind === "try_extend") {
    const better = step.decision === "extend";
    return (
      <>
        Should lot {step.lot} also cover period {step.period}? Average cost per
        period covered: <span className="mono">{formatMoney(step.avg_current!)}</span> now →{" "}
        <span className="mono">{formatMoney(step.avg_extended!)}</span> if extended.{" "}
        {better ? (
          <span className="step-good">Cheaper per period — extend. ✓</span>
        ) : (
          <span className="step-bad">More expensive per period — stop here. ✕</span>
        )}
      </>
    );
  }
  return (
    <>
      <b>Lot {step.lot} fixed:</b> one order of {step.quantity} units in period{" "}
      {step.start} covers periods {step.start}–{step.end}.
    </>
  );
}

export function TeachingDrawer({ steps }: { steps: SilverMealStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Silver–Meal, narrated by the solver"
      question="Why these lots?"
      teaser="watch Silver–Meal decide, step by step, on this exact data"
      describe={describe}
    />
  );
}
```

- [ ] **Step 4: Verify build and unit tests**

Run (in `web/`): `npm run build` — no TS errors (this catches a stale
`./TeachingDrawer.css` import). Then `npm test` — 10 passed.

- [ ] **Step 5: Commit**

```bash
git add web/src/components web/src/pages/lot-sizing
git commit -m "refactor: extract generic step player; add jobs table component"
```

---

### Task 6: Scheduling page — dispatching view (comparison table + Gantt)

**Files:**
- Create: `web/src/pages/scheduling/presets.ts`, `web/src/pages/scheduling/Scheduling.css`, `web/src/pages/scheduling/DispatchView.tsx`, `web/src/pages/scheduling/SchedulingPage.tsx`
- Modify: `web/src/App.tsx`, `web/src/modules.ts`

- [ ] **Step 1: Presets**

Create `web/src/pages/scheduling/presets.ts`:

```ts
import type { DispatchJob, JohnsonJob } from "../../lib/urlState";

export const DISPATCH_PRESETS: Record<string, DispatchJob[]> = {
  "Five-job demo": [
    { id: "A", processingTime: 6, dueDate: 8 },
    { id: "B", processingTime: 2, dueDate: 6 },
    { id: "C", processingTime: 8, dueDate: 18 },
    { id: "D", processingTime: 3, dueDate: 15 },
    { id: "E", processingTime: 9, dueDate: 23 },
  ],
  // the classic counterexample where EDD is NOT optimal for total tardiness
  "EDD beaten by the DP": [
    { id: "A", processingTime: 4, dueDate: 4 },
    { id: "B", processingTime: 3, dueDate: 5 },
    { id: "C", processingTime: 2, dueDate: 6 },
  ],
};

export const JOHNSON_PRESETS: Record<string, JohnsonJob[]> = {
  "Five-job flow shop": [
    { id: "J1", timeM1: 3, timeM2: 6 },
    { id: "J2", timeM1: 5, timeM2: 2 },
    { id: "J3", timeM1: 1, timeM2: 2 },
    { id: "J4", timeM1: 6, timeM2: 6 },
    { id: "J5", timeM1: 7, timeM2: 5 },
  ],
  "Machine 2 is the slow side": [
    { id: "P1", timeM1: 2, timeM2: 7 },
    { id: "P2", timeM1: 4, timeM2: 6 },
    { id: "P3", timeM1: 3, timeM2: 8 },
    { id: "P4", timeM1: 6, timeM2: 5 },
  ],
};
```

- [ ] **Step 2: Comparison-table CSS**

Create `web/src/pages/scheduling/Scheduling.css`:

```css
.compare-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.compare-table th {
  text-align: right;
  padding: 6px 10px;
  color: var(--muted);
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.compare-table th:first-child, .compare-table td:first-child { text-align: left; }
.compare-table td {
  padding: 7px 10px;
  border-top: 1px solid #f1f4f6;
  text-align: right;
  font-family: var(--font-mono);
}
.compare-table td:first-child { font-family: var(--font-body); font-weight: 600; }
.compare-table tbody tr { cursor: pointer; }
.compare-table tbody tr:hover td { background: #f8fafc; }
.compare-table tr.selected td { background: var(--accent-soft); }
.compare-table td.best { color: var(--accent); font-weight: 700; }
.method-note { font-size: 11px; color: var(--subtle); font-weight: 400; }
```

- [ ] **Step 3: DispatchView**

Create `web/src/pages/scheduling/DispatchView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { DispatchMethodName, DispatchResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { DispatchJob } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { PlotCard } from "../../components/PlotCard";
import { DISPATCH_PRESETS } from "./presets";
import "./Scheduling.css";

const METHOD_INFO: Record<DispatchMethodName, { label: string; note: string }> = {
  fcfs: { label: "FCFS", note: "first come, first served — the no-thought baseline" },
  spt: { label: "SPT", note: "shortest first — provably minimizes avg completion" },
  edd: { label: "EDD", note: "earliest due date — minimizes the worst lateness" },
  lpt: { label: "LPT", note: "longest first — usually the cautionary tale" },
  moore_hodgson: { label: "Moore–Hodgson", note: "provably the fewest tardy jobs" },
  min_total_tardiness: { label: "Min total tardiness", note: "exact optimum (subset DP)" },
};
const METHOD_ORDER: DispatchMethodName[] = [
  "fcfs", "spt", "edd", "lpt", "moore_hodgson", "min_total_tardiness",
];

type MetricKey =
  | "avg_completion_time"
  | "avg_tardiness"
  | "total_tardiness"
  | "max_tardiness"
  | "num_tardy";

const METRIC_COLUMNS: { key: MetricKey; label: string }[] = [
  { key: "avg_completion_time", label: "Avg completion" },
  { key: "avg_tardiness", label: "Avg tardiness" },
  { key: "total_tardiness", label: "Total tardiness" },
  { key: "max_tardiness", label: "Max tardiness" },
  { key: "num_tardy", label: "# tardy" },
];

export function DispatchView({
  jobs,
  onJobs,
}: {
  jobs: DispatchJob[];
  onJobs: (next: DispatchJob[]) => void;
}) {
  const [result, setResult] = useState<DispatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DispatchMethodName>("spt");
  const debounced = useDebouncedValue(jobs);

  useEffect(() => {
    let cancelled = false;
    postJson<DispatchResponse>("/scheduling/dispatch", {
      jobs: debounced.map((j) => ({
        id: j.id,
        processing_time: j.processingTime,
        due_date: j.dueDate,
      })),
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

  const methods = result?.methods ?? {};
  const present = METHOD_ORDER.filter((name) => methods[name]);
  // the selected method can disappear (DP row capped beyond 15 jobs)
  const active: DispatchMethodName = methods[selected] ? selected : "spt";
  const plan = methods[active];

  const due = new Map(jobs.map((j) => [j.id, j.dueDate]));
  const tardy = new Set(
    (plan?.schedule ?? [])
      .filter((s) => s.end > (due.get(s.id) ?? Infinity))
      .map((s) => s.id),
  );

  // lower is better for every column; highlight the per-column minimum
  const best: Partial<Record<MetricKey, number>> = {};
  for (const { key } of METRIC_COLUMNS) {
    best[key] = Math.min(...present.map((name) => methods[name]![key]));
  }

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Scheduling</h1>
          <div className="subtitle module-sub">
            One machine, n jobs — which order serves them best?
          </div>
        </div>
        <JobsTable
          label="Jobs (processing time, due date)"
          columns={["p", "due"]}
          rows={jobs.map((j) => ({ id: j.id, a: j.processingTime, b: j.dueDate }))}
          onChange={(rows) =>
            onJobs(rows.map((r) => ({ id: r.id, processingTime: r.a, dueDate: r.b })))
          }
        />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = DISPATCH_PRESETS[e.target.value];
              if (preset) onJobs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(DISPATCH_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {plan && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                {METHOD_INFO[active].label} — {METHOD_INFO[active].note}
              </div>
              <div className="hero-value">{plan.sequence.join(" → ")}</div>
            </div>
            <div className="hero-orders">
              {plan.num_tardy} tardy · avg completion {formatNumber(plan.avg_completion_time)}
            </div>
          </div>
        )}
        {result && (
          <div className="card" style={{ padding: "10px 14px" }}>
            <div className="label">
              Every rule on your jobs — click a row, best value per column in teal
            </div>
            <table className="compare-table">
              <thead>
                <tr>
                  <th>method</th>
                  {METRIC_COLUMNS.map((m) => (
                    <th key={m.key}>{m.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {present.map((name) => (
                  <tr
                    key={name}
                    className={active === name ? "selected" : ""}
                    onClick={() => setSelected(name)}
                  >
                    <td>
                      {METHOD_INFO[name].label}{" "}
                      <span className="method-note">{METHOD_INFO[name].note}</span>
                    </td>
                    {METRIC_COLUMNS.map((m) => (
                      <td
                        key={m.key}
                        className={methods[name]![m.key] === best[m.key] ? "best" : ""}
                      >
                        {formatNumber(methods[name]![m.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {result.optimal_capped && (
              <div className="subtitle" style={{ marginTop: 6, fontSize: 11 }}>
                Exact total-tardiness optimization is capped at 15 jobs (the
                search space doubles with each job) — that row is omitted.
              </div>
            )}
          </div>
        )}
        {plan && (
          <PlotCard
            label={`${METHOD_INFO[active].label} timeline — tardy jobs in red`}
            data={ganttTraces([{ label: "Machine", jobs: plan.schedule }], tardy)}
            layout={{
              barmode: "overlay",
              xaxis: { title: { text: "time" } },
              yaxis: { autorange: "reversed" },
            }}
            height={160}
          />
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 4: Page wrapper with URL state (dispatch only — pills come in Task 7)**

Create `web/src/pages/scheduling/SchedulingPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDispatch, encodeDispatch } from "../../lib/urlState";
import type { DispatchJob } from "../../lib/urlState";
import "../../components/workbench.css";
import { DISPATCH_PRESETS } from "./presets";
import { DispatchView } from "./DispatchView";

export default function SchedulingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState<DispatchJob[]>(
    () => decodeDispatch("?" + searchParams.toString()) ?? DISPATCH_PRESETS["Five-job demo"],
  );

  const update = (next: DispatchJob[]) => {
    setJobs(next);
    setSearchParams(encodeDispatch(next), { replace: true });
  };

  return (
    <div className="workbench">
      <DispatchView jobs={jobs} onJobs={update} />
    </div>
  );
}
```

- [ ] **Step 5: Route and module flip**

In `web/src/App.tsx`, add the import:

```tsx
import SchedulingPage from "./pages/scheduling/SchedulingPage";
```

and add this route directly under the `/lot-sizing` route:

```tsx
<Route path="/scheduling" element={<SchedulingPage />} />
```

In `web/src/modules.ts`, replace the scheduling entry with:

```ts
  { path: "/scheduling", name: "Scheduling", decision: "What order should I run these jobs in?", icon: Calendar, ready: true, exampleSearch: "?j=A,6,8;B,2,6;C,8,18;D,3,15;E,9,23" },
```

- [ ] **Step 6: Verify in the browser**

Run uvicorn in one terminal (repo root): `.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`
Run Vite in another (in `web/`): `npm run dev`
Open `http://localhost:5173/scheduling` and check: hero shows the SPT sequence **B → D → A → C → E**; the comparison table has six rows (FCFS avg completion 15.4, EDD avg tardiness 1.2 highlighted teal, Moore–Hodgson # tardy 1 highlighted); clicking a row swaps the hero and the Gantt; tardy bars are red; editing a processing time recomputes ~300 ms later; emptying a job ID shows the inline core error; the Home card for Scheduling now shows Open + example link. Stop both servers.

- [ ] **Step 7: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src
git commit -m "feat: add scheduling dispatch view with rule comparison and gantt"
```

---

### Task 7: Johnson view, teaching drawer, and mode pills

**Files:**
- Create: `web/src/pages/scheduling/JohnsonView.tsx`, `web/src/pages/scheduling/JohnsonDrawer.tsx`
- Modify: `web/src/pages/scheduling/SchedulingPage.tsx`

- [ ] **Step 1: JohnsonDrawer (describe() over the pick steps)**

Create `web/src/pages/scheduling/JohnsonDrawer.tsx`:

```tsx
import type { JohnsonStep } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: JohnsonStep) {
  if (step.kind === "done") {
    return (
      <>
        <b>Sequence fixed:</b> {step.sequence!.join(" → ")}. Every pick was
        forced by one rule — smallest remaining time decides — and the result
        is provably the minimal makespan.
      </>
    );
  }
  const front = step.placement === "front";
  return (
    <>
      The smallest processing time left anywhere is <b>{step.job}</b>:{" "}
      <span className="mono">{formatNumber(step.time!)}</span> on machine {step.machine}.{" "}
      {front ? (
        <span className="step-good">
          Short machine-1 work reaches machine 2 quickly — place it as early
          as possible: slot {step.slot}.
        </span>
      ) : (
        <span className="step-bad">
          Short machine-2 work would leave machine 2 idle at the end — push it
          as late as possible: slot {step.slot}.
        </span>
      )}
    </>
  );
}

export function JohnsonDrawer({ steps }: { steps: JohnsonStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Johnson's rule, narrated by the solver"
      question="Why this order?"
      teaser="watch Johnson's rule pick the sequence, job by job, on this exact data"
      describe={describe}
    />
  );
}
```

- [ ] **Step 2: JohnsonView**

Create `web/src/pages/scheduling/JohnsonView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { JohnsonResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { JohnsonJob } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { MetricCard } from "../../components/MetricCard";
import { PlotCard } from "../../components/PlotCard";
import { JOHNSON_PRESETS } from "./presets";
import { JohnsonDrawer } from "./JohnsonDrawer";

export function JohnsonView({
  jobs,
  onJobs,
}: {
  jobs: JohnsonJob[];
  onJobs: (next: JohnsonJob[]) => void;
}) {
  const [result, setResult] = useState<JohnsonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(jobs);

  useEffect(() => {
    let cancelled = false;
    postJson<JohnsonResponse>("/scheduling/johnson", {
      jobs: debounced.map((j) => ({ id: j.id, time_m1: j.timeM1, time_m2: j.timeM2 })),
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

  const slower = result ? result.input_order_makespan - result.makespan : 0;

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Scheduling</h1>
          <div className="subtitle module-sub">
            Two machines in series — Johnson's rule finds the fastest order.
          </div>
        </div>
        <JobsTable
          label="Jobs (machine 1, machine 2 times)"
          columns={["M1", "M2"]}
          rows={jobs.map((j) => ({ id: j.id, a: j.timeM1, b: j.timeM2 }))}
          onChange={(rows) => onJobs(rows.map((r) => ({ id: r.id, timeM1: r.a, timeM2: r.b })))}
        />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = JOHNSON_PRESETS[e.target.value];
              if (preset) onJobs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(JOHNSON_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Optimal sequence — Johnson's rule
                </div>
                <div className="hero-value">
                  {result.sequence.join(" → ")}{" "}
                  <span className="hero-detail">makespan {formatNumber(result.makespan)}</span>
                </div>
              </div>
              <div className="hero-orders">
                all done at t = {formatNumber(result.makespan)}
              </div>
            </div>
            <div className="row">
              <MetricCard
                label="Johnson makespan"
                value={formatNumber(result.makespan)}
                detail={<span style={{ color: "var(--accent)" }}>optimal ✓</span>}
              />
              <MetricCard
                label="Input order makespan"
                value={formatNumber(result.input_order_makespan)}
                detail={slower > 0 ? `${formatNumber(slower)} slower` : "already optimal"}
              />
            </div>
            <PlotCard
              label="Two-machine Gantt — gaps on machine 2 are idle time"
              data={ganttTraces([
                { label: "Machine 1", jobs: result.machine1 },
                { label: "Machine 2", jobs: result.machine2 },
              ])}
              layout={{
                barmode: "overlay",
                xaxis: { title: { text: "time" } },
                yaxis: { autorange: "reversed" },
              }}
              height={200}
            />
            <JohnsonDrawer steps={result.steps} />
          </>
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 3: Mode pills in the page wrapper**

Replace `web/src/pages/scheduling/SchedulingPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  decodeDispatch,
  decodeJohnson,
  encodeDispatch,
  encodeJohnson,
} from "../../lib/urlState";
import type { DispatchJob, JohnsonJob } from "../../lib/urlState";
import "../../components/workbench.css";
import { DISPATCH_PRESETS, JOHNSON_PRESETS } from "./presets";
import { DispatchView } from "./DispatchView";
import { JohnsonView } from "./JohnsonView";

export default function SchedulingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const startJohnson = searchParams.get("mode") === "johnson";
  const initialSearch = "?" + searchParams.toString();

  const [mode, setMode] = useState<"dispatch" | "johnson">(
    startJohnson ? "johnson" : "dispatch",
  );
  const [jobs, setJobs] = useState<DispatchJob[]>(
    () =>
      (startJohnson ? null : decodeDispatch(initialSearch)) ??
      DISPATCH_PRESETS["Five-job demo"],
  );
  const [johnsonJobs, setJohnsonJobs] = useState<JohnsonJob[]>(
    () =>
      (startJohnson ? decodeJohnson(initialSearch) : null) ??
      JOHNSON_PRESETS["Five-job flow shop"],
  );

  const updateDispatch = (next: DispatchJob[]) => {
    setJobs(next);
    setSearchParams(encodeDispatch(next), { replace: true });
  };

  const updateJohnson = (next: JohnsonJob[]) => {
    setJohnsonJobs(next);
    setSearchParams("mode=johnson&" + encodeJohnson(next), { replace: true });
  };

  const switchMode = (next: "dispatch" | "johnson") => {
    setMode(next);
    setSearchParams(
      next === "johnson" ? "mode=johnson&" + encodeJohnson(johnsonJobs) : encodeDispatch(jobs),
      { replace: true },
    );
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button
          className={mode === "dispatch" ? "active" : ""}
          onClick={() => switchMode("dispatch")}
        >
          Single machine
        </button>
        <button
          className={mode === "johnson" ? "active" : ""}
          onClick={() => switchMode("johnson")}
        >
          Two-machine flow shop
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "dispatch" ? (
          <DispatchView jobs={jobs} onJobs={updateDispatch} />
        ) : (
          <JohnsonView jobs={johnsonJobs} onJobs={updateJohnson} />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify in the browser**

Both dev servers up (as in Task 6 Step 6). Check `/scheduling`: pills switch
views; the flow-shop default shows **J3 → J1 → J4 → J5 → J2**, makespan 24
vs input order 27 ("3 slower"); the two-row Gantt shows machine 2 idle 0–1
and 3–4; **Walk me through it ▶** narrates: pick J3 (1 on M1, front slot 1)
→ pick J2 (2 on M2, back slot 5) → … → done card with the full sequence;
arrow keys navigate; `/scheduling?mode=johnson` deep-links straight to the
flow shop. Stop servers.

- [ ] **Step 5: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src/pages/scheduling
git commit -m "feat: add johnson flow shop view with gantt and teaching drawer"
```

---

### Task 8: Playwright smoke, docs, final verification

**Files:**
- Create: `web/e2e/scheduling.spec.ts`
- Modify: `README.md`

- [ ] **Step 1: Write the smoke spec**

Create `web/e2e/scheduling.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

// Hand-traced ground truth: jobs A(6,8) B(2,6) C(8,18) D(3,15) E(9,23);
// flow shop J1(3,6) J2(5,2) J3(1,2) J4(6,6) J5(7,5) -> makespan 24 (input order: 27).
test("dispatching compares every rule on the shared-link example", async ({ page }) => {
  await page.goto("/scheduling?j=A,6,8;B,2,6;C,8,18;D,3,15;E,9,23");
  await expect(page.getByText("B → D → A → C → E")).toBeVisible(); // SPT hero (default)
  await expect(page.getByText("15.4").first()).toBeVisible(); // FCFS avg completion
  await expect(page.getByText("Moore–Hodgson").first()).toBeVisible();
});

test("johnson mode shows the optimal sequence and narrates the first pick", async ({ page }) => {
  await page.goto("/scheduling?mode=johnson&j=J1,3,6;J2,5,2;J3,1,2;J4,6,6;J5,7,5");
  await expect(page.getByText("J3 → J1 → J4 → J5 → J2").first()).toBeVisible();
  await expect(page.getByText("makespan 24")).toBeVisible();
  await expect(page.getByText("27", { exact: true })).toBeVisible(); // input-order baseline
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/smallest processing time left/i)).toBeVisible();
});
```

- [ ] **Step 2: Run the smoke tests**

Run (in `web/`): `npm run e2e`
Expected: 5 passed — the 2 new specs plus the 3 lot-sizing ones (which also
prove the Task 5 StepPlayer refactor preserved the drawer's behavior).

- [ ] **Step 3: Update the README roadmap line**

In `README.md`, replace the line

```markdown
- React redesign: Lot Sizing ✅ — remaining modules rolling out one by one
```

with

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅ — remaining modules rolling out one by one
```

- [ ] **Step 4: Full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -q` — 129 passed.
Run (in `web/`): `npm test` (10 passed), `npm run build` (clean), `npm run e2e` (5 passed).

- [ ] **Step 5: Commit**

```bash
git add web/e2e README.md
git commit -m "test: add playwright smoke for scheduling; update roadmap"
```

---

## Self-review notes

- **Spec coverage:** both scheduling endpoints from the API design ✓ (Tasks 2–3); teaching steps recorded by core with TDD ✓ (Task 1); module page anatomy — pills, pinned input panel, hero, comparison, chart, drawer ✓ (Tasks 6–7); input ergonomics — editable table with Excel paste, debounce, sharable URLs, presets ✓ (Tasks 4–6); generic `StepPlayer` from the spec's component list ✓ (Task 5); Playwright smoke asserting hand-traced numbers ✓ (Task 8). The exact optimizers (Moore–Hodgson, min-total-tardiness with the 15-job cap) ride along in the dispatch comparison per the scheduling spec amendment.
- **Type consistency check:** `ScheduledJobOut` (API) ↔ `ScheduledJob` (TS) field names match (`id`, `start`, `end`) ✓; method keys `fcfs/spt/edd/lpt/moore_hodgson/min_total_tardiness` consistent between router, `DispatchMethodName`, `METHOD_INFO`, `METHOD_ORDER` ✓; `JohnsonStep` TS fields match the core step dicts (`kind/job/time/machine/placement/slot/sequence`) ✓; `JobsTable` row shape `{id, a, b}` is mapped to domain names at each view boundary ✓; `StepPlayer` props (`steps/title/question/teaser/describe`) identical at both call sites ✓.
- **Known limitation noted in code:** job IDs containing `,` or `;` break the URL encoding — decode returns null and the page falls back to the preset. Acceptable for course-style IDs (A, B, J1…).
- **Tie/conventions:** untouched — `core/` behavior is preserved by delegation, proven by the existing hand-traced tests.
