# React Redesign Phase 6: Cellular Manufacturing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Cellular Manufacturing module in the React app: Rank Order Clustering on a clickable machine–part incidence matrix, before/after heatmaps with the cells colored by what each entry does to grouping efficacy, cell composition, and a teaching drawer that narrates the binary-value sorting passes.

**Architecture:** `core/cellular` already has ROC, exact cell formation, and grouping efficacy, hand-traced and tested. It gains step recording: `rank_order_clustering` accepts an optional `steps` list (so the narration is emitted by the real loop, not a re-implementation), and a new `solve_cells(matrix)` one-shot returns orders + cells + metrics + steps in one dict. A thin `api/routers/cellular.py` exposes `/api/cellular/solve` and **echoes the input matrix** in the response so the frontend renders heatmaps from one consistent payload (the live input is debounced, so orders must index into the matrix they were computed from, not the current edit). The frontend gains a `/cellular` page: a `MatrixEditor` grid of toggle cells (machines auto-named M1.., parts P1..), two heatmap PlotCards (original vs clustered, ported from `app/cell_charts.py` in Clean Lab colors), cell-composition cards, and a `RocDrawer` on the shared `StepPlayer`.

**Tech Stack:** Python 3.11+, FastAPI, pytest; React 18 + TypeScript, Plotly, Vitest, Playwright. No new dependencies.

**Context for the engineer:** Operations Management teaching toolkit; solver math lives in `core/` with hand-traced tests in `tests/` — never change solver behavior. Specs: `docs/superpowers/specs/2026-06-11-react-redesign-design.md` (UI pattern) and `docs/superpowers/specs/2026-06-11-cellular-design.md` (math + hand traces). Copy the pattern of the shipped modules (`api/routers/process_analysis.py` for a router, `web/src/pages/process-analysis/` for a page). The legacy Streamlit page `app/pages/5_Cellular.py` + `app/cell_charts.py` show exactly what to port. Python runs via `.\.venv\Scripts\python.exe`; frontend commands run in `web/`.

**Reference — hand-traced Example A used everywhere below (already encoded in `tests/test_roc.py` / `tests/test_cells.py`):**

```
     P1 P2 P3 P4 P5
M1:   1  0  0  1  0    row values (P1 = MSB): M1 = 10010 = 18, M2 = 13,
M2:   0  1  1  0  1    M3 = 18, M4 = 12
M3:   1  0  0  1  0
M4:   0  1  1  0  0
```

- Pass 1 rows: values `[18, 13, 18, 12]` (indexed by original machine) → order `[0, 2, 1, 3]` (M1, M3, M2, M4; the 18–18 tie keeps current order).
- Pass 1 cols (read in the new row order): values `[12, 3, 3, 12, 2]` → order `[0, 3, 1, 2, 4]` (P1, P4, P2, P3, P5).
- Pass 2: row values become `[24, 7, 24, 6]`, col values `[12, 3, 3, 12, 2]` — neither order changes → converged in 2 iterations.
- Cells: `machine_cells = [0, 1, 0, 1]`, `part_cells = [0, 1, 1, 0, 1]` (2 cells: {M1,M3}×{P1,P4}, {M2,M4}×{P2,P3,P5}).
- Efficacy: e = 9 ones, 0 exceptional, 1 void (M4–P5) → μ = 9/10 = **0.9**.
- Example B (`MATRIX_B` in `tests/test_cells.py`): e = 8, 1 exceptional, 1 void → μ = 7/9.

---

### Task 1: Step recording in core + one-shot solve_cells

**Files:**
- Modify: `core/cellular/roc.py`, `core/cellular/cells.py`, `core/cellular/__init__.py`
- Test: `tests/test_cells.py` (append)

Step schema (all indices refer to ORIGINAL matrix positions; the UI derives
names M{i+1}/P{j+1} itself):
- `{"kind": "rows", "iteration": 1, "values": [18, 13, 18, 12], "order": [0, 2, 1, 3], "changed": True}` — one per pass; `values[i]` is machine i's binary value read in the current column order, `order` is the new row order.
- `{"kind": "cols", ...}` — same for columns, read in the pass's new row order.
- `{"kind": "converged", "iterations": 2}`
- `{"kind": "cells", "machine_cells": [0, 1, 0, 1], "part_cells": [0, 1, 1, 0, 1], "n_cells": 2}`
- `{"kind": "efficacy", "total_ones": 9, "exceptional": 0, "voids": 1, "grouping_efficacy": 0.9}`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cells.py`, and change its import line to:

```python
from core.cellular.cells import (
    MAX_PARTITION_MACHINES,
    evaluate_cells,
    find_best_cells,
    solve_cells,
)
```

```python
def test_solve_cells_worked_example_a():
    """One-shot solve = ROC orders + best cells + metrics + narration steps.
    Step values are the hand trace: pass-1 row values 18,13,18,12 etc."""
    result = solve_cells(MATRIX_A)
    assert result["row_order"] == [0, 2, 1, 3]
    assert result["col_order"] == [0, 3, 1, 2, 4]
    assert result["iterations"] == 2
    assert result["machine_cells"] == [0, 1, 0, 1]
    assert result["part_cells"] == [0, 1, 1, 0, 1]
    assert result["n_cells"] == 2
    assert result["grouping_efficacy"] == pytest.approx(0.9)
    assert [s["kind"] for s in result["steps"]] == [
        "rows", "cols", "rows", "cols", "converged", "cells", "efficacy",
    ]
    assert result["steps"][0] == {
        "kind": "rows", "iteration": 1, "values": [18, 13, 18, 12],
        "order": [0, 2, 1, 3], "changed": True,
    }
    assert result["steps"][1] == {
        "kind": "cols", "iteration": 1, "values": [12, 3, 3, 12, 2],
        "order": [0, 3, 1, 2, 4], "changed": True,
    }


def test_solve_cells_final_pass_reports_no_change():
    steps = solve_cells(MATRIX_A)["steps"]
    # pass 2 re-sorts and finds the same orders -> changed False, then stop
    assert steps[2]["changed"] is False
    assert steps[3]["changed"] is False
    assert steps[4] == {"kind": "converged", "iterations": 2}
    assert steps[5] == {
        "kind": "cells", "machine_cells": [0, 1, 0, 1],
        "part_cells": [0, 1, 1, 0, 1], "n_cells": 2,
    }


def test_solve_cells_example_b_counts_exceptional_and_voids():
    result = solve_cells(MATRIX_B)
    assert result["total_ones"] == 8
    assert result["exceptional"] == 1
    assert result["voids"] == 1
    assert result["grouping_efficacy"] == pytest.approx(7 / 9)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_cells.py -q`
Expected: FAIL — `ImportError: cannot import name 'solve_cells'`.

- [ ] **Step 3: Implement**

In `core/cellular/roc.py`, replace `_sorted_by_binary_value` with a values
helper (so the recorded steps can show the numbers a student would write
down) and add the optional `steps` parameter to `rank_order_clustering`:

```python
def _binary_values(vectors: list[list[int]]) -> list[int]:
    """Each vector read as a binary number, first element = most significant."""
    values = []
    for vector in vectors:
        bits = 0
        for bit in vector:
            bits = bits * 2 + bit
        values.append(bits)
    return values


def _sorted_by_value(values: list[int], current: list[int]) -> list[int]:
    """Reorder `current` indices by decreasing value. The sort is stable, so
    ties keep their current relative order (the ROC analogue of the course's
    lower-ID tie-break)."""
    return sorted(current, key=lambda index: values[index], reverse=True)


def rank_order_clustering(
    matrix: list[list[int]], steps: list[dict] | None = None
) -> RocResult:
    """If `steps` is given, every row/column pass is appended to it as a
    structured step for the UI player (values indexed by ORIGINAL position)."""
    validate_matrix(matrix)
    n_rows, n_cols = len(matrix), len(matrix[0])
    row_order = list(range(n_rows))
    col_order = list(range(n_cols))

    iterations = 0
    while True:
        iterations += 1
        # Row pass: each row read left-to-right in the CURRENT column order.
        rows = [[matrix[i][j] for j in col_order] for i in range(n_rows)]
        row_values = _binary_values(rows)
        new_rows = _sorted_by_value(row_values, row_order)
        # Column pass: each column read top-to-bottom in the NEW row order.
        cols = [[matrix[i][j] for i in new_rows] for j in range(n_cols)]
        col_values = _binary_values(cols)
        new_cols = _sorted_by_value(col_values, col_order)

        if steps is not None:
            steps.append({
                "kind": "rows", "iteration": iterations, "values": row_values,
                "order": new_rows, "changed": new_rows != row_order,
            })
            steps.append({
                "kind": "cols", "iteration": iterations, "values": col_values,
                "order": new_cols, "changed": new_cols != col_order,
            })

        if new_rows == row_order and new_cols == col_order:
            return RocResult(row_order, col_order, iterations)
        row_order, col_order = new_rows, new_cols
```

(Behavior is unchanged — same stable descending sort — which the existing
`tests/test_roc.py` traces confirm.)

In `core/cellular/cells.py`, change the top import to
`from .roc import rank_order_clustering, validate_matrix` and append:

```python
def solve_cells(matrix: list[list[int]]) -> dict:
    """One-shot solve for the API: ROC ordering, the best consecutive cell
    partition, its quality metrics, and the narration steps for the UI."""
    steps: list[dict] = []
    roc = rank_order_clustering(matrix, steps)
    steps.append({"kind": "converged", "iterations": roc.iterations})
    machine_cells, part_cells = find_best_cells(matrix, roc.row_order)
    n_cells = max(machine_cells) + 1
    steps.append({
        "kind": "cells",
        "machine_cells": machine_cells,
        "part_cells": part_cells,
        "n_cells": n_cells,
    })
    metrics = evaluate_cells(matrix, machine_cells, part_cells)
    steps.append({"kind": "efficacy", **metrics})
    return {
        "row_order": roc.row_order,
        "col_order": roc.col_order,
        "iterations": roc.iterations,
        "machine_cells": machine_cells,
        "part_cells": part_cells,
        "n_cells": n_cells,
        **metrics,
        "steps": steps,
    }
```

In `core/cellular/__init__.py`, add `solve_cells` to the `.cells` import and
to `__all__` (alphabetical: after `reorder_matrix`).

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 145 passed.

- [ ] **Step 5: Commit**

```bash
git add core/cellular tests/test_cells.py
git commit -m "feat: record roc passes and add one-shot solve_cells"
```

---

### Task 2: Cellular solve endpoint

**Files:**
- Create: `api/routers/cellular.py`
- Modify: `api/main.py`
- Test: `tests/test_api_cellular.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_cellular.py`:

```python
"""Cellular API endpoint, validated against the hand-traced Example A
(tests/test_cells.py): ROC orders M1,M3,M2,M4 / P1,P4,P2,P3,P5; 2 cells;
e = 9, 0 exceptional, 1 void -> grouping efficacy 0.9."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

MATRIX_A = [
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
]


def test_solve_endpoint_worked_example():
    response = client.post("/api/cellular/solve", json={"matrix": MATRIX_A})
    assert response.status_code == 200
    body = response.json()
    assert body["matrix"] == MATRIX_A  # echoed for consistent rendering
    assert body["row_order"] == [0, 2, 1, 3]
    assert body["col_order"] == [0, 3, 1, 2, 4]
    assert body["iterations"] == 2
    assert body["machine_cells"] == [0, 1, 0, 1]
    assert body["part_cells"] == [0, 1, 1, 0, 1]
    assert body["n_cells"] == 2
    assert body["exceptional"] == 0
    assert body["voids"] == 1
    assert body["grouping_efficacy"] == pytest.approx(0.9)
    # narration for the teaching drawer
    assert body["steps"][0]["kind"] == "rows"
    assert body["steps"][0]["values"] == [18, 13, 18, 12]
    assert body["steps"][-1]["kind"] == "efficacy"


def test_solve_rejects_non_binary_matrix_with_core_message():
    response = client.post("/api/cellular/solve", json={"matrix": [[1, 2], [0, 1]]})
    assert response.status_code == 422
    assert "0 or 1" in response.json()["detail"]


def test_solve_rejects_zero_row_with_core_message():
    response = client.post("/api/cellular/solve", json={"matrix": [[1, 1], [0, 0]]})
    assert response.status_code == 422
    assert "processes no parts" in response.json()["detail"]


def test_solve_rejects_oversized_instances():
    # 17 machines x 1 part: valid matrix, but past the exact-search cap
    response = client.post("/api/cellular/solve", json={"matrix": [[1]] * 17})
    assert response.status_code == 422
    assert "16" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_cellular.py -q`
Expected: FAIL — 404, route does not exist.

- [ ] **Step 3: Implement the router**

Create `api/routers/cellular.py`:

```python
"""Cellular manufacturing endpoint: Rank Order Clustering + cell formation.

The response echoes the input matrix so the frontend renders the heatmaps
from one consistent payload — the page input is debounced, and the orders
must index into the matrix they were computed from, not the current edit.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.cellular import solve_cells

router = APIRouter(prefix="/api/cellular", tags=["cellular"])


class SolveRequest(BaseModel):
    matrix: list[list[int]]


class SolveResponse(BaseModel):
    matrix: list[list[int]]
    row_order: list[int]
    col_order: list[int]
    iterations: int
    machine_cells: list[int]
    part_cells: list[int]
    n_cells: int
    total_ones: int
    exceptional: int
    voids: int
    grouping_efficacy: float
    steps: list[dict]


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    # solve_cells validates the matrix (core's ValueError message -> 422)
    return SolveResponse(matrix=req.matrix, **solve_cells(req.matrix))
```

In `api/main.py`, change the routers import to:

```python
from api.routers import cellular, line_balancing, lot_sizing, process_analysis, scheduling
```

and add first among the includes (alphabetical):

```python
app.include_router(cellular.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: 149 passed, none broken.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api_cellular.py
git commit -m "feat: add cellular solve endpoint"
```

---

### Task 3: Frontend lib — API types and matrix URL state

**Files:**
- Modify: `web/src/lib/api.ts`, `web/src/lib/urlState.ts`
- Test: `web/src/lib/urlState.test.ts` (append)

- [ ] **Step 1: Write the failing tests**

Append to `web/src/lib/urlState.test.ts` (merge `decodeCellular`,
`encodeCellular` into the existing `./urlState` import):

```ts
describe("cellular URL state", () => {
  it("round-trips the worked example matrix", () => {
    const matrix = [
      [1, 0, 0, 1, 0],
      [0, 1, 1, 0, 1],
      [1, 0, 0, 1, 0],
      [0, 1, 1, 0, 0],
    ];
    expect(decodeCellular("?" + encodeCellular(matrix))).toEqual(matrix);
  });

  it("returns null for malformed or ragged matrices", () => {
    expect(decodeCellular("")).toBeNull();
    expect(decodeCellular("?m=10a10")).toBeNull();
    expect(decodeCellular("?m=10;1")).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — `encodeCellular` / `decodeCellular` not exported.

- [ ] **Step 3: Implement**

Append to `web/src/lib/api.ts`:

```ts
export interface CellularStep {
  kind: "rows" | "cols" | "converged" | "cells" | "efficacy";
  iteration?: number;
  values?: number[];
  order?: number[];
  changed?: boolean;
  iterations?: number;
  machine_cells?: number[];
  part_cells?: number[];
  n_cells?: number;
  total_ones?: number;
  exceptional?: number;
  voids?: number;
  grouping_efficacy?: number;
}

export interface CellularResponse {
  matrix: number[][]; // echoed input; all orders index into this
  row_order: number[];
  col_order: number[];
  iterations: number;
  machine_cells: number[];
  part_cells: number[];
  n_cells: number;
  total_ones: number;
  exceptional: number;
  voids: number;
  grouping_efficacy: number;
  steps: CellularStep[];
}
```

Append to `web/src/lib/urlState.ts`:

```ts
// The incidence matrix encodes as one binary word per machine: m=10010;01101;…
// (machines and parts are auto-named M1../P1.., so only the bits travel).
export function encodeCellular(matrix: number[][]): string {
  const params = new URLSearchParams();
  params.set("m", matrix.map((row) => row.join("")).join(";"));
  return params.toString();
}

export function decodeCellular(search: string): number[][] | null {
  const raw = new URLSearchParams(search).get("m");
  if (!raw) return null;
  const matrix: number[][] = [];
  let width = -1;
  for (const word of raw.split(";")) {
    if (!/^[01]+$/.test(word)) return null;
    if (width === -1) width = word.length;
    if (word.length !== width) return null;
    matrix.push([...word].map(Number));
  }
  return matrix;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 23 passed. Also `npm run build` — clean.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib
git commit -m "feat: add cellular api types and url state"
```

---

### Task 4: Incidence and clustered heatmap traces

**Files:**
- Create: `web/src/pages/cellular/charts.ts`
- Test: `web/src/pages/cellular/charts.test.ts`

These port `app/cell_charts.py` nearly 1:1, restyled to the Clean Lab
palette (teal `#0d9488` for a 1 inside its cell, red `#dc2626` for an
exceptional element, gray `#d9d9d9` for a void).

- [ ] **Step 1: Write the failing tests**

Create `web/src/pages/cellular/charts.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { clusteredTrace, incidenceTrace, names, partDisplayOrder, reorder } from "./charts";

// Hand-traced Example A (tests/test_cells.py)
const MATRIX_A = [
  [1, 0, 0, 1, 0],
  [0, 1, 1, 0, 1],
  [1, 0, 0, 1, 0],
  [0, 1, 1, 0, 0],
];

describe("names", () => {
  it("auto-names machines and parts from 1", () => {
    expect(names("M", 3)).toEqual(["M1", "M2", "M3"]);
  });
});

describe("reorder", () => {
  it("applies the hand-traced ROC orders for example A", () => {
    expect(reorder(MATRIX_A, [0, 2, 1, 3], [0, 3, 1, 2, 4])).toEqual([
      [1, 1, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [0, 0, 1, 1, 1],
      [0, 0, 1, 1, 0],
    ]);
  });
});

describe("partDisplayOrder", () => {
  it("groups part columns by cell, keeping relative ROC order", () => {
    // ROC order [2,0,1] with cells (by original index) [0,1,1]:
    // P1 (cell 0) first, then P3, P2 keep their ROC relative order
    expect(partDisplayOrder([2, 0, 1], [0, 1, 1])).toEqual([0, 2, 1]);
  });
});

describe("incidenceTrace", () => {
  it("passes the binary matrix through as heatmap z", () => {
    const trace = incidenceTrace(MATRIX_A, names("M", 4), names("P", 5)) as any;
    expect(trace.z).toEqual(MATRIX_A);
    expect(trace.y).toEqual(["M1", "M2", "M3", "M4"]);
  });
});

describe("clusteredTrace", () => {
  it("categorizes entries: empty 0, void 1, in-cell 2, exceptional 3", () => {
    // Example A in display order: machines M1,M3,M2,M4 / parts P1,P4,P2,P3,P5
    const ordered = reorder(MATRIX_A, [0, 2, 1, 3], [0, 3, 1, 2, 4]);
    const trace = clusteredTrace(
      ordered,
      ["M1", "M3", "M2", "M4"],
      ["P1", "P4", "P2", "P3", "P5"],
      [0, 0, 1, 1],
      [0, 0, 1, 1, 1],
    ) as any;
    // M4 row: two empties, two in-cell 1s, and the M4-P5 void
    expect(trace.z[3]).toEqual([0, 0, 2, 2, 1]);
    expect(trace.customdata[3]).toEqual(["", "", "in cell", "in cell", "void"]);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — module `./charts` doesn't exist.

- [ ] **Step 3: Implement**

Create `web/src/pages/cellular/charts.ts`:

```ts
import type { Data } from "plotly.js";

// Entry categories (indices into the discrete colorscale below).
const EMPTY = "#ffffff";
const VOID = "#d9d9d9"; // a 0 inside a cell: idle machine-part pairing
const IN_CELL = "#0d9488"; // a 1 inside its cell
const EXCEPTIONAL = "#dc2626"; // a 1 outside every cell: intercell travel
const SCALE: [number, string][] = [
  [0.0, EMPTY], [0.249, EMPTY],
  [0.25, VOID], [0.499, VOID],
  [0.5, IN_CELL], [0.749, IN_CELL],
  [0.75, EXCEPTIONAL], [1.0, EXCEPTIONAL],
];

export const names = (prefix: string, count: number) =>
  Array.from({ length: count }, (_, i) => `${prefix}${i + 1}`);

export function reorder(
  matrix: number[][], rowOrder: number[], colOrder: number[],
): number[][] {
  return rowOrder.map((i) => colOrder.map((j) => matrix[i][j]));
}

/** Part columns regrouped so each cell shows as one contiguous block:
 * stable sort of the ROC column order by each part's cell. */
export function partDisplayOrder(colOrder: number[], partCells: number[]): number[] {
  return [...colOrder].sort((a, b) => partCells[a] - partCells[b]);
}

/** Plain binary incidence matrix: teal = part visits machine. */
export function incidenceTrace(
  matrix: number[][], machineNames: string[], partNames: string[],
): Data {
  return {
    type: "heatmap",
    z: matrix,
    x: partNames,
    y: machineNames,
    zmin: 0,
    zmax: 1,
    colorscale: [[0, EMPTY], [0.499, EMPTY], [0.5, IN_CELL], [1, IN_CELL]],
    showscale: false,
    xgap: 2,
    ygap: 2,
    hovertemplate: "%{y} × %{x}: %{z}<extra></extra>",
  };
}

/** Clustered matrix colored by what each entry does to grouping efficacy.
 * All inputs must already be in display order. */
export function clusteredTrace(
  matrix: number[][],
  machineNames: string[],
  partNames: string[],
  machineCells: number[],
  partCells: number[],
): Data {
  const labels = ["", "void", "in cell", "exceptional"];
  const z = matrix.map((row, i) =>
    row.map((entry, j) => {
      const sameCell = machineCells[i] === partCells[j];
      if (entry === 1) return sameCell ? 2 : 3;
      return sameCell ? 1 : 0;
    }),
  );
  return {
    type: "heatmap",
    z,
    x: partNames,
    y: machineNames,
    zmin: 0,
    zmax: 3,
    colorscale: SCALE,
    showscale: false,
    xgap: 2,
    ygap: 2,
    customdata: z.map((row) => row.map((c) => labels[c])),
    hovertemplate: "%{y} × %{x}: %{customdata}<extra></extra>",
  } as Data;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test` — 28 passed.

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/cellular
git commit -m "feat: add incidence and clustered heatmap traces"
```

---

### Task 5: Matrix editor, ROC teaching drawer, presets

**Files:**
- Create: `web/src/pages/cellular/MatrixEditor.tsx`, `web/src/pages/cellular/MatrixEditor.css`, `web/src/pages/cellular/RocDrawer.tsx`, `web/src/pages/cellular/presets.ts`

- [ ] **Step 1: Presets**

Create `web/src/pages/cellular/presets.ts` (ported from `CELLULAR_EXAMPLES`
in `app/examples.py`):

```ts
export const CELLULAR_PRESETS: Record<string, number[][]> = {
  // The worked example from the test suite: two near-perfect cells
  "Two clean cells (4×5)": [
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
  ],
  // M5 serves parts from two families - exceptional elements are unavoidable
  "Bottleneck machine (5×7)": [
    [1, 0, 0, 1, 0, 0, 1],
    [0, 1, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 1, 1, 0],
    [0, 0, 1, 0, 0, 1, 1],
  ],
  // Three perfect cells hidden by the row order - efficacy 1 after ROC
  "Scrambled blocks (6×8)": [
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 1],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 0, 1, 0, 1, 0, 0, 1],
  ],
};
```

- [ ] **Step 2: MatrixEditor**

Create `web/src/pages/cellular/MatrixEditor.css`:

```css
.matrix-editor { border-collapse: collapse; }
.matrix-editor th {
  font-size: 10px;
  color: var(--subtle);
  font-weight: 600;
  padding: 2px 3px;
  text-align: center;
}
.matrix-editor td { padding: 2px; }
.matrix-editor td button {
  width: 24px;
  height: 24px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: transparent;
  font-size: 11px;
  font-weight: 700;
}
.matrix-editor td button.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.matrix-editor-actions { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.matrix-editor-actions button {
  font-size: 11px;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--subtle);
}
```

Create `web/src/pages/cellular/MatrixEditor.tsx`:

```tsx
import "./MatrixEditor.css";

/** Editable binary incidence matrix: rows = machines, columns = parts.
 * Click a cell to toggle whether the part visits the machine. A freshly
 * added all-zero machine/part triggers core's "remove it" message inline,
 * which tells the user exactly what to do next. */
export function MatrixEditor({
  matrix,
  onChange,
}: {
  matrix: number[][];
  onChange: (next: number[][]) => void;
}) {
  const nParts = matrix[0]?.length ?? 0;

  const toggle = (i: number, j: number) =>
    onChange(
      matrix.map((row, r) =>
        r === i ? row.map((v, c) => (c === j ? 1 - v : v)) : row,
      ),
    );

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        Incidence matrix — tick where the part visits the machine
      </div>
      <table className="matrix-editor">
        <thead>
          <tr>
            <th />
            {Array.from({ length: nParts }, (_, j) => (
              <th key={j}>P{j + 1}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <th>M{i + 1}</th>
              {row.map((v, j) => (
                <td key={j}>
                  <button
                    className={v ? "on" : ""}
                    aria-label={`M${i + 1} × P${j + 1}`}
                    onClick={() => toggle(i, j)}
                  >
                    {v ? "1" : ""}
                  </button>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="matrix-editor-actions">
        <button onClick={() => onChange([...matrix, matrix[0].map(() => 0)])}>
          + machine
        </button>
        <button onClick={() => matrix.length > 1 && onChange(matrix.slice(0, -1))}>
          − machine
        </button>
        <button onClick={() => onChange(matrix.map((row) => [...row, 0]))}>
          + part
        </button>
        <button onClick={() => nParts > 1 && onChange(matrix.map((row) => row.slice(0, -1)))}>
          − part
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: RocDrawer**

Create `web/src/pages/cellular/RocDrawer.tsx`:

```tsx
import type { CellularStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatNumber } from "../../lib/format";

const machine = (i: number) => `M${i + 1}`;
const part = (j: number) => `P${j + 1}`;

/** "M1 = 18, M3 = 18, M2 = 13, M4 = 12" — values listed in the new order. */
function rankList(order: number[], values: number[], name: (i: number) => string) {
  return order.map((i) => `${name(i)} = ${values[i]}`).join(", ");
}

function members(cells: number[], cell: number, name: (i: number) => string) {
  return cells.flatMap((c, i) => (c === cell ? [name(i)] : [])).join(", ");
}

function describe(step: CellularStep) {
  if (step.kind === "rows" || step.kind === "cols") {
    const isRows = step.kind === "rows";
    return (
      <>
        <b>Pass {step.iteration}</b> — read each{" "}
        {isRows ? "machine row" : "part column"} as a binary number (
        {isRows ? "leftmost part" : "topmost machine"} = biggest bit) and sort
        by decreasing value:{" "}
        {rankList(step.order!, step.values!, isRows ? machine : part)}
        {step.changed ? "." : <> — <b>no change</b>.</>}
      </>
    );
  }
  if (step.kind === "converged") {
    return (
      <>
        A full pass changed nothing, so ROC stops after{" "}
        <b>{step.iterations} pass{step.iterations! > 1 ? "es" : ""}</b> — the
        1s have gathered into blocks along the diagonal.
      </>
    );
  }
  if (step.kind === "cells") {
    return (
      <>
        ROC only reorders — the boundaries come from scoring every consecutive
        split of the machine list. Best: <b>{step.n_cells} cells</b>:{" "}
        {Array.from({ length: step.n_cells! }, (_, c) => (
          <span key={c}>
            Cell {c + 1} = {members(step.machine_cells!, c, machine)} ×{" "}
            {members(step.part_cells!, c, part)}
            {c < step.n_cells! - 1 ? " · " : ""}
          </span>
        ))}
        . Each part joins the cell where it has the most operations.
      </>
    );
  }
  return (
    <>
      Grouping efficacy μ = (e − exceptional) / (e + voids) = ({step.total_ones}{" "}
      − <span className="step-bad">{step.exceptional}</span>) / ({step.total_ones}{" "}
      + {step.voids}) = <b>{formatNumber(step.grouping_efficacy!)}</b>.
      Exceptional elements are 1s outside every cell (parts travelling between
      cells); voids are 0s inside a cell (idle pairings). μ = 1 is a perfect
      block diagonal.
    </>
  );
}

export function RocDrawer({ steps }: { steps: CellularStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Rank Order Clustering, narrated by the solver"
      question="How did the blocks appear?"
      teaser="watch rows and columns sort by binary value until the cells emerge"
      describe={describe}
    />
  );
}
```

- [ ] **Step 4: Build check and commit**

Run (in `web/`): `npm run build` — clean (components are not yet wired into a
page, but must compile).

```bash
git add web/src/pages/cellular
git commit -m "feat: add matrix editor, roc drawer, and cellular presets"
```

---

### Task 6: Cellular page — route and module flip

**Files:**
- Create: `web/src/pages/cellular/CellularPage.tsx`
- Modify: `web/src/App.tsx`, `web/src/modules.ts`

- [ ] **Step 1: CellularPage**

Create `web/src/pages/cellular/CellularPage.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ApiError, postJson } from "../../lib/api";
import type { CellularResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { decodeCellular, encodeCellular } from "../../lib/urlState";
import { MetricCard } from "../../components/MetricCard";
import { PlotCard } from "../../components/PlotCard";
import "../../components/workbench.css";
import { MatrixEditor } from "./MatrixEditor";
import { RocDrawer } from "./RocDrawer";
import { clusteredTrace, incidenceTrace, names, partDisplayOrder, reorder } from "./charts";
import { CELLULAR_PRESETS } from "./presets";

const HEATMAP_LAYOUT = {
  xaxis: { side: "top" as const, showgrid: false },
  yaxis: { autorange: "reversed" as const, showgrid: false },
  margin: { l: 60, r: 16, t: 30, b: 10 },
};

export default function CellularPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [matrix, setMatrix] = useState<number[][]>(
    () =>
      decodeCellular("?" + searchParams.toString()) ??
      CELLULAR_PRESETS["Two clean cells (4×5)"],
  );
  const [result, setResult] = useState<CellularResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(matrix);

  const update = (next: number[][]) => {
    setMatrix(next);
    setSearchParams(encodeCellular(next), { replace: true });
  };

  useEffect(() => {
    let cancelled = false;
    postJson<CellularResponse>("/cellular/solve", { matrix: debounced })
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

  // Everything below renders from the echoed result.matrix, never the live
  // input — the orders must index into the matrix they were computed from.
  const displayCols = result ? partDisplayOrder(result.col_order, result.part_cells) : [];
  const machineNames = result ? names("M", result.matrix.length) : [];
  const partNames = result ? names("P", result.matrix[0].length) : [];
  const cells = result
    ? Array.from({ length: result.n_cells }, (_, c) => ({
        machines: result.row_order
          .filter((i) => result.machine_cells[i] === c)
          .map((i) => machineNames[i])
          .join(", "),
        parts: result.col_order
          .filter((j) => result.part_cells[j] === c)
          .map((j) => partNames[j])
          .join(", "),
      }))
    : [];

  return (
    <div className="workbench">
      <div className="input-panel">
        <div>
          <h1>Cellular Manufacturing</h1>
          <div className="subtitle module-sub">
            Group machines into cells so each part family stays in one cell.
          </div>
        </div>
        <MatrixEditor matrix={matrix} onChange={update} />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = CELLULAR_PRESETS[e.target.value];
              if (preset) update(preset.map((row) => [...row]));
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(CELLULAR_PRESETS).map((name) => (
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
                Cells — machines that work as a team
              </div>
              <div className="hero-value">
                {result.n_cells} cells{" "}
                <span className="hero-detail">
                  grouping efficacy {formatNumber(result.grouping_efficacy)} ·
                  converged in {result.iterations} ROC pass
                  {result.iterations > 1 ? "es" : ""}
                </span>
              </div>
            </div>
            <div className="hero-orders">μ = (e − exceptional) / (e + voids)</div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="Grouping efficacy"
              value={formatNumber(result.grouping_efficacy)}
              detail="μ = 1 is a perfect block diagonal"
            />
            <MetricCard
              label="Exceptional elements"
              value={result.exceptional}
              detail="1s outside every cell — intercell travel"
            />
            <MetricCard
              label="Voids"
              value={result.voids}
              detail="0s inside a cell — idle pairings"
            />
          </div>
        )}
        {result && (
          <div className="row">
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="Original matrix"
                data={[
                  incidenceTrace(
                    result.matrix,
                    machineNames,
                    partNames,
                  ),
                ]}
                layout={HEATMAP_LAYOUT}
                height={110 + 36 * result.matrix.length}
              />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="After ROC, grouped into cells — red = exceptional, gray = void"
                data={[
                  clusteredTrace(
                    reorder(result.matrix, result.row_order, displayCols),
                    result.row_order.map((i) => machineNames[i]),
                    displayCols.map((j) => partNames[j]),
                    result.row_order.map((i) => result.machine_cells[i]),
                    displayCols.map((j) => result.part_cells[j]),
                  ),
                ]}
                layout={HEATMAP_LAYOUT}
                height={110 + 36 * result.matrix.length}
              />
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            {cells.map((cell, c) => (
              <MetricCard
                key={c}
                label={`Cell ${c + 1}`}
                value={cell.machines}
                detail={`parts: ${cell.parts}`}
              />
            ))}
          </div>
        )}
        {result && <RocDrawer steps={result.steps} />}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Route and module flip**

In `web/src/App.tsx`, add the import (alphabetical, before `ComingSoon`):

```tsx
import CellularPage from "./pages/cellular/CellularPage";
```

and add this route directly below the `/` route:

```tsx
<Route path="/cellular" element={<CellularPage />} />
```

In `web/src/modules.ts`, replace the cellular entry with:

```ts
  { path: "/cellular", name: "Cellular", decision: "Which machines belong together in cells?", icon: Grid3X3, ready: true, exampleSearch: "?m=10010;01101;10010;01100" },
```

- [ ] **Step 3: Verify in the browser**

Run `npm run build` (in `web/`), then uvicorn (repo root):
`.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`, open
`http://localhost:8000/cellular?m=10010;01101;10010;01100` and check:
hero shows **2 cells**, grouping efficacy **0.9**, converged in **2 ROC
passes**; metric cards show 0 exceptional / 1 void; the left heatmap is the
scrambled original, the right one shows two teal blocks with one gray void
at M4×P5; cell cards read Cell 1 = M1, M3 / parts P1, P4 and Cell 2 = M2,
M4 / parts P2, P3, P5; toggling a cell updates everything after the
debounce; "− machine" down to an all-empty row shows core's inline message;
the drawer narrates "Pass 1 — … M1 = 18, M3 = 18, M2 = 13, M4 = 12";
loading "Scrambled blocks (6×8)" gives efficacy 1 with three clean blocks;
the Home example link works. Stop the server.

- [ ] **Step 4: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src
git commit -m "feat: add cellular page with before-after matrices and cells"
```

---

### Task 7: Playwright smoke, docs, final verification

**Files:**
- Create: `web/e2e/cellular.spec.ts`
- Modify: `README.md`

- [ ] **Step 1: Write the smoke spec**

Create `web/e2e/cellular.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

// Hand-traced ground truth (tests/test_cells.py): ROC orders M1,M3,M2,M4 /
// P1,P4,P2,P3,P5; 2 cells; e = 9, 0 exceptional, 1 void -> efficacy 0.9.
test("cellular finds two cells on the shared-link example", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await expect(page.getByText("2 cells")).toBeVisible();
  await expect(page.getByText("grouping efficacy 0.9")).toBeVisible();
});

test("cell composition matches the hand trace", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await expect(page.getByText("M1, M3")).toBeVisible(); // Cell 1 machines
  await expect(page.getByText("parts: P2, P3, P5")).toBeVisible(); // Cell 2
});

test("teaching drawer narrates the binary-value sort", async ({ page }) => {
  await page.goto("/cellular?m=10010;01101;10010;01100");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  // pass 1: M1 = 18, M3 = 18, M2 = 13, M4 = 12
  await expect(page.getByText(/M1 = 18, M3 = 18/)).toBeVisible();
});
```

- [ ] **Step 2: Run the smoke tests**

Run (in `web/`): `npm run e2e`
Expected: 13 passed (3 new + 10 existing).

- [ ] **Step 3: Update the README roadmap line**

In `README.md`, replace

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅, Line Balancing ✅, Process Analysis ✅ — remaining modules rolling out one by one
```

with

```markdown
- React redesign: Lot Sizing ✅, Scheduling ✅, Line Balancing ✅, Process Analysis ✅, Cellular ✅ — Productivity is the last module to go
```

- [ ] **Step 4: Full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -q` — 149 passed.
Run (in `web/`): `npm test` (28 passed), `npm run build` (clean), `npm run e2e` (13 passed).

- [ ] **Step 5: Commit**

```bash
git add web/e2e README.md
git commit -m "test: add playwright smoke for cellular; update roadmap"
```

---

## Self-review notes

- **Spec coverage** (`2026-06-11-cellular-design.md`): ROC with stable-sort tie-break unchanged in core ✓; cell formation via exact consecutive enumeration + grouping efficacy surfaced in hero/metrics ✓ (Task 6); before/after matrix heatmaps incl. exceptional/void coloring ported from `app/cell_charts.py` ✓ (Tasks 4, 6); cell composition ✓; validation messages (empty/ragged/non-binary/zero rows, >16 machines) flow as inline 422s ✓ (Task 2); both hand-traced examples used as ground truth in tests ✓ (Tasks 1, 2, 4, 7).
- **Type consistency:** `SolveResponse` (API) ↔ `CellularResponse` (TS) fields match incl. the echoed `matrix` ✓; `CellularStep` TS fields match the core step dicts (`values`/`order`/`changed`, `machine_cells`/`part_cells`/`n_cells`, `total_ones`/`exceptional`/`voids`/`grouping_efficacy`) ✓; chart helper signatures identical in tests (Task 4) and page (Task 6) ✓.
- **Conventions:** no solver behavior change — the `steps` parameter only records what the existing loop already computes (existing `test_roc.py` traces still pass untouched); narration assembly lives in core (`solve_cells`), keeping the router ~3 lines like other modules.
- **Known limitations:** machines/parts are auto-named M1../P1.. (no custom names — keeps the URL state a compact binary string `m=10010;…`); matrices past 16 machines are rejected rather than shown ROC-only (the Streamlit page's fallback), acceptable at course-problem sizes and consistent with scheduling's exact-optimizer cap.
