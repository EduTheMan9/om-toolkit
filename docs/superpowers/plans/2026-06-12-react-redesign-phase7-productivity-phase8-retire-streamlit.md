# React Redesign Phase 7 (Productivity) + Phase 8 (Retire Streamlit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the last module (Productivity metrics: single-factor calculator + two-period multifactor comparison with a teaching drawer) in the React app, then retire the legacy Streamlit `app/` now that all six modules have parity.

**Architecture:** `core/productivity` has the three validated primitives; it gains `compare_periods()` (in a new `compare.py`), which composes them into the two-period comparison the UI needs — multifactor per period, per-factor single-factor ratios (None when a factor has zero cost in either period, matching the Streamlit page's "—"), plus narration steps. A thin `api/routers/productivity.py` exposes `POST /api/productivity/compare` (the single-factor calculator is pure display math, `output ÷ input`, done client-side per the original spec's "display logic lives in the page"). The frontend gains a `/productivity` page with two mode pills (Two-period comparison / Single-factor) copying the ProcessAnalysisPage pattern, a per-factor change bar chart ported from `app/productivity_charts.py`, and a `MultifactorDrawer`. Phase 8 then deletes `app/`, drops streamlit/plotly/pandas from `requirements.txt` (verified: only `app/` imports them), and updates README/CLAUDE.md/Home.tsx.

**Tech Stack:** Python 3.11+, FastAPI, pytest; React 18 + TypeScript, Plotly, Vitest, Playwright. No new dependencies.

**Reference — hand-traced example (extends `tests/test_productivity.py`'s bakery numbers):**

Output $5,000 → $6,000; costs Labor 1500→1600, Materials 1000→1150, Overhead 500→500.
- Multifactor: 5000/3000 = **5/3 ≈ 1.67**; 6000/3250 = **24/13 ≈ 1.85**; change 7/65 ≈ **+10.8%**.
- Labor: 5000/1500 = 10/3 ≈ 3.33 → 6000/1600 = 3.75 → **+12.5%**.
- Materials: 5 → 6000/1150 ≈ 5.22 → **+4.3%**. Overhead: 10 → 12 → **+20%**.

---

### Task 1: core compare_periods with narration steps

**Files:**
- Create: `core/productivity/compare.py`
- Modify: `core/productivity/__init__.py`
- Test: `tests/test_productivity.py` (append)

Step schema:
- `{"kind": "totals", "period": "previous" | "current", "output": 5000.0, "total": 3000.0, "mfp": 1.6667}`
- `{"kind": "change", "previous": 1.6667, "current": 1.8462, "change": 0.1077}`
- `{"kind": "factor", "name": "Labor", "previous": 3.3333, "current": 3.75, "change": 0.125}` — one per factor, in input order; all three values None when the factor has zero cost in either period.

- [ ] **Step 1: failing tests** — append to `tests/test_productivity.py` (add `compare_periods` import from `core.productivity.compare`):

```python
BAKERY_INPUTS = [
    ("Labor", 1500.0, 1600.0),
    ("Materials", 1000.0, 1150.0),
    ("Overhead", 500.0, 500.0),
]


def test_compare_periods_worked_example():
    result = compare_periods(5000.0, 6000.0, BAKERY_INPUTS)
    assert result["multifactor"]["previous"] == pytest.approx(5 / 3)
    assert result["multifactor"]["current"] == pytest.approx(24 / 13)
    assert result["multifactor"]["change"] == pytest.approx(7 / 65)
    labor = result["factors"][0]
    assert labor["name"] == "Labor"
    assert labor["previous"] == pytest.approx(10 / 3)
    assert labor["current"] == pytest.approx(3.75)
    assert labor["change"] == pytest.approx(0.125)
    assert [s["kind"] for s in result["steps"]] == [
        "totals", "totals", "change", "factor", "factor", "factor",
    ]
    assert result["steps"][0] == {
        "kind": "totals", "period": "previous", "output": 5000.0,
        "total": pytest.approx(3000.0), "mfp": pytest.approx(5 / 3),
    }


def test_compare_periods_zero_cost_factor_has_no_ratio():
    result = compare_periods(5000.0, 6000.0, [("Labor", 1500.0, 1600.0), ("Robot", 0.0, 2000.0)])
    robot = result["factors"][1]
    assert robot == {"name": "Robot", "previous": None, "current": None, "change": None}


def test_compare_periods_rejects_duplicate_names():
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        compare_periods(5000.0, 6000.0, [("Labor", 1.0, 1.0), ("Labor", 2.0, 2.0)])
```

- [ ] **Step 2: run** `pytest tests/test_productivity.py -q` → FAIL (ImportError).
- [ ] **Step 3: implement** `core/productivity/compare.py`:

```python
"""Two-period productivity comparison: the display-ready composition of the
three primitives. Lives in core so the API router stays thin and the
narration steps are emitted next to the math they explain."""
from .metrics import multifactor_productivity, productivity_change, single_factor_productivity


def compare_periods(
    previous_output: float,
    current_output: float,
    inputs: list[tuple[str, float, float]],
) -> dict:
    """inputs = (name, previous_cost, current_cost) per factor, all in money.
    A factor with zero cost in either period has no defined ratio or change."""
    names = [name for name, _, _ in inputs]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate input names - each factor must appear once.")

    previous_costs = {name: prev for name, prev, _ in inputs}
    current_costs = {name: cur for name, _, cur in inputs}
    previous_mfp = multifactor_productivity(previous_output, previous_costs)
    current_mfp = multifactor_productivity(current_output, current_costs)
    change = productivity_change(previous_mfp, current_mfp)

    steps: list[dict] = [
        {
            "kind": "totals", "period": "previous", "output": previous_output,
            "total": sum(previous_costs.values()), "mfp": previous_mfp,
        },
        {
            "kind": "totals", "period": "current", "output": current_output,
            "total": sum(current_costs.values()), "mfp": current_mfp,
        },
        {"kind": "change", "previous": previous_mfp, "current": current_mfp, "change": change},
    ]
    factors: list[dict] = []
    for name, prev_cost, cur_cost in inputs:
        if prev_cost > 0 and cur_cost > 0:
            prev_p = single_factor_productivity(previous_output, prev_cost)
            cur_p = single_factor_productivity(current_output, cur_cost)
            factor = {
                "name": name, "previous": prev_p, "current": cur_p,
                "change": productivity_change(prev_p, cur_p),
            }
        else:
            factor = {"name": name, "previous": None, "current": None, "change": None}
        factors.append(factor)
        steps.append({"kind": "factor", **factor})

    return {
        "multifactor": {"previous": previous_mfp, "current": current_mfp, "change": change},
        "factors": factors,
        "steps": steps,
    }
```

`__init__.py`: export `compare_periods` alongside the three primitives.

- [ ] **Step 4: full suite** → 153 passed. **Step 5: commit** `feat: add two-period productivity comparison in core`.

---

### Task 2: /api/productivity/compare endpoint

**Files:**
- Create: `api/routers/productivity.py`
- Modify: `api/main.py`
- Test: `tests/test_api_productivity.py`

- [ ] **Step 1: failing tests** — create `tests/test_api_productivity.py`:

```python
"""Productivity API, validated against the bakery example in
tests/test_productivity.py: 5000/3000 -> 6000/3250, change +7/65."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

REQUEST = {
    "previous_output": 5000,
    "current_output": 6000,
    "inputs": [
        {"name": "Labor", "previous": 1500, "current": 1600},
        {"name": "Materials", "previous": 1000, "current": 1150},
        {"name": "Overhead", "previous": 500, "current": 500},
    ],
}


def test_compare_endpoint_worked_example():
    response = client.post("/api/productivity/compare", json=REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["multifactor"]["previous"] == pytest.approx(5 / 3)
    assert body["multifactor"]["current"] == pytest.approx(24 / 13)
    assert body["multifactor"]["change"] == pytest.approx(7 / 65)
    assert body["factors"][0]["change"] == pytest.approx(0.125)
    assert body["steps"][0]["kind"] == "totals"
    assert body["steps"][2]["kind"] == "change"


def test_compare_zero_cost_factor_returns_nulls():
    request = {
        "previous_output": 5000, "current_output": 6000,
        "inputs": [{"name": "Labor", "previous": 1500, "current": 1600},
                   {"name": "Robot", "previous": 0, "current": 2000}],
    }
    body = client.post("/api/productivity/compare", json=request).json()
    assert body["factors"][1] == {"name": "Robot", "previous": None, "current": None, "change": None}


def test_compare_rejects_empty_inputs_with_core_message():
    request = {"previous_output": 5000, "current_output": 6000, "inputs": []}
    response = client.post("/api/productivity/compare", json=request)
    assert response.status_code == 422
    assert "at least one" in response.json()["detail"]


def test_compare_rejects_duplicate_names():
    request = {
        "previous_output": 5000, "current_output": 6000,
        "inputs": [{"name": "Labor", "previous": 1, "current": 1},
                   {"name": "Labor", "previous": 2, "current": 2}],
    }
    response = client.post("/api/productivity/compare", json=request)
    assert response.status_code == 422
    assert "uplicate" in response.json()["detail"]
```

- [ ] **Step 2: run** → FAIL 404. **Step 3: implement** `api/routers/productivity.py`:

```python
"""Productivity endpoint: two-period multifactor comparison.

The single-factor calculator (output / input in arbitrary units) is display
math and lives client-side, per the module spec.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.productivity import compare_periods

router = APIRouter(prefix="/api/productivity", tags=["productivity"])


class InputRow(BaseModel):
    name: str
    previous: float
    current: float


class CompareRequest(BaseModel):
    previous_output: float
    current_output: float
    inputs: list[InputRow]


class MultifactorOut(BaseModel):
    previous: float
    current: float
    change: float


class FactorOut(BaseModel):
    name: str
    previous: float | None
    current: float | None
    change: float | None


class CompareResponse(BaseModel):
    multifactor: MultifactorOut
    factors: list[FactorOut]
    steps: list[dict]


@router.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest) -> CompareResponse:
    # compare_periods validates (core's ValueError message -> 422)
    return CompareResponse(**compare_periods(
        req.previous_output,
        req.current_output,
        [(r.name, r.previous, r.current) for r in req.inputs],
    ))
```

`api/main.py`: add `productivity` to the routers import and `app.include_router(productivity.router)` (alphabetical, after `process_analysis`).

- [ ] **Step 4: full suite** → 157 passed. **Step 5: commit** `feat: add productivity compare endpoint`.

---

### Task 3: frontend lib — API types and productivity URL state

**Files:**
- Modify: `web/src/lib/api.ts`, `web/src/lib/urlState.ts`
- Test: `web/src/lib/urlState.test.ts` (append)

- [ ] **Step 1: failing tests** (merge `decodeProductivity`, `encodeProductivity` into the import):

```ts
describe("productivity URL state", () => {
  it("round-trips outputs and input costs", () => {
    const inputs = {
      outputPrevious: 5000,
      outputCurrent: 6000,
      inputs: [
        { name: "Labor", previous: 1500, current: 1600 },
        { name: "Overhead", previous: 500, current: 500 },
      ],
    };
    expect(decodeProductivity("?" + encodeProductivity(inputs))).toEqual(inputs);
  });

  it("returns null for malformed strings", () => {
    expect(decodeProductivity("")).toBeNull();
    expect(decodeProductivity("?i=Labor,x,1&o=5,6")).toBeNull();
    expect(decodeProductivity("?i=Labor,1,2&o=5")).toBeNull();
  });
});
```

- [ ] **Step 2: run** → FAIL. **Step 3: implement** — append to `api.ts`:

```ts
export interface ProductivityFactor {
  name: string;
  previous: number | null;
  current: number | null;
  change: number | null;
}

export interface ProductivityStep {
  kind: "totals" | "change" | "factor";
  period?: "previous" | "current";
  output?: number;
  total?: number;
  mfp?: number;
  previous?: number | null;
  current?: number | null;
  change?: number | null;
  name?: string;
}

export interface ProductivityResponse {
  multifactor: { previous: number; current: number; change: number };
  factors: ProductivityFactor[];
  steps: ProductivityStep[];
}
```

append to `urlState.ts`:

```ts
export interface ProductivityInputRow {
  name: string;
  previous: number;
  current: number;
}

export interface ProductivityInputs {
  outputPrevious: number;
  outputCurrent: number;
  inputs: ProductivityInputRow[];
}

// Inputs encode as i=name,prev,cur;... plus o=<prev>,<cur> output values.
// Names containing "," or ";" break the format; decode returns null and the
// page falls back to a preset.
export function encodeProductivity(inputs: ProductivityInputs): string {
  const params = new URLSearchParams();
  params.set("o", `${inputs.outputPrevious},${inputs.outputCurrent}`);
  params.set(
    "i",
    inputs.inputs.map((x) => [x.name, x.previous, x.current].join(",")).join(";"),
  );
  return params.toString();
}

export function decodeProductivity(search: string): ProductivityInputs | null {
  const params = new URLSearchParams(search);
  const o = params.get("o");
  const raw = params.get("i");
  if (!o || !raw) return null;
  const outputs = o.split(",").map(Number);
  if (outputs.length !== 2 || outputs.some(Number.isNaN)) return null;
  const inputs: ProductivityInputRow[] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const previous = Number(fields[1]);
    const current = Number(fields[2]);
    if (Number.isNaN(previous) || Number.isNaN(current)) return null;
    inputs.push({ name: fields[0], previous, current });
  }
  return { outputPrevious: outputs[0], outputCurrent: outputs[1], inputs };
}
```

- [ ] **Step 4: run** → 30 vitest passed, build clean. **Step 5: commit** `feat: add productivity api types and url state`.

---

### Task 4: change bar chart trace

**Files:**
- Create: `web/src/pages/productivity/charts.ts`
- Test: `web/src/pages/productivity/charts.test.ts`

- [ ] **Step 1: failing test**:

```ts
import { describe, expect, it } from "vitest";
import { changeTrace, formatChange } from "./charts";

describe("changeTrace", () => {
  it("shows percent changes with negatives in red", () => {
    const trace = changeTrace(["Labor", "Machines"], [0.125, -0.046]) as any;
    expect(trace.x[0]).toBeCloseTo(12.5);
    expect(trace.text).toEqual(["+12.5%", "-4.6%"]);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("formatChange", () => {
  it("formats a fraction as a signed percentage", () => {
    expect(formatChange(7 / 65)).toBe("+10.8%");
    expect(formatChange(-0.2)).toBe("-20.0%");
  });
});
```

- [ ] **Step 2: run** → FAIL. **Step 3: implement** `charts.ts`:

```ts
import type { Data } from "plotly.js";

/** +0.108 -> "+10.8%" — productivity change is a fraction in core/API. */
export const formatChange = (change: number) =>
  `${change >= 0 ? "+" : ""}${(change * 100).toFixed(1)}%`;

/** Change per factor: bars left of the zero line mean the factor got LESS
 * productive. The zero line is a layout shape added by the view. */
export function changeTrace(names: string[], changes: number[]): Data {
  return {
    type: "bar",
    orientation: "h",
    y: names,
    x: changes.map((c) => c * 100),
    marker: { color: changes.map((c) => (c < 0 ? "#dc2626" : "#0d9488")) },
    text: changes.map(formatChange),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}
```

- [ ] **Step 4: run** → 32 passed. **Step 5: commit** `feat: add productivity change trace`.

---

### Task 5: drawer, presets, page, route, module flip

**Files:**
- Create: `web/src/pages/productivity/presets.ts`, `web/src/pages/productivity/MultifactorDrawer.tsx`, `web/src/pages/productivity/ProductivityPage.tsx`
- Modify: `web/src/App.tsx`, `web/src/modules.ts`

- [ ] **Step 1: presets** (ported from `PRODUCTIVITY_EXAMPLES` in `app/examples.py`):

```ts
import type { ProductivityInputs } from "../../lib/urlState";

export const PRODUCTIVITY_PRESETS: Record<string, ProductivityInputs> = {
  // Last period is the worked example from the test suite (multifactor 5/3)
  "Bakery, two weeks": {
    outputPrevious: 5000,
    outputCurrent: 6000,
    inputs: [
      { name: "Labor", previous: 1500, current: 1600 },
      { name: "Materials", previous: 1000, current: 1150 },
      { name: "Overhead", previous: 500, current: 500 },
    ],
  },
  // Labor productivity explodes but MULTIFACTOR falls - the robot costs
  // more than the labor it saved
  "Automation trade-off": {
    outputPrevious: 8000,
    outputCurrent: 8200,
    inputs: [
      { name: "Labor", previous: 2000, current: 800 },
      { name: "Machines", previous: 500, current: 2200 },
      { name: "Materials", previous: 2000, current: 2050 },
    ],
  },
};
```

- [ ] **Step 2: MultifactorDrawer** — describe() over the three step kinds: totals ("Last period: output $5,000 ÷ total input cost $3,000 = 1.67"), change (demand-style good/bad span on sign), factor ("Labor alone: 3.33 → 3.75 (+12.5%) — one factor can look great while the others absorb the load"); zero-cost factors narrate "has zero cost in a period — no defined ratio". Full code in the page commit.

- [ ] **Step 3: ProductivityPage** — mode pills "Two-period comparison" / "Single-factor calculator" (ProcessAnalysisPage pattern; comparison inputs in the URL, single-factor session-local). Comparison view: `JobsTable` (`idLabel="input"`, columns `["last $", "this $"]`) + two NumberFields for output values + presets select; results: hero (multifactor change, formatChange, detail "1.67 → 1.85 $ out per $ in"), three MetricCards (last, this, change), factor table in a card (name / last / this / change, "—" for nulls), PlotCard with changeTrace (factors + "Multifactor (all inputs)" row, zero line shape), MultifactorDrawer. Single-factor view: output + input NumberFields, result MetricCard `output / input` with an "input must be positive" inline guard — client-side display math per the spec.

- [ ] **Step 4: route + flip** — App.tsx import + `<Route path="/productivity" element={<ProductivityPage />} />`; modules.ts entry: `ready: true, exampleSearch: "?o=5000,6000&i=Labor,1500,1600;Materials,1000,1150;Overhead,500,500"`.

- [ ] **Step 5: verify in browser** — hero +10.8%, cards 1.67/1.85, Labor row +12.5%, Materials +4.3%, Overhead +20%; "Automation trade-off" preset shows Labor hugely positive but multifactor negative (red); duplicate input name shows core's message; single-factor mode 500/200 = 2.5; drawer narrates the totals; Home example link works.

- [ ] **Step 6:** `npm run build` clean → commit `feat: add productivity page with two-period comparison`.

---

### Task 6: Playwright smoke for productivity

**Files:**
- Create: `web/e2e/productivity.spec.ts`

```ts
import { expect, test } from "@playwright/test";

// Hand-traced bakery example (tests/test_productivity.py): multifactor
// 5000/3000 = 1.67 -> 6000/3250 = 1.85, change +10.8%; Labor +12.5%.
test("productivity compares two periods on the shared-link example", async ({ page }) => {
  await page.goto("/productivity?o=5000,6000&i=Labor,1500,1600;Materials,1000,1150;Overhead,500,500");
  await expect(page.getByText("+10.8%").first()).toBeVisible();
  await expect(page.getByText("1.67").first()).toBeVisible();
  await expect(page.getByText("1.85").first()).toBeVisible();
});

test("teaching drawer narrates the multifactor totals", async ({ page }) => {
  await page.goto("/productivity?o=5000,6000&i=Labor,1500,1600;Materials,1000,1150;Overhead,500,500");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/5,000.*3,000/)).toBeVisible();
});

test("single-factor calculator divides output by input", async ({ page }) => {
  await page.goto("/productivity?mode=single");
  await expect(page.getByText("2.5", { exact: true })).toBeVisible(); // 500/200
});
```

- [ ] Run `npm run e2e` → 16 passed. Commit `test: add playwright smoke for productivity`.

---

### Task 7: Phase 8 — retire the Streamlit app

**Files:**
- Delete: `app/` (entire directory)
- Modify: `requirements.txt`, `README.md`, `CLAUDE.md`, `web/src/pages/Home.tsx`

- [ ] **Step 1:** `git rm -r app` (and clear `app/__pycache__` leftovers).
- [ ] **Step 2:** `requirements.txt` → keep only `pytest`, `fastapi`, `uvicorn[standard]`, `httpx` (streamlit/plotly/pandas were only imported by `app/` — verified by grep over core/api/tests).
- [ ] **Step 3:** README — Run locally: single app (pip install, npm build, uvicorn + the dev-mode note); Project structure: drop the `app/` line; Roadmap: all six modules in the React app ✅, deploy remaining. Status table header stays.
- [ ] **Step 4:** CLAUDE.md — Architecture: drop the `app/` bullet; Commands: replace `streamlit run app/Home.py` with the uvicorn + `npm run dev` pair; Roadmap: mark modules 4–6 ✅ done.
- [ ] **Step 5:** Home.tsx — the "Coming soon — available in the classic app" string never renders now (every module is `ready`), but fix the dangling reference: "Coming soon".
- [ ] **Step 6:** grep repo for remaining `streamlit` references (expect none outside docs/ history and the kickoff prompt, which stay as project history).
- [ ] **Step 7:** full verification — pytest (157), vitest (32), build, e2e (16).
- [ ] **Step 8:** commit `chore!: retire legacy streamlit app, all modules live in react` + push.

---

## Self-review notes

- **Spec coverage:** `/api/productivity/compare` is the endpoint named in the redesign spec ✓; single-factor calculator client-side follows the productivity spec's "display logic lives in the page" ✓; comparison table, multifactor metrics, and the per-factor change chart port the Streamlit page 1:1 ✓; both presets ported ✓; zero-cost "—" convention preserved as nulls ✓.
- **Type consistency:** `FactorOut`/`ProductivityFactor` and step dicts match across core/API/TS ✓; `formatChange`/`changeTrace` used identically in tests and page ✓.
- **Phase 8 safety:** nothing in core/api/tests imports app/ or its dependencies (grepped); Playwright config never touches Streamlit; docs/specs keep their historical references intentionally.
