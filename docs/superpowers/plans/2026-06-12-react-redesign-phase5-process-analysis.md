# React Redesign Phase 5: Process Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Process Analysis module in the React app: capacity/bottleneck analysis (capacity per resource, flow rate, utilization, implied utilization, unloaded flow time) plus a Little's Law calculator, with a teaching drawer that narrates why the bottleneck sets the pace.

**Architecture:** `core/process_analysis` already has all the math, hand-traced and tested — it only gains `capacity_steps`, the step-recording narration for the teaching drawer. A new `api/routers/process_analysis.py` exposes `/api/process-analysis/solve` and `/api/process-analysis/littles-law`, both unit-agnostic like core (per-minute in, per-minute out); the frontend sends minutes and converts displays to units/hour (×60), exactly as the design spec prescribes. The frontend gains a `/process-analysis` page with two mode pills (Capacity & bottleneck / Little's Law) copying the LotSizingPage Dynamic/EOQ pattern; the capacity view reuses `JobsTable` (which gains an `idLabel` prop), ports the two Streamlit chart configs (capacity bars with bottleneck highlighted + demand line; horizontal utilization bars with the 100% line), and ends with a `BottleneckDrawer` on the shared `StepPlayer`.

**Tech Stack:** Python 3.11+, FastAPI, pytest; React 18 + TypeScript, Plotly, Vitest, Playwright. No new dependencies.

**Context for the engineer:** Operations Management teaching toolkit; solver math lives in `core/` with hand-traced tests in `tests/` — never change solver behavior. Specs: `docs/superpowers/specs/2026-06-11-react-redesign-design.md` (UI pattern) and `docs/superpowers/specs/2026-06-11-process-analysis-design.md` (math + units convention). Copy the pattern of the shipped modules (`api/routers/scheduling.py`, `web/src/pages/lot-sizing/LotSizingPage.tsx` for mode pills, `web/src/pages/scheduling/DispatchView.tsx` for a view). The legacy Streamlit page `app/pages/2_Process_Analysis.py` + `app/process_charts.py` show exactly what to port. Python runs via `.\.venv\Scripts\python.exe`; frontend commands run in `web/`.

**Reference — hand-traced example used everywhere below (already encoded in `tests/test_capacity.py`):**

Resources (processing time in minutes per unit): A = 10 min × 2 servers → capacity 0.2/min (12/h), B = 6 min × 1 → 1/6 per min (10/h) ← **bottleneck**, C = 4 min × 1 → 0.25/min (15/h).
- Process capacity 1/6 per min = 10/h. Unloaded flow time 20 min.
- Demand 0.15/min (= 9/h) < 1/6 → **demand-constrained**, flow rate 0.15/min (9/h); utilizations A 75%, B 90%, C 60%; implied utilizations equal utilizations here (rate = demand).
- No demand → **capacity-constrained**, flow rate = 1/6; B runs at 100%.
- Little's Law (from `tests/test_littles_law.py`): I=20, R=4 → T = 5.

---

### Task 1: Capacity-analysis step trace in core/

**Files:**
- Modify: `core/process_analysis/capacity.py`, `core/process_analysis/__init__.py`
- Test: `tests/test_capacity.py` (append)

The narration is the order a student computes it by hand: capacity per
resource → the minimum is the bottleneck → flow rate = min(demand, capacity)
→ utilization per resource. Steps are pure data; all values stay in core's
unit-agnostic per-minute terms (the UI converts for display).

Step schema:
- `{"kind": "capacity", "resource": "A", "processing_time": 10.0, "servers": 2, "capacity": 0.2}` — one per resource, in process order.
- `{"kind": "bottleneck", "resource": "B", "capacity": 0.1667}` — the minimum.
- `{"kind": "flow_rate", "capacity": 0.1667, "demand": 0.15 | None, "rate": 0.15, "constraint": "demand" | "capacity"}` — `demand < capacity` ⇒ "demand", else (or no demand) "capacity", matching the Streamlit page's caption logic.
- `{"kind": "utilization", "resource": "A", "utilization": 0.75, "implied": 0.75 | None}` — one per resource; `implied` is None when no demand was given.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_capacity.py` (and add `capacity_steps` to the existing
`from core.process_analysis.capacity import (...)` list, alphabetical —
after `bottleneck`):

```python
def test_capacity_steps_narrate_the_worked_example():
    """The docstring trace above as recorded steps: capacities in process
    order, then the bottleneck, the flow-rate decision, and utilizations."""
    steps = capacity_steps(RESOURCES, demand=0.15)
    assert [s["kind"] for s in steps] == [
        "capacity", "capacity", "capacity", "bottleneck", "flow_rate",
        "utilization", "utilization", "utilization",
    ]
    assert steps[0] == {
        "kind": "capacity", "resource": "A", "processing_time": 10.0,
        "servers": 2, "capacity": pytest.approx(0.2),
    }
    assert steps[3] == {
        "kind": "bottleneck", "resource": "B", "capacity": pytest.approx(1 / 6),
    }
    flow = steps[4]
    assert flow["demand"] == pytest.approx(0.15)
    assert flow["rate"] == pytest.approx(0.15)
    assert flow["constraint"] == "demand"
    util_b = steps[6]
    assert util_b["resource"] == "B"
    assert util_b["utilization"] == pytest.approx(0.90)
    assert util_b["implied"] == pytest.approx(0.90)  # rate = demand here


def test_capacity_steps_without_demand_are_capacity_constrained():
    steps = capacity_steps(RESOURCES)
    flow = next(s for s in steps if s["kind"] == "flow_rate")
    assert flow["demand"] is None
    assert flow["constraint"] == "capacity"
    assert flow["rate"] == pytest.approx(1 / 6)
    utils = [s for s in steps if s["kind"] == "utilization"]
    assert utils[0]["implied"] is None
    # flow rate = bottleneck capacity -> the bottleneck runs flat out
    assert utils[1]["utilization"] == pytest.approx(1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_capacity.py -q`
Expected: FAIL — `ImportError: cannot import name 'capacity_steps'`.

- [ ] **Step 3: Implement**

Append to `core/process_analysis/capacity.py`:

```python
def capacity_steps(resources: list[Resource], demand: float | None = None) -> list[dict]:
    """Narrate the capacity analysis as structured steps for the UI player,
    in the order you'd compute it by hand: each resource's capacity, the
    minimum (bottleneck), the flow-rate decision, then utilizations."""
    validate_resources(resources)
    steps: list[dict] = [
        {
            "kind": "capacity",
            "resource": r.name,
            "processing_time": r.processing_time,
            "servers": r.servers,
            "capacity": r.capacity,
        }
        for r in resources
    ]
    bn = bottleneck(resources)
    steps.append({"kind": "bottleneck", "resource": bn.name, "capacity": bn.capacity})
    rate = flow_rate(resources, demand)
    constrained_by_demand = demand is not None and demand < bn.capacity
    steps.append(
        {
            "kind": "flow_rate",
            "capacity": bn.capacity,
            "demand": demand,
            "rate": rate,
            "constraint": "demand" if constrained_by_demand else "capacity",
        }
    )
    for r in resources:
        steps.append(
            {
                "kind": "utilization",
                "resource": r.name,
                "utilization": utilization(r, rate),
                "implied": None if demand is None else implied_utilization(r, demand),
            }
        )
    return steps
```

In `core/process_analysis/__init__.py`, add `capacity_steps` to the
`.capacity` import and to `__all__` (alphabetical: after `bottleneck`).

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 136 passed.

- [ ] **Step 5: Commit**

```bash
git add core/process_analysis tests/test_capacity.py
git commit -m "feat: record capacity analysis steps for the teaching drawer"
```

---

### Task 2: Process-analysis endpoints

**Files:**
- Create: `api/routers/process_analysis.py`
- Modify: `api/main.py`
- Test: `tests/test_api_process_analysis.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_process_analysis.py`:

```python
"""Process-analysis API endpoints, validated against the hand-traced
example in tests/test_capacity.py (A 10minx2, B 6min, C 4min; demand 0.15/min)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SOLVE_REQUEST = {
    "resources": [
        {"name": "A", "processing_time": 10, "servers": 2},
        {"name": "B", "processing_time": 6},
        {"name": "C", "processing_time": 4},
    ],
    "demand": 0.15,
}


def test_solve_endpoint_worked_example():
    response = client.post("/api/process-analysis/solve", json=SOLVE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["bottleneck"] == "B"
    assert body["process_capacity"] == pytest.approx(1 / 6)
    assert body["flow_rate"] == pytest.approx(0.15)
    assert body["constraint"] == "demand"
    assert body["unloaded_flow_time"] == pytest.approx(20.0)
    a = body["resources"][0]
    assert a["capacity"] == pytest.approx(0.2)
    assert a["utilization"] == pytest.approx(0.75)
    assert a["implied_utilization"] == pytest.approx(0.75)
    # narration for the teaching drawer
    assert body["steps"][0]["kind"] == "capacity"
    assert body["steps"][3] == {
        "kind": "bottleneck", "resource": "B", "capacity": pytest.approx(1 / 6),
    }


def test_solve_without_demand_is_capacity_constrained():
    request = {"resources": SOLVE_REQUEST["resources"]}
    response = client.post("/api/process-analysis/solve", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["constraint"] == "capacity"
    assert body["flow_rate"] == pytest.approx(1 / 6)
    assert body["resources"][0]["implied_utilization"] is None


def test_solve_rejects_duplicate_names_with_core_message():
    bad = {"resources": [{"name": "A", "processing_time": 5},
                         {"name": "A", "processing_time": 3}]}
    response = client.post("/api/process-analysis/solve", json=bad)
    assert response.status_code == 422
    assert "uplicate" in response.json()["detail"]


def test_solve_rejects_fractional_servers():
    bad = {"resources": [{"name": "A", "processing_time": 5, "servers": 1.5}]}
    response = client.post("/api/process-analysis/solve", json=bad)
    assert response.status_code == 422
    assert "whole number" in response.json()["detail"]


def test_littles_law_solves_the_missing_variable():
    response = client.post(
        "/api/process-analysis/littles-law",
        json={"inventory": 20, "flow_rate": 4},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["solved_for"] == "flow_time"
    assert body["flow_time"] == pytest.approx(5.0)
    assert body["inventory"] == pytest.approx(20.0)
    assert body["flow_rate"] == pytest.approx(4.0)


def test_littles_law_requires_exactly_one_unknown():
    response = client.post(
        "/api/process-analysis/littles-law", json={"inventory": 20}
    )
    assert response.status_code == 422
    assert "exactly one" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_process_analysis.py -q`
Expected: FAIL — 404, routes do not exist.

- [ ] **Step 3: Implement the router**

Create `api/routers/process_analysis.py`:

```python
"""Process-analysis endpoints: capacity/bottleneck analysis and Little's Law.

Unit-agnostic like core/: capacities come out in units per the same time
unit as processing_time. The frontend sends minutes and shows units/hour.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.process_analysis import (
    Resource,
    bottleneck,
    capacity_steps,
    flow_rate,
    implied_utilization,
    process_capacity,
    solve_littles_law,
    unloaded_flow_time,
    utilization,
)

router = APIRouter(prefix="/api/process-analysis", tags=["process-analysis"])


class ResourceIn(BaseModel):
    name: str
    processing_time: float
    # float so a typed "1.5" reaches our check below and fails with a human
    # message instead of pydantic's structured 422
    servers: float = 1


class SolveRequest(BaseModel):
    resources: list[ResourceIn]
    demand: float | None = None


class ResourceOut(BaseModel):
    name: str
    processing_time: float
    servers: int
    capacity: float
    utilization: float
    implied_utilization: float | None


class SolveResponse(BaseModel):
    bottleneck: str
    process_capacity: float
    flow_rate: float
    constraint: str  # "demand" | "capacity"
    unloaded_flow_time: float
    resources: list[ResourceOut]
    steps: list[dict]


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    for r in req.resources:
        if r.servers != int(r.servers):
            raise ValueError(f"Resource {r.name}: servers must be a whole number.")
    resources = [
        Resource(r.name, r.processing_time, int(r.servers)) for r in req.resources
    ]
    if req.demand is not None and req.demand <= 0:
        raise ValueError("Demand must be positive.")
    # capacity_steps validates the resources (core's message -> 422)
    steps = capacity_steps(resources, req.demand)
    rate = flow_rate(resources, req.demand)
    flow_step = next(s for s in steps if s["kind"] == "flow_rate")
    return SolveResponse(
        bottleneck=bottleneck(resources).name,
        process_capacity=process_capacity(resources),
        flow_rate=rate,
        constraint=flow_step["constraint"],
        unloaded_flow_time=unloaded_flow_time(resources),
        resources=[
            ResourceOut(
                name=r.name,
                processing_time=r.processing_time,
                servers=r.servers,
                capacity=r.capacity,
                utilization=utilization(r, rate),
                implied_utilization=(
                    None if req.demand is None else implied_utilization(r, req.demand)
                ),
            )
            for r in resources
        ],
        steps=steps,
    )


class LittlesLawRequest(BaseModel):
    inventory: float | None = None
    flow_rate: float | None = None
    flow_time: float | None = None


class LittlesLawResponse(BaseModel):
    solved_for: str
    inventory: float
    flow_rate: float
    flow_time: float


@router.post("/littles-law", response_model=LittlesLawResponse)
def littles_law(req: LittlesLawRequest) -> LittlesLawResponse:
    value = solve_littles_law(req.inventory, req.flow_rate, req.flow_time)
    known = {
        "inventory": req.inventory,
        "flow_rate": req.flow_rate,
        "flow_time": req.flow_time,
    }
    solved_for = next(name for name, v in known.items() if v is None)
    known[solved_for] = value
    return LittlesLawResponse(solved_for=solved_for, **known)
```

In `api/main.py`, change the routers import to:

```python
from api.routers import line_balancing, lot_sizing, process_analysis, scheduling
```

and add with the others (alphabetical):

```python
app.include_router(process_analysis.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 142 passed, none broken.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api_process_analysis.py
git commit -m "feat: add process-analysis solve and littles-law endpoints"
```

---

### Task 3: Frontend lib — API types, process URL state, JobsTable idLabel

**Files:**
- Modify: `web/src/lib/api.ts`, `web/src/lib/urlState.ts`, `web/src/components/JobsTable.tsx`
- Test: `web/src/lib/urlState.test.ts` (append)

- [ ] **Step 1: Write the failing tests**

Append to `web/src/lib/urlState.test.ts` (merge `decodeProcess`,
`encodeProcess` into the existing `./urlState` import):

```ts
describe("process analysis URL state", () => {
  it("round-trips resources and a known demand", () => {
    const inputs = {
      resources: [
        { name: "Take order", timeMin: 1.5, servers: 1 },
        { name: "Make sandwich", timeMin: 3, servers: 2 },
      ],
      demandPerHour: 35,
    };
    expect(decodeProcess("?" + encodeProcess(inputs))).toEqual(inputs);
  });

  it("round-trips capacity-only inputs (no demand)", () => {
    const inputs = {
      resources: [{ name: "A", timeMin: 10, servers: 2 }],
      demandPerHour: null,
    };
    expect(decodeProcess("?" + encodeProcess(inputs))).toEqual(inputs);
  });

  it("returns null for malformed resource strings", () => {
    expect(decodeProcess("")).toBeNull();
    expect(decodeProcess("?r=A,x,1")).toBeNull();
    expect(decodeProcess("?r=A,10,2&d=abc")).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — `encodeProcess` / `decodeProcess` not exported.

- [ ] **Step 3: Implement**

Append to `web/src/lib/api.ts`:

```ts
export interface ProcessResource {
  name: string;
  processing_time: number;
  servers: number;
  capacity: number;
  utilization: number;
  implied_utilization: number | null;
}

export interface ProcessStep {
  kind: "capacity" | "bottleneck" | "flow_rate" | "utilization";
  resource?: string;
  processing_time?: number;
  servers?: number;
  capacity?: number;
  demand?: number | null;
  rate?: number;
  constraint?: "demand" | "capacity";
  utilization?: number;
  implied?: number | null;
}

export interface ProcessResponse {
  bottleneck: string;
  process_capacity: number;
  flow_rate: number;
  constraint: "demand" | "capacity";
  unloaded_flow_time: number;
  resources: ProcessResource[];
  steps: ProcessStep[];
}

export type LittlesVariable = "inventory" | "flow_rate" | "flow_time";

export interface LittlesLawResponse {
  solved_for: LittlesVariable;
  inventory: number;
  flow_rate: number;
  flow_time: number;
}
```

Append to `web/src/lib/urlState.ts`:

```ts
export interface ProcessResourceInput {
  name: string;
  timeMin: number; // minutes per unit (the UI's display unit convention)
  servers: number;
}

export interface ProcessInputs {
  resources: ProcessResourceInput[];
  demandPerHour: number | null; // null = capacity-only analysis
}

// Resources encode as r=name,minutes,servers;... plus optional d=<units/hour>.
// Names containing "," or ";" break the format; decode returns null and the
// page falls back to a preset.
export function encodeProcess(inputs: ProcessInputs): string {
  const params = new URLSearchParams();
  params.set(
    "r",
    inputs.resources
      .map((x) => [x.name, x.timeMin, x.servers].join(","))
      .join(";"),
  );
  if (inputs.demandPerHour !== null) params.set("d", String(inputs.demandPerHour));
  return params.toString();
}

export function decodeProcess(search: string): ProcessInputs | null {
  const params = new URLSearchParams(search);
  const raw = params.get("r");
  if (!raw) return null;
  const resources: ProcessResourceInput[] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const timeMin = Number(fields[1]);
    const servers = Number(fields[2]);
    if (Number.isNaN(timeMin) || Number.isNaN(servers)) return null;
    resources.push({ name: fields[0], timeMin, servers });
  }
  const d = params.get("d");
  if (d === null) return { resources, demandPerHour: null };
  const demandPerHour = Number(d);
  if (Number.isNaN(demandPerHour)) return null;
  return { resources, demandPerHour };
}
```

In `web/src/components/JobsTable.tsx`, generalize the hardcoded "job"
wording so the table also serves process resources. Add `idLabel` to the
props (after `label`):

```ts
  label,
  idLabel = "job",
  columns,
  rows,
  onChange,
}: {
  label: string;
  idLabel?: string;
  columns: [string, string];
```

then replace `<th>job</th>` with `<th>{idLabel}</th>`, the two action
buttons with `+ {idLabel}` / `− {idLabel}`, and in `addRow` derive the ID
prefix from the label instead of the literal `J`:

```ts
  const addRow = () => {
    const prefix = idLabel.charAt(0).toUpperCase();
    let n = rows.length + 1;
    while (rows.some((r) => r.id === `${prefix}${n}`)) n += 1;
    onChange([...rows, { id: `${prefix}${n}`, a: 1, b: 1 }]);
  };
```

(Scheduling's two call sites pass no `idLabel`, so they keep "job" and `J`.)

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 18 passed. Also `npm run build` — clean.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib web/src/components/JobsTable.tsx
git commit -m "feat: add process-analysis api types and url state"
```

---

### Task 4: Capacity and utilization chart traces

**Files:**
- Create: `web/src/pages/process-analysis/charts.ts`
- Test: `web/src/pages/process-analysis/charts.test.ts`

These port `app/process_charts.py` nearly 1:1, restyled to the Clean Lab
palette (teal `#0d9488` bars, red `#dc2626` for the bottleneck/overload).
The demand line and the 100% line are layout shapes added in the view.

- [ ] **Step 1: Write the failing tests**

Create `web/src/pages/process-analysis/charts.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { capacityTrace, perHour, utilizationTrace } from "./charts";

const RESOURCES = [
  { name: "A", processing_time: 10, servers: 2, capacity: 0.2, utilization: 0.75, implied_utilization: 0.75 },
  { name: "B", processing_time: 6, servers: 1, capacity: 1 / 6, utilization: 0.9, implied_utilization: 0.9 },
];

describe("capacityTrace", () => {
  it("converts per-minute capacities to units/hour and flags the bottleneck", () => {
    const trace = capacityTrace(RESOURCES, "B") as any;
    expect(trace.y[0]).toBeCloseTo(12); // 0.2/min * 60
    expect(trace.y[1]).toBeCloseTo(10);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("utilizationTrace", () => {
  it("shows percentages and turns overload (>100%) red", () => {
    const trace = utilizationTrace(["A", "B"], [0.75, 1.2]) as any;
    expect(trace.x).toEqual([75, 120]);
    expect(trace.text).toEqual(["75%", "120%"]);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("perHour", () => {
  it("formats a per-minute rate as units per hour", () => {
    expect(perHour(1 / 6)).toBe("10");
    expect(perHour(0.15)).toBe("9");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — module `./charts` doesn't exist.

- [ ] **Step 3: Implement**

Create `web/src/pages/process-analysis/charts.ts`:

```ts
import type { Data } from "plotly.js";
import type { ProcessResource } from "../../lib/api";
import { formatNumber } from "../../lib/format";

/** Core and the API are unit-agnostic (per-minute); the UI convention is
 * processing times in minutes and rates in units/hour. */
export const perHour = (perMin: number) => formatNumber(perMin * 60);

/** Capacity per resource in units/hour; the bottleneck bar is red.
 * The dashed demand line is a layout shape added by the view. */
export function capacityTrace(
  resources: ProcessResource[],
  bottleneckName: string,
): Data {
  return {
    type: "bar",
    x: resources.map((r) => r.name),
    y: resources.map((r) => r.capacity * 60),
    marker: {
      color: resources.map((r) =>
        r.name === bottleneckName ? "#dc2626" : "#0d9488",
      ),
    },
    text: resources.map((r) => perHour(r.capacity)),
    textposition: "outside",
    hoverinfo: "x+y",
    showlegend: false,
  };
}

/** Horizontal utilization bars; anything past the 100% line is overload. */
export function utilizationTrace(names: string[], values: number[]): Data {
  return {
    type: "bar",
    orientation: "h",
    y: names,
    x: values.map((v) => v * 100),
    marker: {
      color: values.map((v) => (v > 1 ? "#dc2626" : "#0d9488")),
    },
    text: values.map((v) => `${Math.round(v * 100)}%`),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 21 passed.

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/process-analysis
git commit -m "feat: add capacity and utilization chart traces"
```

---

### Task 5: Bottleneck teaching drawer and presets

**Files:**
- Create: `web/src/pages/process-analysis/BottleneckDrawer.tsx`, `web/src/pages/process-analysis/presets.ts`

- [ ] **Step 1: Presets**

Create `web/src/pages/process-analysis/presets.ts` (ported from
`PROCESS_EXAMPLES` in `app/examples.py`):

```ts
import type { ProcessInputs } from "../../lib/urlState";

export const PROCESS_PRESETS: Record<string, ProcessInputs> = {
  "Sandwich line": {
    resources: [
      { name: "Take order", timeMin: 1.5, servers: 1 },
      { name: "Make sandwich", timeMin: 3, servers: 2 },
      { name: "Toast", timeMin: 2, servers: 1 },
      { name: "Checkout", timeMin: 1, servers: 1 },
    ],
    demandPerHour: 35,
  },
  "Health clinic (overloaded)": {
    resources: [
      { name: "Reception", timeMin: 5, servers: 1 },
      { name: "Nurse triage", timeMin: 15, servers: 2 },
      { name: "Doctor consult", timeMin: 20, servers: 3 },
    ],
    demandPerHour: 10,
  },
  "Three-step demo": {
    resources: [
      { name: "A", timeMin: 10, servers: 2 },
      { name: "B", timeMin: 6, servers: 1 },
      { name: "C", timeMin: 4, servers: 1 },
    ],
    demandPerHour: 9,
  },
};
```

- [ ] **Step 2: BottleneckDrawer**

Create `web/src/pages/process-analysis/BottleneckDrawer.tsx`:

```tsx
import type { ProcessStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatNumber } from "../../lib/format";
import { perHour } from "./charts";

function describe(step: ProcessStep) {
  if (step.kind === "capacity") {
    return (
      <>
        <b>{step.resource}</b> takes {formatNumber(step.processing_time!)} min/unit
        with {step.servers} server{step.servers! > 1 ? "s" : ""} → capacity ={" "}
        {step.servers} ÷ {formatNumber(step.processing_time!)} ={" "}
        <b>{perHour(step.capacity!)} units/hour</b>.
      </>
    );
  }
  if (step.kind === "bottleneck") {
    return (
      <>
        The lowest capacity wins: <b>{step.resource}</b> at{" "}
        {perHour(step.capacity!)}/h is the{" "}
        <span className="step-bad">bottleneck</span> — the process can never
        flow faster than its slowest resource.
      </>
    );
  }
  if (step.kind === "flow_rate") {
    if (step.constraint === "demand") {
      return (
        <>
          Demand ({perHour(step.demand!)}/h) is below the bottleneck's{" "}
          {perHour(step.capacity!)}/h, so the process is{" "}
          <span className="step-good">demand-constrained</span>: flow rate ={" "}
          <b>{perHour(step.rate!)}/h</b>.
        </>
      );
    }
    return (
      <>
        {step.demand != null
          ? `Demand (${perHour(step.demand)}/h) exceeds what the bottleneck can do, so the process is `
          : "With no demand given, the process is "}
        <span className="step-bad">capacity-constrained</span>: flow rate =
        bottleneck capacity = <b>{perHour(step.rate!)}/h</b>.
      </>
    );
  }
  return (
    <>
      <b>{step.resource}</b> runs at{" "}
      <b>{Math.round(step.utilization! * 100)}%</b> utilization (flow rate ÷
      its capacity)
      {step.implied != null && step.implied > 1 ? (
        <>
          {" "}— but meeting demand would imply{" "}
          <span className="step-bad">{Math.round(step.implied * 100)}%</span>:
          it is overloaded.
        </>
      ) : (
        "."
      )}
    </>
  );
}

export function BottleneckDrawer({ steps }: { steps: ProcessStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Capacity analysis, narrated by the solver"
      question="Why this bottleneck?"
      teaser="watch each resource's capacity get computed and the slowest one set the pace"
      describe={describe}
    />
  );
}
```

- [ ] **Step 3: Build check and commit**

Run (in `web/`): `npm run build` — clean (components are not yet wired into a
page, but must compile).

```bash
git add web/src/pages/process-analysis
git commit -m "feat: add bottleneck drawer and process presets"
```

---

### Task 6: Process Analysis page — views, route, module flip

**Files:**
- Create: `web/src/pages/process-analysis/ProcessView.tsx`, `web/src/pages/process-analysis/LittlesView.tsx`, `web/src/pages/process-analysis/ProcessAnalysisPage.tsx`
- Modify: `web/src/App.tsx`, `web/src/modules.ts`

- [ ] **Step 1: ProcessView**

Create `web/src/pages/process-analysis/ProcessView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { ProcessResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { ProcessInputs } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { BottleneckDrawer } from "./BottleneckDrawer";
import { capacityTrace, perHour, utilizationTrace } from "./charts";
import { PROCESS_PRESETS } from "./presets";

export function ProcessView({
  inputs,
  onInputs,
}: {
  inputs: ProcessInputs;
  onInputs: (next: ProcessInputs) => void;
}) {
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<ProcessResponse>("/process-analysis/solve", {
      resources: debounced.resources.map((r) => ({
        name: r.name,
        processing_time: r.timeMin,
        servers: r.servers,
      })),
      // UI speaks units/hour; core and the API are per-minute
      demand: debounced.demandPerHour === null ? null : debounced.demandPerHour / 60,
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

  const demandKnown = inputs.demandPerHour !== null;
  const names = result?.resources.map((r) => r.name) ?? [];

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Process Analysis</h1>
          <div className="subtitle module-sub">
            Find the bottleneck — the step that sets the pace for everything.
          </div>
        </div>
        <JobsTable
          label="Process steps, in order (minutes/unit, servers)"
          idLabel="resource"
          columns={["min/unit", "servers"]}
          rows={inputs.resources.map((r) => ({ id: r.name, a: r.timeMin, b: r.servers }))}
          onChange={(rows) =>
            onInputs({
              ...inputs,
              resources: rows.map((row) => ({ name: row.id, timeMin: row.a, servers: row.b })),
            })
          }
        />
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Demand</div>
          <div className="mode-pills">
            <button
              className={demandKnown ? "active" : ""}
              onClick={() => onInputs({ ...inputs, demandPerHour: 30 })}
            >
              Known
            </button>
            <button
              className={demandKnown ? "" : "active"}
              onClick={() => onInputs({ ...inputs, demandPerHour: null })}
            >
              Capacity only
            </button>
          </div>
        </div>
        {demandKnown && (
          <NumberField
            label="Demand (units/hour)"
            value={inputs.demandPerHour ?? 0}
            onChange={(demandPerHour) => onInputs({ ...inputs, demandPerHour })}
          />
        )}
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = PROCESS_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(PROCESS_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Bottleneck — the slowest resource sets the pace
              </div>
              <div className="hero-value">
                {result.bottleneck}{" "}
                <span className="hero-detail">
                  capacity {perHour(result.process_capacity)} /h · flow rate{" "}
                  {perHour(result.flow_rate)} /h · {result.constraint}-constrained
                </span>
              </div>
            </div>
            <div className="hero-orders">
              flow rate = min(demand, bottleneck capacity)
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="Process capacity"
              value={`${perHour(result.process_capacity)} /h`}
              detail="the bottleneck's capacity"
            />
            <MetricCard
              label="Flow rate"
              value={`${perHour(result.flow_rate)} /h`}
              detail={`${result.constraint}-constrained`}
            />
            <MetricCard
              label="Flow time (no waiting)"
              value={`${formatNumber(result.unloaded_flow_time)} min`}
              detail="sum of processing times"
            />
          </div>
        )}
        {result && (
          <PlotCard
            label="Capacity per resource (units/hour) — red bar is the bottleneck"
            data={[capacityTrace(result.resources, result.bottleneck)]}
            layout={{
              yaxis: { title: { text: "units/hour" } },
              shapes:
                inputs.demandPerHour === null
                  ? []
                  : [
                      {
                        type: "line",
                        xref: "paper",
                        x0: 0,
                        x1: 1,
                        y0: inputs.demandPerHour,
                        y1: inputs.demandPerHour,
                        line: { color: "#101418", width: 1.5, dash: "dot" },
                      },
                    ],
            }}
            height={240}
          />
        )}
        {result && (
          <div className="row">
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="Utilization (flow rate / capacity)"
                data={[utilizationTrace(names, result.resources.map((r) => r.utilization))]}
                layout={{
                  xaxis: { range: [0, 130], title: { text: "%" } },
                  yaxis: { autorange: "reversed" },
                  shapes: [
                    {
                      type: "line",
                      yref: "paper",
                      x0: 100,
                      x1: 100,
                      y0: 0,
                      y1: 1,
                      line: { color: "#8a94a0", width: 1, dash: "dot" },
                    },
                  ],
                }}
                height={90 + 36 * names.length}
              />
            </div>
            {demandKnown && (
              <div style={{ flex: 1, minWidth: 0 }}>
                <PlotCard
                  label="Implied utilization (demand / capacity) — past 100% is overload"
                  data={[
                    utilizationTrace(
                      names,
                      result.resources.map((r) => r.implied_utilization ?? 0),
                    ),
                  ]}
                  layout={{
                    xaxis: {
                      range: [
                        0,
                        Math.max(
                          130,
                          ...result.resources.map((r) => (r.implied_utilization ?? 0) * 115),
                        ),
                      ],
                      title: { text: "%" },
                    },
                    yaxis: { autorange: "reversed" },
                    shapes: [
                      {
                        type: "line",
                        yref: "paper",
                        x0: 100,
                        x1: 100,
                        y0: 0,
                        y1: 1,
                        line: { color: "#8a94a0", width: 1, dash: "dot" },
                      },
                    ],
                  }}
                  height={90 + 36 * names.length}
                />
              </div>
            )}
          </div>
        )}
        {result && <BottleneckDrawer steps={result.steps} />}
      </div>
    </>
  );
}
```

- [ ] **Step 2: LittlesView**

Create `web/src/pages/process-analysis/LittlesView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { LittlesLawResponse, LittlesVariable } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";

const INFO: Record<LittlesVariable, { label: string; unit: string }> = {
  inventory: { label: "Inventory I", unit: "units in the process" },
  flow_rate: { label: "Flow rate R", unit: "units per time" },
  flow_time: { label: "Flow time T", unit: "time in the process" },
};
const FORMULA: Record<LittlesVariable, string> = {
  inventory: "I = R × T",
  flow_rate: "R = I ÷ T",
  flow_time: "T = I ÷ R",
};
const ORDER: LittlesVariable[] = ["inventory", "flow_rate", "flow_time"];

export interface LittlesInputs {
  solveFor: LittlesVariable;
  inventory: number;
  flowRate: number;
  flowTime: number;
}

export const LITTLES_DEFAULTS: LittlesInputs = {
  solveFor: "flow_time",
  inventory: 20,
  flowRate: 4,
  flowTime: 5,
};

export function LittlesView({
  inputs,
  onInputs,
}: {
  inputs: LittlesInputs;
  onInputs: (next: LittlesInputs) => void;
}) {
  const [result, setResult] = useState<LittlesLawResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<LittlesLawResponse>("/process-analysis/littles-law", {
      inventory: debounced.solveFor === "inventory" ? null : debounced.inventory,
      flow_rate: debounced.solveFor === "flow_rate" ? null : debounced.flowRate,
      flow_time: debounced.solveFor === "flow_time" ? null : debounced.flowTime,
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

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Little's Law</h1>
          <div className="subtitle module-sub">
            I = R × T — know two, get the third. Holds for any stable process.
          </div>
        </div>
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Solve for</div>
          <div className="mode-pills">
            {ORDER.map((v) => (
              <button
                key={v}
                className={inputs.solveFor === v ? "active" : ""}
                onClick={() => onInputs({ ...inputs, solveFor: v })}
              >
                {v === "inventory" ? "I" : v === "flow_rate" ? "R" : "T"}
              </button>
            ))}
          </div>
        </div>
        {inputs.solveFor !== "inventory" && (
          <NumberField
            label="Inventory I (units)"
            value={inputs.inventory}
            onChange={(inventory) => onInputs({ ...inputs, inventory })}
          />
        )}
        {inputs.solveFor !== "flow_rate" && (
          <NumberField
            label="Flow rate R (units/time)"
            value={inputs.flowRate}
            onChange={(flowRate) => onInputs({ ...inputs, flowRate })}
          />
        )}
        {inputs.solveFor !== "flow_time" && (
          <NumberField
            label="Flow time T (time)"
            value={inputs.flowTime}
            onChange={(flowTime) => onInputs({ ...inputs, flowTime })}
          />
        )}
        <div className="subtitle" style={{ fontSize: 11 }}>
          Use consistent units — e.g. R in units/min and T in minutes.
        </div>
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  {FORMULA[result.solved_for]}
                </div>
                <div className="hero-value">
                  {INFO[result.solved_for].label} ={" "}
                  {formatNumber(result[result.solved_for])}{" "}
                  <span className="hero-detail">{INFO[result.solved_for].unit}</span>
                </div>
              </div>
            </div>
            <div className="row">
              {ORDER.map((v) => (
                <MetricCard
                  key={v}
                  label={INFO[v].label}
                  value={formatNumber(result[v])}
                  detail={v === result.solved_for ? "solved" : "given"}
                  selected={v === result.solved_for}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 3: Page wrapper with mode pills and URL state**

Create `web/src/pages/process-analysis/ProcessAnalysisPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeProcess, encodeProcess } from "../../lib/urlState";
import type { ProcessInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { PROCESS_PRESETS } from "./presets";
import { ProcessView } from "./ProcessView";
import { LITTLES_DEFAULTS, LittlesView } from "./LittlesView";
import type { LittlesInputs } from "./LittlesView";

export default function ProcessAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"capacity" | "littles">(
    searchParams.get("mode") === "littles" ? "littles" : "capacity",
  );
  const [inputs, setInputs] = useState<ProcessInputs>(
    () =>
      decodeProcess("?" + searchParams.toString()) ??
      PROCESS_PRESETS["Sandwich line"],
  );
  const [littles, setLittles] = useState<LittlesInputs>(LITTLES_DEFAULTS);

  const update = (next: ProcessInputs) => {
    setInputs(next);
    setSearchParams(encodeProcess(next), { replace: true });
  };

  const switchMode = (next: "capacity" | "littles") => {
    setMode(next);
    setSearchParams(next === "littles" ? "mode=littles" : encodeProcess(inputs), {
      replace: true,
    });
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button
          className={mode === "capacity" ? "active" : ""}
          onClick={() => switchMode("capacity")}
        >
          Capacity & bottleneck
        </button>
        <button
          className={mode === "littles" ? "active" : ""}
          onClick={() => switchMode("littles")}
        >
          Little's Law
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "capacity" ? (
          <ProcessView inputs={inputs} onInputs={update} />
        ) : (
          <LittlesView inputs={littles} onInputs={setLittles} />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Route and module flip**

In `web/src/App.tsx`, add the import (alphabetical, after `LotSizingPage`):

```tsx
import ProcessAnalysisPage from "./pages/process-analysis/ProcessAnalysisPage";
```

and add this route directly below the `/lot-sizing` route:

```tsx
<Route path="/process-analysis" element={<ProcessAnalysisPage />} />
```

In `web/src/modules.ts`, replace the process-analysis entry with:

```ts
  { path: "/process-analysis", name: "Process Analysis", decision: "Where is my bottleneck, and what is it costing me?", icon: Search, ready: true, exampleSearch: "?r=A,10,2;B,6,1;C,4,1&d=9" },
```

- [ ] **Step 5: Verify in the browser**

Run `npm run build` (in `web/`), then uvicorn (repo root):
`.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`, open
`http://localhost:8000/process-analysis?r=A,10,2;B,6,1;C,4,1&d=9` and check:
hero shows bottleneck **B**, capacity **10 /h**, flow rate **9 /h**,
demand-constrained; metric cards show flow time **20 min**; capacity bars
12/10/15 with B red and a dotted demand line at 9; utilization bars
75/90/60% with the implied chart beside it; the drawer narrates "A takes 10
min/unit with 2 servers → capacity = 2 ÷ 10 = 12 units/hour"; switching
demand to "Capacity only" hides the implied chart and shows
capacity-constrained; loading the "Health clinic (overloaded)" preset turns
Nurse triage past 100% (red) in implied utilization; a duplicate resource
name shows core's inline message; the Little's Law pill solves T = 5 for
I=20, R=4 and switching the solve-for pill recomputes; presets and the Home
example link work. Stop the server.

- [ ] **Step 6: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src
git commit -m "feat: add process analysis view with bottleneck and littles law"
```

---

### Task 7: Playwright smoke, docs, final verification

**Files:**
- Create: `web/e2e/process-analysis.spec.ts`
- Modify: `README.md`

- [ ] **Step 1: Write the smoke spec**

Create `web/e2e/process-analysis.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

// Hand-traced ground truth: A 10minx2 (12/h), B 6min (10/h, bottleneck),
// C 4min (15/h); demand 9/h -> demand-constrained, flow rate 9/h.
test("process analysis finds the bottleneck on the shared-link example", async ({ page }) => {
  await page.goto("/process-analysis?r=A,10,2;B,6,1;C,4,1&d=9");
  await expect(page.getByText("capacity 10 /h")).toBeVisible();
  await expect(page.getByText("flow rate 9 /h")).toBeVisible();
  await expect(page.getByText("demand-constrained").first()).toBeVisible();
  await expect(page.getByText("20 min")).toBeVisible(); // unloaded flow time
});

test("teaching drawer narrates the capacity computation", async ({ page }) => {
  await page.goto("/process-analysis?r=A,10,2;B,6,1;C,4,1&d=9");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  // first step: A's capacity = 2 servers / 10 min = 12 units/hour
  await expect(page.getByText(/12 units\/hour/)).toBeVisible();
});

test("littles law mode solves the missing variable", async ({ page }) => {
  await page.goto("/process-analysis?mode=littles");
  await expect(page.getByText("Flow time T = 5")).toBeVisible(); // I=20, R=4
});
```

- [ ] **Step 2: Run the smoke tests**

Run (in `web/`): `npm run e2e`
Expected: 10 passed (3 new + 7 existing).

- [ ] **Step 3: Update the README roadmap line**

In `README.md`, replace

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅, Line Balancing ✅ — remaining modules rolling out one by one
```

with

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅, Line Balancing ✅, Process Analysis ✅ — remaining modules rolling out one by one
```

- [ ] **Step 4: Full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -q` — 142 passed.
Run (in `web/`): `npm test` (21 passed), `npm run build` (clean), `npm run e2e` (10 passed).

- [ ] **Step 5: Commit**

```bash
git add web/e2e README.md
git commit -m "test: add playwright smoke for process analysis; update roadmap"
```

---

## Self-review notes

- **Spec coverage:** both spec'd endpoints `/api/process-analysis/solve` and `/api/process-analysis/littles-law` ✓ (Task 2); all Phase-2 quantities surface in the UI — resource capacity, process capacity, bottleneck (tie → first in order, lives in core), flow rate, utilization, implied utilization (>100% highlighted), unloaded flow time, Little's Law ✓ (Tasks 4–6); units convention "minutes in, units/hour displayed, ×60 in the UI" honoured — core and API stay unit-agnostic, `perHour` is the single conversion point ✓; teaching steps recorded in core with TDD ✓ (Task 1); ergonomics — debounce, sharable URLs, inline 422 errors, presets ported from the Streamlit examples ✓; Playwright smoke on hand-traced numbers ✓ (Task 7).
- **Type consistency:** `ResourceOut` (API) ↔ `ProcessResource` (TS) fields match (`name`, `processing_time`, `servers`, `capacity`, `utilization`, `implied_utilization`) ✓; `ProcessStep` TS fields match the core step dicts incl. `implied`/`constraint` ✓; `LittlesVariable` = `solved_for` values = pydantic field names ✓; `capacityTrace`/`utilizationTrace`/`perHour` signatures identical in tests (Task 4) and view (Task 6) ✓; `idLabel` prop added in Task 3 is what Task 6 passes ✓.
- **Conventions:** no solver behavior changes — `capacity_steps` only reads via the existing public functions; constraint wording matches the Streamlit caption (`demand < capacity` ⇒ demand-constrained).
- **Known limitations:** resource names containing `,` or `;` break the URL encoding (decode → null → preset fallback) — same documented trade-off as scheduling/line-balancing; Little's Law inputs are session-local (no URL state beyond `mode=littles`), mirroring how EOQ mode works.
