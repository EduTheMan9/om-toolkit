# React Redesign Phase 1–2: Scaffold + Lot Sizing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the FastAPI + React (Clean Lab × Workbench) app and ship the Lot Sizing module end-to-end, including the first self-narrating teaching drawer.

**Architecture:** FastAPI (`api/`) wraps the untouched `core/` solvers as a JSON API and serves the built React bundle; React + TS + Vite (`web/`) renders the workbench UI. `core/` gains one new function: a Silver–Meal variant that records its decisions as structured steps. The legacy Streamlit `app/` keeps working throughout.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx (tests); React 18, TypeScript, Vite, react-router-dom, react-plotly.js + plotly.js-dist-min, lucide-react, @fontsource fonts, Vitest, @playwright/test.

**Context for the engineer:** This repo is an Operations Management teaching toolkit. All solver math lives in `core/` as pure Python with hand-traced tests in `tests/` — never edit solver behavior. The spec is `docs/superpowers/specs/2026-06-11-react-redesign-design.md`; read it first. Run Python via the project venv: `.\.venv\Scripts\python.exe`. The repo root is the pytest rootdir, so `import api` / `import core` work in tests.

**Reference — hand-traced Lot Sizing example used everywhere below:**
demands `[50, 60, 90, 70, 30, 100]`, S=150, h=1 → lot-for-lot $900, Silver–Meal $640 (orders `[110,0,190,0,0,100]`), Wagner–Whitin $640 (same plan, provably optimal). EOQ: D=1200, S=100, H=6 → Q\*=200, total $1,200.

---

### Task 1: FastAPI skeleton with health endpoint

**Files:**
- Modify: `requirements.txt`
- Create: `api/__init__.py`, `api/main.py`, `api/routers/__init__.py`
- Test: `tests/test_api_main.py`

- [ ] **Step 1: Add backend dependencies and install**

Append to `requirements.txt`:

```
fastapi
uvicorn[standard]
httpx
```

Run: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
Expected: installs succeed.

- [ ] **Step 2: Write the failing test**

Create `tests/test_api_main.py`:

```python
"""API skeleton: health check and ValueError -> 422 mapping."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_main.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'api'`.

- [ ] **Step 4: Write minimal implementation**

Create empty `api/__init__.py` and `api/routers/__init__.py`.

Create `api/main.py`:

```python
"""OM Toolkit API: thin JSON layer over core/, plus static hosting of web/dist.

All domain validation lives in core/'s validate_* functions; they raise
ValueError with a human-readable message, which we surface as HTTP 422 so
the frontend can show it inline next to the offending input.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="OM Toolkit API")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_main.py -q`
Expected: 1 passed. Also run the full suite (`.\.venv\Scripts\python.exe -m pytest -q`) — 117 passed, none broken.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt api tests/test_api_main.py
git commit -m "feat: add FastAPI skeleton with health endpoint"
```

---

### Task 2: EOQ endpoint

**Files:**
- Create: `api/routers/lot_sizing.py`
- Modify: `api/main.py`
- Test: `tests/test_api_lot_sizing.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_lot_sizing.py`:

```python
"""Lot-sizing API endpoints, validated against the hand-traced examples
(see tests/test_eoq.py and tests/test_dynamic_lot_sizing.py)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_eoq_endpoint_worked_example():
    response = client.post(
        "/api/lot-sizing/eoq",
        json={"demand": 1200.0, "ordering_cost": 100.0, "holding_cost": 6.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == pytest.approx(200.0)
    assert body["total_cost"] == pytest.approx(1200.0)
    assert body["ordering_cost_total"] == pytest.approx(body["holding_cost_total"])
    # cost curve for the chart: parallel arrays, same length, total = sum
    curve = body["curve"]
    assert len(curve["q"]) == len(curve["total"]) == 200
    assert curve["total"][50] == pytest.approx(
        curve["ordering"][50] + curve["holding"][50]
    )


def test_eoq_endpoint_rejects_bad_input_with_core_message():
    response = client.post(
        "/api/lot-sizing/eoq",
        json={"demand": 0.0, "ordering_cost": 100.0, "holding_cost": 6.0},
    )
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_lot_sizing.py -q`
Expected: FAIL — 404, route does not exist.

- [ ] **Step 3: Implement the router**

Create `api/routers/lot_sizing.py`:

```python
"""Lot-sizing endpoints: EOQ and dynamic lot sizing."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.lot_sizing import economic_order_quantity

router = APIRouter(prefix="/api/lot-sizing", tags=["lot-sizing"])

CURVE_POINTS = 200


class EoqRequest(BaseModel):
    demand: float
    ordering_cost: float
    holding_cost: float


class EoqCurve(BaseModel):
    q: list[float]
    ordering: list[float]
    holding: list[float]
    total: list[float]


class EoqResponse(BaseModel):
    quantity: float
    orders_per_period: float
    time_between_orders: float
    ordering_cost_total: float
    holding_cost_total: float
    total_cost: float
    curve: EoqCurve


@router.post("/eoq", response_model=EoqResponse)
def eoq(req: EoqRequest) -> EoqResponse:
    result = economic_order_quantity(req.demand, req.ordering_cost, req.holding_cost)
    # Sample TC(Q) = (D/Q)S + (Q/2)H up to 3*Q* (the interesting region; the
    # 1/Q blow-up at tiny Q is clipped by starting the range above zero).
    q_max = result.quantity * 3
    qs = [q_max * (i + 1) / CURVE_POINTS for i in range(CURVE_POINTS)]
    ordering = [(req.demand / q) * req.ordering_cost for q in qs]
    holding = [(q / 2) * req.holding_cost for q in qs]
    return EoqResponse(
        quantity=result.quantity,
        orders_per_period=result.orders_per_period,
        time_between_orders=result.time_between_orders,
        ordering_cost_total=result.ordering_cost_total,
        holding_cost_total=result.holding_cost_total,
        total_cost=result.total_cost,
        curve=EoqCurve(
            q=qs,
            ordering=ordering,
            holding=holding,
            total=[o + h for o, h in zip(ordering, holding)],
        ),
    )
```

In `api/main.py`, add after the imports:

```python
from api.routers import lot_sizing
```

and after `app = FastAPI(...)`:

```python
app.include_router(lot_sizing.router)
```

Note: `TestClient` re-raises app exceptions by default only when they are not handled; the `ValueError` handler from Task 1 converts core's errors to 422 — no try/except needed in routers.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_lot_sizing.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api_lot_sizing.py
git commit -m "feat: add EOQ endpoint with cost-curve sampling"
```

---

### Task 3: Silver–Meal step trace in core/

**Files:**
- Modify: `core/lot_sizing/dynamic.py`, `core/lot_sizing/__init__.py`
- Test: `tests/test_dynamic_lot_sizing.py` (append)

The teaching drawer replays Silver–Meal's decisions on the user's data. The
solver records its own decisions as structured dicts; `silver_meal` keeps its
exact current behavior by delegating.

Step schema (1-based periods, matching course notation):
- `{"kind": "open_lot", "lot": 1, "period": 1}` — a new lot starts.
- `{"kind": "try_extend", "lot": 1, "period": 2, "avg_current": 150.0, "avg_extended": 105.0, "decision": "extend"}` — `decision` is `"stop"` when `avg_extended >= avg_current`.
- `{"kind": "close_lot", "lot": 1, "start": 1, "end": 2, "quantity": 110.0}` — the lot is fixed.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dynamic_lot_sizing.py`:

```python
def test_silver_meal_with_steps_narrates_the_worked_example():
    """Hand trace: lot 1 avg 150 -> 105 (extend) -> 130 (stop);
    lot 2 avg 150 -> 110 -> 93.33 (extend twice) -> 145 (stop); lot 3 = p6."""
    from core.lot_sizing.dynamic import silver_meal_with_steps

    orders, steps = silver_meal_with_steps(DEMANDS, S, H)
    assert orders == silver_meal(DEMANDS, S, H)

    decisions = [s["decision"] for s in steps if s["kind"] == "try_extend"]
    assert decisions == ["extend", "stop", "extend", "extend", "stop"]

    closes = [
        (s["lot"], s["start"], s["end"], s["quantity"])
        for s in steps
        if s["kind"] == "close_lot"
    ]
    assert closes == [(1, 1, 2, 110.0), (2, 3, 5, 190.0), (3, 6, 6, 100.0)]

    first_try = next(s for s in steps if s["kind"] == "try_extend")
    assert first_try["avg_current"] == pytest.approx(150.0)
    assert first_try["avg_extended"] == pytest.approx(105.0)
    assert steps[0] == {"kind": "open_lot", "lot": 1, "period": 1}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_dynamic_lot_sizing.py -q`
Expected: FAIL — `ImportError: cannot import name 'silver_meal_with_steps'`.

- [ ] **Step 3: Implement by refactoring silver_meal**

In `core/lot_sizing/dynamic.py`, REPLACE the existing `silver_meal` function with:

```python
def silver_meal_with_steps(
    demands: list[float], setup_cost: float, holding_cost: float
) -> tuple[list[float], list[dict]]:
    """Silver-Meal that records its own decisions while it runs, so the UI
    can replay the algorithm step by step on the user's data.
    Periods in steps are 1-based to match course notation."""
    validate_inputs(demands, setup_cost, holding_cost)
    n = len(demands)
    orders = [0.0] * n
    steps: list[dict] = []
    lot = 0
    j = 0
    while j < n:
        if demands[j] == 0:  # nothing to cover; no order, no setup
            j += 1
            continue
        lot += 1
        steps.append({"kind": "open_lot", "lot": lot, "period": j + 1})
        t = j
        avg = _lot_cost(demands, j, t, setup_cost, holding_cost)  # 1 period covered
        while t + 1 < n:
            next_avg = _lot_cost(demands, j, t + 1, setup_cost, holding_cost) / (t + 2 - j)
            decision = "stop" if next_avg >= avg else "extend"
            steps.append(
                {
                    "kind": "try_extend",
                    "lot": lot,
                    "period": t + 2,
                    "avg_current": avg,
                    "avg_extended": next_avg,
                    "decision": decision,
                }
            )
            if decision == "stop":
                break
            avg = next_avg
            t += 1
        orders[j] = sum(demands[j : t + 1])
        steps.append(
            {"kind": "close_lot", "lot": lot, "start": j + 1, "end": t + 1, "quantity": orders[j]}
        )
        j = t + 1
    return orders, steps


def silver_meal(demands: list[float], setup_cost: float, holding_cost: float) -> list[float]:
    """Extend the current lot one period at a time while the average cost
    per period covered keeps falling; stop at the first increase. Myopic —
    usually near-optimal, but not guaranteed (that's Wagner-Whitin's job)."""
    orders, _ = silver_meal_with_steps(demands, setup_cost, holding_cost)
    return orders
```

In `core/lot_sizing/__init__.py`, add `silver_meal_with_steps` to the import from `.dynamic` and to `__all__` (keep both alphabetical).

- [ ] **Step 4: Run the full suite to verify everything passes**

Run: `.\.venv\Scripts\python.exe -m pytest -q`
Expected: all pass (the pre-existing `test_silver_meal_worked_example` proves the refactor preserved behavior).

- [ ] **Step 5: Commit**

```bash
git add core/lot_sizing tests/test_dynamic_lot_sizing.py
git commit -m "feat: add silver-meal step trace for the teaching drawer"
```

---

### Task 4: Dynamic lot-sizing endpoint (plans + costs + steps)

**Files:**
- Modify: `api/routers/lot_sizing.py`
- Test: `tests/test_api_lot_sizing.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_api_lot_sizing.py`:

```python
DYNAMIC_REQUEST = {
    "demands": [50.0, 60.0, 90.0, 70.0, 30.0, 100.0],
    "setup_cost": 150.0,
    "holding_cost": 1.0,
}


def test_dynamic_endpoint_worked_example():
    response = client.post("/api/lot-sizing/dynamic", json=DYNAMIC_REQUEST)
    assert response.status_code == 200
    body = response.json()
    plans = body["plans"]
    assert plans["wagner_whitin"]["total_cost"] == pytest.approx(640.0)
    assert plans["wagner_whitin"]["orders"] == [110.0, 0.0, 190.0, 0.0, 0.0, 100.0]
    assert plans["silver_meal"]["total_cost"] == pytest.approx(640.0)
    assert plans["lot_for_lot"]["total_cost"] == pytest.approx(900.0)
    assert plans["lot_for_lot"]["setups"] == 6
    # silver-meal narration is included for the teaching drawer
    kinds = {s["kind"] for s in body["steps"]}
    assert kinds == {"open_lot", "try_extend", "close_lot"}


def test_dynamic_endpoint_rejects_shortage_free_invalid_input():
    bad = dict(DYNAMIC_REQUEST, setup_cost=0.0)
    response = client.post("/api/lot-sizing/dynamic", json=bad)
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_lot_sizing.py -q`
Expected: the two new tests FAIL with 404.

- [ ] **Step 3: Implement the endpoint**

In `api/routers/lot_sizing.py`, extend the core import and add below the EOQ endpoint:

```python
from core.lot_sizing import (
    economic_order_quantity,
    evaluate_plan,
    lot_for_lot,
    silver_meal_with_steps,
    wagner_whitin,
)
```

```python
class DynamicRequest(BaseModel):
    demands: list[float]
    setup_cost: float
    holding_cost: float


class PlanResult(BaseModel):
    orders: list[float]
    setups: int
    setup_cost: float
    holding_cost: float
    total_cost: float
    ending_inventory: list[float]


class DynamicResponse(BaseModel):
    plans: dict[str, PlanResult]
    steps: list[dict]


@router.post("/dynamic", response_model=DynamicResponse)
def dynamic(req: DynamicRequest) -> DynamicResponse:
    sm_orders, sm_steps = silver_meal_with_steps(
        req.demands, req.setup_cost, req.holding_cost
    )
    plans = {
        "lot_for_lot": lot_for_lot(req.demands, req.setup_cost, req.holding_cost),
        "silver_meal": sm_orders,
        "wagner_whitin": wagner_whitin(req.demands, req.setup_cost, req.holding_cost),
    }
    return DynamicResponse(
        plans={
            name: PlanResult(
                orders=orders,
                **evaluate_plan(req.demands, orders, req.setup_cost, req.holding_cost),
            )
            for name, orders in plans.items()
        },
        steps=sm_steps,
    )
```

(`evaluate_plan` returns exactly the remaining `PlanResult` fields: `setups`, `setup_cost`, `holding_cost`, `total_cost`, `ending_inventory`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_lot_sizing.py -q`
Expected: 4 passed. Run full suite: all pass.

- [ ] **Step 5: Commit**

```bash
git add api/routers/lot_sizing.py tests/test_api_lot_sizing.py
git commit -m "feat: add dynamic lot-sizing endpoint with narration steps"
```

---

### Task 5: Vite + React scaffold with Clean Lab design tokens

**Files:**
- Create: `web/` (Vite scaffold), `web/src/styles/tokens.css`, `web/src/styles/global.css`
- Modify: `web/vite.config.ts`, `web/src/main.tsx`, `web/index.html`, `.gitignore`

- [ ] **Step 1: Verify Node and scaffold the project**

Run: `node --version` (need ≥18; if missing, stop and tell the user).
From the repo root:

```bash
npm create vite@latest web -- --template react-ts
cd web
npm install
npm install react-router-dom react-plotly.js plotly.js-dist-min lucide-react @fontsource/inter @fontsource/space-grotesk @fontsource/jetbrains-mono
npm install -D vitest @types/react-plotly.js
```

Delete the template noise: `web/src/App.css`, `web/src/index.css`, `web/src/assets/react.svg`, `web/public/vite.svg` (App.tsx and main.tsx get fully replaced in Task 6).

Append to the root `.gitignore`:

```
node_modules/
web/dist/
```

- [ ] **Step 2: Configure the dev proxy and test script**

Replace `web/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev runs two servers: Vite (5173) proxies /api to uvicorn (8000),
// so the frontend code can always fetch("/api/...") in dev and prod alike.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
```

In `web/package.json` scripts, add: `"test": "vitest run"`.

- [ ] **Step 3: Create the design tokens**

Create `web/src/styles/tokens.css`:

```css
/* Clean Lab design tokens — single source of truth for the visual identity.
   Spec: docs/superpowers/specs/2026-06-11-react-redesign-design.md */
:root {
  --bg: #fafbfc;
  --surface: #ffffff;
  --border: #e6eaee;
  --ink: #101418;
  --subtle: #5a6572;
  --muted: #8a94a0;
  --accent: #0d9488;
  --accent-bright: #2dd4bf;
  --accent-soft: #f0fdfa;
  --accent-border: #99f6e4;
  --danger: #dc2626;
  --rail-bg: #101418;
  --radius: 12px;
  --shadow: 0 1px 2px rgba(16, 20, 24, 0.04);
  --font-display: "Space Grotesk", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
}
```

Create `web/src/styles/global.css`:

```css
* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 14px;
}

h1, h2, h3 { font-family: var(--font-display); margin: 0; }

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--muted);
  font-weight: 600;
}

.subtitle { color: var(--subtle); font-size: 13px; }

button {
  font-family: var(--font-body);
  cursor: pointer;
}

input, select {
  font-family: var(--font-mono);
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px 10px;
  background: var(--surface);
  color: var(--ink);
  width: 100%;
}

input:focus, select:focus {
  outline: 1.5px solid var(--accent);
  border-color: var(--accent);
}

input.invalid { outline: 1.5px solid var(--danger); border-color: var(--danger); }

.error-text { color: var(--danger); font-size: 12px; }
```

- [ ] **Step 4: Wire fonts and styles in the entrypoint**

Replace `web/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/space-grotesk/500.css";
import "@fontsource/space-grotesk/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/600.css";
import "./styles/tokens.css";
import "./styles/global.css";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
```

In `web/index.html`, set `<title>OM Toolkit</title>` and remove the vite.svg icon link.

Temporarily replace `web/src/App.tsx` so the build compiles (Task 6 replaces it):

```tsx
export default function App() {
  return <div>OM Toolkit</div>;
}
```

- [ ] **Step 5: Verify the build**

Run (in `web/`): `npm run build`
Expected: `vite build` completes with no TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add .gitignore web
git commit -m "feat: scaffold React frontend with Clean Lab design tokens"
```

---

### Task 6: App shell — icon rail, routes, placeholder pages

**Files:**
- Create: `web/src/modules.ts`, `web/src/components/Rail.tsx`, `web/src/components/Rail.css`, `web/src/pages/Home.tsx`, `web/src/pages/Home.css`, `web/src/pages/ComingSoon.tsx`
- Modify: `web/src/App.tsx`

- [ ] **Step 1: Create the module registry**

Create `web/src/modules.ts`:

```ts
import { Calendar, Grid3X3, Package, Scale, Search, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface ModuleDef {
  path: string;
  name: string;
  decision: string; // the question this module answers, in plain language
  icon: LucideIcon;
  ready: boolean; // false = still only in the legacy Streamlit app
  exampleSearch?: string; // query string that loads a preset
}

export const MODULES: ModuleDef[] = [
  { path: "/line-balancing", name: "Line Balancing", decision: "How do I split assembly work into balanced stations?", icon: Scale, ready: false },
  { path: "/process-analysis", name: "Process Analysis", decision: "Where is my bottleneck, and what is it costing me?", icon: Search, ready: false },
  { path: "/scheduling", name: "Scheduling", decision: "What order should I run these jobs in?", icon: Calendar, ready: false },
  { path: "/lot-sizing", name: "Lot Sizing", decision: "How much should I order, and when?", icon: Package, ready: true, exampleSearch: "?d=50,60,90,70,30,100&s=150&h=1" },
  { path: "/cellular", name: "Cellular", decision: "Which machines belong together in cells?", icon: Grid3X3, ready: false },
  { path: "/productivity", name: "Productivity", decision: "Did we actually get more productive?", icon: TrendingUp, ready: false },
];
```

- [ ] **Step 2: Create the rail**

Create `web/src/components/Rail.css`:

```css
.rail {
  width: 60px;
  min-height: 100vh;
  background: var(--rail-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 0;
  gap: 6px;
  flex-shrink: 0;
}

.rail-logo { color: var(--accent-bright); margin-bottom: 14px; display: flex; }

.rail-item {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  transition: background 0.15s, color 0.15s;
}

.rail-item:hover { color: #fff; background: #1f2937; }
.rail-item.active { background: var(--accent); color: #fff; }
```

Create `web/src/components/Rail.tsx`:

```tsx
import { Hexagon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { MODULES } from "../modules";
import "./Rail.css";

export function Rail() {
  return (
    <nav className="rail">
      <NavLink to="/" className="rail-logo" title="Home" aria-label="Home">
        <Hexagon size={22} />
      </NavLink>
      {MODULES.map((m) => (
        <NavLink
          key={m.path}
          to={m.path}
          title={m.name}
          aria-label={m.name}
          className={({ isActive }) => `rail-item${isActive ? " active" : ""}`}
        >
          <m.icon size={19} />
        </NavLink>
      ))}
    </nav>
  );
}
```

- [ ] **Step 3: Create Home and ComingSoon pages**

Create `web/src/pages/Home.css`:

```css
.home { padding: 48px 56px; max-width: 1000px; }
.home h1 { font-size: 30px; font-weight: 700; }
.home .tagline { margin: 8px 0 32px; }

.home-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.module-card { padding: 18px; display: flex; flex-direction: column; gap: 8px; }
.module-card h3 { font-size: 16px; display: flex; align-items: center; gap: 8px; }
.module-card .decision { color: var(--subtle); font-size: 13px; flex: 1; }
.module-card .actions { display: flex; gap: 10px; align-items: center; }

.module-card a.open {
  background: var(--accent);
  color: #fff;
  border-radius: 8px;
  padding: 6px 14px;
  font-weight: 600;
  font-size: 12px;
  text-decoration: none;
}

.module-card a.example { color: var(--accent); font-size: 12px; text-decoration: none; }
.module-card .soon { color: var(--muted); font-size: 12px; }
```

Create `web/src/pages/Home.tsx`:

```tsx
import { Link } from "react-router-dom";
import { MODULES } from "../modules";
import "./Home.css";

export default function Home() {
  return (
    <div className="home">
      <h1>OM Toolkit</h1>
      <p className="subtitle tagline">
        Interactive solvers for the core Operations Management methods — each
        one shows its work, step by step.
      </p>
      <div className="home-grid">
        {MODULES.map((m) => (
          <div key={m.path} className="card module-card">
            <h3>
              <m.icon size={17} color="var(--accent)" /> {m.name}
            </h3>
            <div className="decision">{m.decision}</div>
            <div className="actions">
              {m.ready ? (
                <>
                  <Link className="open" to={m.path}>
                    Open
                  </Link>
                  {m.exampleSearch && (
                    <Link className="example" to={m.path + m.exampleSearch}>
                      load an example →
                    </Link>
                  )}
                </>
              ) : (
                <span className="soon">Coming soon — available in the classic app</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

Create `web/src/pages/ComingSoon.tsx`:

```tsx
import { useLocation } from "react-router-dom";
import { MODULES } from "../modules";

export default function ComingSoon() {
  const { pathname } = useLocation();
  const mod = MODULES.find((m) => m.path === pathname);
  return (
    <div style={{ padding: "48px 56px" }}>
      <h1 style={{ fontSize: 24 }}>{mod?.name ?? "Module"}</h1>
      <p className="subtitle" style={{ marginTop: 8 }}>
        This module hasn't been rebuilt yet — it's still available in the
        classic Streamlit app while the redesign rolls out module by module.
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Wire the shell layout and routes**

Replace `web/src/App.tsx`:

```tsx
import { Route, Routes } from "react-router-dom";
import { Rail } from "./components/Rail";
import ComingSoon from "./pages/ComingSoon";
import Home from "./pages/Home";
import LotSizingPage from "./pages/lot-sizing/LotSizingPage";
import { MODULES } from "./modules";

export default function App() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Rail />
      <main style={{ flex: 1, minWidth: 0 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lot-sizing" element={<LotSizingPage />} />
          {MODULES.filter((m) => !m.ready).map((m) => (
            <Route key={m.path} path={m.path} element={<ComingSoon />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
```

Create a placeholder `web/src/pages/lot-sizing/LotSizingPage.tsx` so the build compiles (fully replaced in Task 9):

```tsx
export default function LotSizingPage() {
  return <div style={{ padding: 48 }}>Lot Sizing — under construction</div>;
}
```

- [ ] **Step 5: Verify build and look**

Run (in `web/`): `npm run build` — expect no errors.
Then `npm run dev` and open `http://localhost:5173`: dark rail with 7 icons, Home shows six cards, Lot Sizing card has Open + example links, others say coming soon. Stop the dev server.

- [ ] **Step 6: Commit**

```bash
git add web/src
git commit -m "feat: add app shell - icon rail, module registry, home"
```

---

### Task 7: Frontend lib — typed API client, debounce, URL state

**Files:**
- Create: `web/src/lib/api.ts`, `web/src/lib/useDebouncedValue.ts`, `web/src/lib/urlState.ts`, `web/src/lib/format.ts`
- Test: `web/src/lib/urlState.test.ts`, `web/src/lib/format.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `web/src/lib/urlState.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { decodeDynamic, encodeDynamic } from "./urlState";

describe("dynamic lot-sizing URL state", () => {
  it("round-trips inputs through the query string", () => {
    const inputs = { demands: [50, 60, 90], setupCost: 150, holdingCost: 1 };
    expect(decodeDynamic("?" + encodeDynamic(inputs))).toEqual(inputs);
  });

  it("returns null for missing or garbage params", () => {
    expect(decodeDynamic("")).toBeNull();
    expect(decodeDynamic("?d=50,abc&s=150&h=1")).toBeNull();
  });
});
```

Create `web/src/lib/format.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { formatMoney, percentGap } from "./format";

describe("formatting", () => {
  it("formats money without trailing zeros", () => {
    expect(formatMoney(640)).toBe("$640");
    expect(formatMoney(1234.5)).toBe("$1,234.5");
  });

  it("formats the gap to the best plan", () => {
    expect(percentGap(900, 640)).toBe("+41%");
    expect(percentGap(640, 640)).toBe("+0%");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (in `web/`): `npm test`
Expected: FAIL — modules `./urlState` and `./format` don't exist.

- [ ] **Step 3: Implement the lib modules**

Create `web/src/lib/urlState.ts`:

```ts
// Inputs serialize to the query string so a solved problem is a sharable link.
export interface DynamicInputs {
  demands: number[];
  setupCost: number;
  holdingCost: number;
}

export function encodeDynamic(inputs: DynamicInputs): string {
  const params = new URLSearchParams();
  params.set("d", inputs.demands.join(","));
  params.set("s", String(inputs.setupCost));
  params.set("h", String(inputs.holdingCost));
  return params.toString();
}

export function decodeDynamic(search: string): DynamicInputs | null {
  const params = new URLSearchParams(search);
  const d = params.get("d");
  const s = params.get("s");
  const h = params.get("h");
  if (!d || !s || !h) return null;
  const demands = d.split(",").map(Number);
  const setupCost = Number(s);
  const holdingCost = Number(h);
  if (demands.some(Number.isNaN) || Number.isNaN(setupCost) || Number.isNaN(holdingCost)) {
    return null;
  }
  return { demands, setupCost, holdingCost };
}
```

Create `web/src/lib/format.ts`:

```ts
export function formatMoney(value: number): string {
  return "$" + value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

/** Gap to the best plan, e.g. +41% — what choosing this method costs you. */
export function percentGap(cost: number, best: number): string {
  return `+${Math.round((cost / best - 1) * 100)}%`;
}
```

Create `web/src/lib/api.ts`:

```ts
// Typed client for the FastAPI backend. Core's ValueError messages arrive
// as {detail} on 422 and are shown inline next to the inputs.
export class ApiError extends Error {}

export async function postJson<TRes>(path: string, body: unknown): Promise<TRes> {
  const res = await fetch("/api" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(data?.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export interface PlanResult {
  orders: number[];
  setups: number;
  setup_cost: number;
  holding_cost: number;
  total_cost: number;
  ending_inventory: number[];
}

export type PlanName = "lot_for_lot" | "silver_meal" | "wagner_whitin";

export interface SilverMealStep {
  kind: "open_lot" | "try_extend" | "close_lot";
  lot: number;
  period?: number;
  avg_current?: number;
  avg_extended?: number;
  decision?: "extend" | "stop";
  start?: number;
  end?: number;
  quantity?: number;
}

export interface DynamicResponse {
  plans: Record<PlanName, PlanResult>;
  steps: SilverMealStep[];
}

export interface EoqResponse {
  quantity: number;
  orders_per_period: number;
  time_between_orders: number;
  ordering_cost_total: number;
  holding_cost_total: number;
  total_cost: number;
  curve: { q: number[]; ordering: number[]; holding: number[]; total: number[] };
}
```

Create `web/src/lib/useDebouncedValue.ts`:

```ts
import { useEffect, useState } from "react";

/** Live recompute without hammering the API: ~300ms after the last edit. */
export function useDebouncedValue<T>(value: T, ms = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return debounced;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run (in `web/`): `npm test`
Expected: 4 passed. Also `npm run build` — no TS errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib
git commit -m "feat: add typed api client, url state, and debounce hook"
```

---

### Task 8: Shared workbench components

**Files:**
- Create: `web/src/components/MetricCard.tsx`, `web/src/components/NumberField.tsx`, `web/src/components/DemandTable.tsx`, `web/src/components/DemandTable.css`, `web/src/components/PlotCard.tsx`, `web/src/components/workbench.css`, `web/src/types/plotly.d.ts`

- [ ] **Step 1: Plotly factory wrapper and type shim**

Create `web/src/types/plotly.d.ts`:

```ts
declare module "plotly.js-dist-min";
```

Create `web/src/components/PlotCard.tsx`:

```tsx
import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { Data, Layout } from "plotly.js";

const Plot = createPlotlyComponent(Plotly);

const BASE_LAYOUT: Partial<Layout> = {
  font: { family: "Inter, sans-serif", size: 12, color: "#101418" },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  margin: { l: 40, r: 16, t: 16, b: 32 },
};

export function PlotCard({
  label,
  data,
  layout,
  height = 280,
}: {
  label: string;
  data: Data[];
  layout?: Partial<Layout>;
  height?: number;
}) {
  return (
    <div className="card" style={{ padding: "12px 14px" }}>
      <div className="label">{label}</div>
      <Plot
        data={data}
        layout={{ ...BASE_LAYOUT, ...layout, height }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
```

- [ ] **Step 2: MetricCard and NumberField**

Create `web/src/components/MetricCard.tsx`:

```tsx
import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  detail,
  selected = false,
  onClick,
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      className="card"
      onClick={onClick}
      style={{
        padding: "10px 14px",
        flex: 1,
        cursor: onClick ? "pointer" : undefined,
        borderColor: selected ? "var(--accent)" : undefined,
        borderWidth: selected ? 1.5 : 1,
      }}
    >
      <div className="label">{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700 }}>
        {value}
      </div>
      {detail && <div style={{ fontSize: 11, color: "var(--subtle)" }}>{detail}</div>}
    </div>
  );
}
```

Create `web/src/components/NumberField.tsx`:

```tsx
export function NumberField({
  label,
  value,
  onChange,
  min = 0,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
}) {
  return (
    <div style={{ flex: 1 }}>
      <div className="label" style={{ marginBottom: 4 }}>{label}</div>
      <input
        type="number"
        value={Number.isNaN(value) ? "" : value}
        min={min}
        step="any"
        onChange={(e) => onChange(e.target.valueAsNumber)}
      />
    </div>
  );
}
```

- [ ] **Step 3: DemandTable with Excel paste**

Create `web/src/components/DemandTable.css`:

```css
.demand-table { width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 12px; }
.demand-table th { text-align: left; color: var(--muted); font-weight: 400; padding: 4px; }
.demand-table td { border-top: 1px solid #f1f4f6; padding: 2px 4px; }
.demand-table td.idx { color: var(--muted); width: 32px; }
.demand-table input { border: none; border-radius: 4px; padding: 5px 6px; background: transparent; }
.demand-table input:focus { outline: 1.5px solid var(--accent); background: var(--accent-soft); }
.demand-table-actions { display: flex; gap: 10px; margin-top: 6px; }
.demand-table-actions button {
  background: none; border: 1px solid var(--border); border-radius: 6px;
  padding: 3px 10px; font-size: 11px; color: var(--subtle);
}
.demand-table-hint { font-size: 10px; color: var(--muted); margin-top: 4px; }
```

Create `web/src/components/DemandTable.tsx`:

```tsx
import "./DemandTable.css";

/** Editable per-period numeric column. Pasting a column/range from
 * Excel/Sheets replaces values starting at the pasted-into row. */
export function DemandTable({
  label,
  values,
  onChange,
}: {
  label: string;
  values: number[];
  onChange: (next: number[]) => void;
}) {
  const setAt = (i: number, v: number) => {
    const next = [...values];
    next[i] = v;
    onChange(next);
  };

  const handlePaste = (i: number, e: React.ClipboardEvent) => {
    const pasted = e.clipboardData
      .getData("text")
      .split(/[\s,;]+/)
      .filter((t) => t.length > 0)
      .map(Number);
    if (pasted.length < 2 || pasted.some(Number.isNaN)) return; // normal paste
    e.preventDefault();
    const next = [...values];
    pasted.forEach((v, k) => {
      next[i + k] = v;
    });
    onChange(next);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>{label}</div>
      <table className="demand-table">
        <thead>
          <tr><th>t</th><th>demand</th></tr>
        </thead>
        <tbody>
          {values.map((v, i) => (
            <tr key={i}>
              <td className="idx">{i + 1}</td>
              <td>
                <input
                  type="number"
                  step="any"
                  min={0}
                  value={Number.isNaN(v) ? "" : v}
                  onChange={(e) => setAt(i, e.target.valueAsNumber)}
                  onPaste={(e) => handlePaste(i, e)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={() => onChange([...values, 0])}>+ period</button>
        <button onClick={() => values.length > 1 && onChange(values.slice(0, -1))}>
          − period
        </button>
      </div>
      <div className="demand-table-hint">tip: paste a column straight from Excel</div>
    </div>
  );
}
```

- [ ] **Step 4: Workbench layout CSS**

Create `web/src/components/workbench.css`:

```css
.workbench { display: flex; min-height: 100vh; }

.input-panel {
  width: 290px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-panel h1 { font-size: 20px; font-weight: 700; }
.input-panel .module-sub { margin-top: 2px; font-size: 12px; }

.mode-pills { display: flex; gap: 6px; }
.mode-pills button {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--subtle);
  border-radius: 99px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 500;
}
.mode-pills button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}

.results-pane {
  flex: 1;
  min-width: 0;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-card {
  padding: 14px 18px;
  background: linear-gradient(135deg, var(--accent-soft), var(--surface));
  border-color: var(--accent-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.hero-card .hero-value { font-family: var(--font-display); font-size: 26px; font-weight: 700; }
.hero-card .hero-detail { font-size: 12px; color: var(--subtle); font-weight: 500; }
.hero-card .hero-orders {
  font-family: var(--font-mono);
  background: var(--rail-bg);
  color: var(--accent-bright);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  white-space: nowrap;
}

.row { display: flex; gap: 10px; }
```

- [ ] **Step 5: Verify build, commit**

Run (in `web/`): `npm run build` — expect clean.

```bash
git add web/src/components web/src/types
git commit -m "feat: add shared workbench components"
```

---

### Task 9: Lot Sizing page — dynamic view (hero, comparison, chart)

**Files:**
- Create: `web/src/pages/lot-sizing/DynamicView.tsx`, `web/src/pages/lot-sizing/presets.ts`
- Modify: `web/src/pages/lot-sizing/LotSizingPage.tsx`

- [ ] **Step 1: Presets**

Create `web/src/pages/lot-sizing/presets.ts`:

```ts
import type { DynamicInputs } from "../../lib/urlState";

export const DYNAMIC_PRESETS: Record<string, DynamicInputs> = {
  "Six-period demo": { demands: [50, 60, 90, 70, 30, 100], setupCost: 150, holdingCost: 1 },
  "Lumpy demand": { demands: [10, 80, 0, 120, 5, 0, 90, 40], setupCost: 200, holdingCost: 2 },
  "Cheap setups": { demands: [40, 50, 35, 60, 45, 55], setupCost: 30, holdingCost: 3 },
};
```

- [ ] **Step 2: DynamicView**

Create `web/src/pages/lot-sizing/DynamicView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { DynamicResponse, PlanName } from "../../lib/api";
import { formatMoney, percentGap } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { DynamicInputs } from "../../lib/urlState";
import { DemandTable } from "../../components/DemandTable";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { DYNAMIC_PRESETS } from "./presets";
import { TeachingDrawer } from "./TeachingDrawer";

const PLAN_LABELS: Record<PlanName, string> = {
  wagner_whitin: "Wagner–Whitin",
  silver_meal: "Silver–Meal",
  lot_for_lot: "Lot-for-lot",
};
const PLAN_ORDER: PlanName[] = ["wagner_whitin", "silver_meal", "lot_for_lot"];

export function DynamicView({
  inputs,
  onInputs,
}: {
  inputs: DynamicInputs;
  onInputs: (next: DynamicInputs) => void;
}) {
  const [result, setResult] = useState<DynamicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<PlanName>("wagner_whitin");
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<DynamicResponse>("/lot-sizing/dynamic", {
      demands: debounced.demands,
      setup_cost: debounced.setupCost,
      holding_cost: debounced.holdingCost,
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

  const best = result?.plans.wagner_whitin;
  const plan = result?.plans[selected];
  const orderPeriods = best
    ? best.orders.flatMap((q, i) => (q > 0 ? [i + 1] : [])).join(", ")
    : "";
  const periods = inputs.demands.map((_, i) => i + 1);

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Lot Sizing</h1>
          <div className="subtitle module-sub">
            Balance setup costs against holding inventory.
          </div>
        </div>
        <DemandTable
          label="Demand per period"
          values={inputs.demands}
          onChange={(demands) => onInputs({ ...inputs, demands })}
        />
        <div className="row">
          <NumberField
            label="Setup S"
            value={inputs.setupCost}
            onChange={(setupCost) => onInputs({ ...inputs, setupCost })}
          />
          <NumberField
            label="Holding h"
            value={inputs.holdingCost}
            onChange={(holdingCost) => onInputs({ ...inputs, holdingCost })}
          />
        </div>
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = DYNAMIC_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(DYNAMIC_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {best && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Best plan — Wagner–Whitin (optimal)
              </div>
              <div className="hero-value">
                {formatMoney(best.total_cost)}{" "}
                <span className="hero-detail">
                  total cost · {best.setups} setups · orders in t = {orderPeriods}
                </span>
              </div>
            </div>
            <div className="hero-orders">
              {best.orders.map((q) => (q > 0 ? q : "—")).join(" · ")}
            </div>
          </div>
        )}
        {result && best && (
          <div className="row">
            {PLAN_ORDER.map((name) => (
              <MetricCard
                key={name}
                label={PLAN_LABELS[name]}
                value={formatMoney(result.plans[name].total_cost)}
                detail={
                  name === "wagner_whitin" ? (
                    <span style={{ color: "var(--accent)" }}>optimal ✓</span>
                  ) : (
                    percentGap(result.plans[name].total_cost, best.total_cost)
                  )
                }
                selected={selected === name}
                onClick={() => setSelected(name)}
              />
            ))}
          </div>
        )}
        {plan && (
          <PlotCard
            label={`${PLAN_LABELS[selected]} — orders vs demand, with ending inventory`}
            data={[
              { type: "bar", x: periods, y: inputs.demands, name: "Demand", marker: { color: "#e6eaee" } },
              { type: "bar", x: periods, y: plan.orders, name: "Order", marker: { color: "#0d9488" } },
              {
                type: "scatter",
                x: periods,
                y: plan.ending_inventory,
                name: "Ending inventory",
                mode: "lines+markers",
                line: { color: "#f59e0b" },
              },
            ]}
            layout={{ barmode: "group", xaxis: { dtick: 1, title: { text: "period" } } }}
          />
        )}
        {result && <TeachingDrawer steps={result.steps} />}
      </div>
    </>
  );
}
```

Create a placeholder `web/src/pages/lot-sizing/TeachingDrawer.tsx` so this compiles (fully implemented in Task 10):

```tsx
import type { SilverMealStep } from "../../lib/api";

export function TeachingDrawer({ steps }: { steps: SilverMealStep[] }) {
  return null && steps;
}
```

- [ ] **Step 3: Page wrapper with URL state**

Replace `web/src/pages/lot-sizing/LotSizingPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDynamic, encodeDynamic } from "../../lib/urlState";
import type { DynamicInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { DYNAMIC_PRESETS } from "./presets";
import { DynamicView } from "./DynamicView";

export default function LotSizingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputs, setInputs] = useState<DynamicInputs>(
    () => decodeDynamic("?" + searchParams.toString()) ?? DYNAMIC_PRESETS["Six-period demo"],
  );

  const update = (next: DynamicInputs) => {
    setInputs(next);
    setSearchParams(encodeDynamic(next), { replace: true });
  };

  return (
    <div className="workbench">
      <DynamicView inputs={inputs} onInputs={update} />
    </div>
  );
}
```

(EOQ mode pills are added in Task 11 — keeping this task shippable on its own.)

- [ ] **Step 4: Verify in the browser**

Run uvicorn in one terminal (repo root): `.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`
Run Vite in another (in `web/`): `npm run dev`
Open `http://localhost:5173/lot-sizing` and check: hero shows **$640**, orders `110 · — · 190 · — · — · 100`, three comparison cards (Lot-for-lot `+41%`), chart renders, editing a demand cell recomputes ~300ms later, setting Setup S to 0 shows the inline core error, presets load, and the URL updates as you type. Stop both servers.

- [ ] **Step 5: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src/pages
git commit -m "feat: add lot sizing dynamic view with live recompute"
```

---

### Task 10: Teaching drawer with step player

**Files:**
- Replace: `web/src/pages/lot-sizing/TeachingDrawer.tsx`
- Create: `web/src/pages/lot-sizing/TeachingDrawer.css`

- [ ] **Step 1: Implement the drawer**

Create `web/src/pages/lot-sizing/TeachingDrawer.css`:

```css
.drawer-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f8fafc;
  width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 13px;
  text-align: left;
}
.drawer-trigger b { font-weight: 600; }
.drawer-trigger .go {
  background: var(--rail-bg);
  color: #fff;
  border-radius: 8px;
  padding: 6px 14px;
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.step-player {
  background: var(--rail-bg);
  color: #d3dae1;
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.step-player .label { color: var(--accent-bright); }
.step-card { background: #1f2937; border-radius: 8px; padding: 10px 12px; font-size: 13px; }
.step-card .mono { font-family: var(--font-mono); }
.step-good { color: var(--accent-bright); font-weight: 600; }
.step-bad { color: #fca5a5; font-weight: 600; }
.step-nav { display: flex; gap: 8px; align-items: center; }
.step-nav button {
  border: 1px solid #374151;
  background: none;
  color: #d3dae1;
  border-radius: 6px;
  padding: 4px 14px;
  font-size: 12px;
}
.step-nav button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.step-nav button:disabled { opacity: 0.4; cursor: default; }
.step-nav .count { font-size: 11px; color: var(--muted); margin-left: auto; }
```

Replace `web/src/pages/lot-sizing/TeachingDrawer.tsx`:

```tsx
import { useEffect, useState } from "react";
import type { SilverMealStep } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import "./TeachingDrawer.css";

function describe(step: SilverMealStep): JSX.Element {
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
          💡 <b>Why these lots?</b>{" "}
          <span className="subtitle">
            watch Silver–Meal decide, step by step, on this exact data
          </span>
        </span>
        <span className="go">Walk me through it ▶</span>
      </button>
    );
  }

  const step = steps[Math.min(index, steps.length - 1)];
  return (
    <div className="step-player">
      <div className="label">LEARN · Silver–Meal, narrated by the solver</div>
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

- [ ] **Step 2: Verify in the browser**

Start both dev servers (as in Task 9 Step 4), open `/lot-sizing`, click **Walk me through it ▶**. Step through with buttons and arrow keys; with the default example the narration must follow the hand trace: lot 1 opens p1 → extend to p2 ($150→$105 ✓) → stop at p3 ($105→$130 ✕) → lot 1 fixed 110 units p1–2 → … → lot 3 fixed 100 units p6. Stop servers.

- [ ] **Step 3: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src/pages/lot-sizing
git commit -m "feat: add teaching drawer - silver-meal step player"
```

---

### Task 11: EOQ view and mode pills

**Files:**
- Create: `web/src/pages/lot-sizing/EoqView.tsx`
- Modify: `web/src/pages/lot-sizing/LotSizingPage.tsx`

- [ ] **Step 1: EoqView**

Create `web/src/pages/lot-sizing/EoqView.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { EoqResponse } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";

export interface EoqInputs {
  demand: number;
  orderingCost: number;
  holdingCost: number;
}

export const EOQ_DEFAULTS: EoqInputs = { demand: 1200, orderingCost: 100, holdingCost: 6 };

export function EoqView({
  inputs,
  onInputs,
}: {
  inputs: EoqInputs;
  onInputs: (next: EoqInputs) => void;
}) {
  const [result, setResult] = useState<EoqResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<EoqResponse>("/lot-sizing/eoq", {
      demand: debounced.demand,
      ordering_cost: debounced.orderingCost,
      holding_cost: debounced.holdingCost,
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
          <h1>Lot Sizing</h1>
          <div className="subtitle module-sub">
            Constant demand: the classic ordering-vs-holding trade-off.
          </div>
        </div>
        <NumberField
          label="Demand D (units/period)"
          value={inputs.demand}
          onChange={(demand) => onInputs({ ...inputs, demand })}
        />
        <NumberField
          label="Ordering cost S"
          value={inputs.orderingCost}
          onChange={(orderingCost) => onInputs({ ...inputs, orderingCost })}
        />
        <NumberField
          label="Holding cost H"
          value={inputs.holdingCost}
          onChange={(holdingCost) => onInputs({ ...inputs, holdingCost })}
        />
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Optimal order quantity
                </div>
                <div className="hero-value">
                  Q* = {result.quantity.toFixed(1)}{" "}
                  <span className="hero-detail">
                    units · {formatMoney(result.total_cost)} total ·{" "}
                    {result.orders_per_period.toFixed(2)} orders/period
                  </span>
                </div>
              </div>
            </div>
            <div className="row">
              <MetricCard label="Ordering cost" value={formatMoney(result.ordering_cost_total)} />
              <MetricCard label="Holding cost" value={formatMoney(result.holding_cost_total)} />
              <MetricCard
                label="Time between orders"
                value={result.time_between_orders.toFixed(3)}
                detail="periods"
              />
            </div>
            <PlotCard
              label="The trade-off: ordering falls, holding rises — Q* is the crossing"
              data={[
                { type: "scatter", x: result.curve.q, y: result.curve.ordering, name: "Ordering (D/Q)·S", line: { color: "#94a3b8" } },
                { type: "scatter", x: result.curve.q, y: result.curve.holding, name: "Holding (Q/2)·H", line: { color: "#cbd5e1" } },
                { type: "scatter", x: result.curve.q, y: result.curve.total, name: "Total", line: { color: "#0d9488", width: 3 } },
              ]}
              layout={{
                xaxis: { title: { text: "order quantity Q" } },
                yaxis: { range: [0, result.total_cost * 3] },
              }}
              height={320}
            />
          </>
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 2: Mode pills in the page wrapper**

Replace `web/src/pages/lot-sizing/LotSizingPage.tsx`:

```tsx
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDynamic, encodeDynamic } from "../../lib/urlState";
import type { DynamicInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { DYNAMIC_PRESETS } from "./presets";
import { DynamicView } from "./DynamicView";
import { EOQ_DEFAULTS, EoqView } from "./EoqView";
import type { EoqInputs } from "./EoqView";

export default function LotSizingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"dynamic" | "eoq">(
    searchParams.get("mode") === "eoq" ? "eoq" : "dynamic",
  );
  const [inputs, setInputs] = useState<DynamicInputs>(
    () => decodeDynamic("?" + searchParams.toString()) ?? DYNAMIC_PRESETS["Six-period demo"],
  );
  const [eoqInputs, setEoqInputs] = useState<EoqInputs>(EOQ_DEFAULTS);

  const update = (next: DynamicInputs) => {
    setInputs(next);
    setSearchParams(encodeDynamic(next), { replace: true });
  };

  const switchMode = (next: "dynamic" | "eoq") => {
    setMode(next);
    if (next === "eoq") setSearchParams("mode=eoq", { replace: true });
    else setSearchParams(encodeDynamic(inputs), { replace: true });
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button className={mode === "dynamic" ? "active" : ""} onClick={() => switchMode("dynamic")}>
          Dynamic demand
        </button>
        <button className={mode === "eoq" ? "active" : ""} onClick={() => switchMode("eoq")}>
          EOQ
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "dynamic" ? (
          <DynamicView inputs={inputs} onInputs={update} />
        ) : (
          <EoqView inputs={eoqInputs} onInputs={setEoqInputs} />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify in the browser**

Both dev servers up; check `/lot-sizing`: pills switch views; EOQ defaults show Q\* = 200.0 and $1,200; curve renders with the teal total crossing; `/lot-sizing?mode=eoq` opens straight to EOQ. Stop servers.

- [ ] **Step 4: Build check and commit**

Run (in `web/`): `npm run build` — clean.

```bash
git add web/src/pages/lot-sizing
git commit -m "feat: add EOQ view with mode pills"
```

---

### Task 12: Serve the built frontend from FastAPI

**Files:**
- Modify: `api/main.py`
- Test: `tests/test_api_main.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_main.py`:

```python
def test_spa_fallback_serves_index_for_client_routes(tmp_path, monkeypatch):
    """Deep links like /lot-sizing must serve the SPA's index.html."""
    import api.main as main

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "DIST_DIR", dist)

    response = client.get("/lot-sizing")
    assert response.status_code == 200
    assert "spa" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_main.py -q`
Expected: new test FAILS — `AttributeError` (no `DIST_DIR`) or 404.

- [ ] **Step 3: Implement static hosting with SPA fallback**

In `api/main.py`, add to the imports:

```python
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse
```

and at the bottom of the file (AFTER all routers are included — route order matters, `/api/*` must win):

```python
DIST_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"


@app.get("/{path:path}", include_in_schema=False)
async def spa(path: str):
    """Serve the built frontend; unknown paths fall back to index.html so
    client-side routes (e.g. /lot-sizing) survive refreshes and deep links."""
    if not DIST_DIR.exists():
        return JSONResponse(status_code=404, content={"detail": "Frontend not built."})
    file = DIST_DIR / path
    if path and file.is_file():
        return FileResponse(file)
    return FileResponse(DIST_DIR / "index.html")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api_main.py tests/test_api_lot_sizing.py -q`
Expected: all pass (API routes still resolve before the catch-all).

- [ ] **Step 5: Verify the single-server production mode**

Run (in `web/`): `npm run build`
Run (repo root): `.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`
Open `http://localhost:8000/lot-sizing` — the full app must work from the one server (no Vite). Stop the server.

- [ ] **Step 6: Commit**

```bash
git add api/main.py tests/test_api_main.py
git commit -m "feat: serve built frontend from FastAPI with SPA fallback"
```

---

### Task 13: Playwright smoke test

**Files:**
- Create: `web/playwright.config.ts`, `web/e2e/lot-sizing.spec.ts`
- Modify: `web/package.json` (script), `.gitignore`

- [ ] **Step 1: Install Playwright**

Run (in `web/`):

```bash
npm install -D @playwright/test
npx playwright install chromium
```

Add to `web/package.json` scripts: `"e2e": "playwright test"`.
Append to root `.gitignore`:

```
web/test-results/
web/playwright-report/
```

- [ ] **Step 2: Config that boots both servers**

Create `web/playwright.config.ts`:

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: [
    {
      command: "cd .. && .venv\\Scripts\\python.exe -m uvicorn api.main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
```

- [ ] **Step 3: Write the smoke spec**

Create `web/e2e/lot-sizing.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

// The hand-traced ground truth: [50,60,90,70,30,100], S=150, h=1 -> $640.
test("lot sizing solves the shared-link example to the hand-traced answer", async ({ page }) => {
  await page.goto("/lot-sizing?d=50,60,90,70,30,100&s=150&h=1");
  await expect(page.getByText("$640").first()).toBeVisible();
  await expect(page.getByText("+41%")).toBeVisible(); // lot-for-lot gap
});

test("teaching drawer narrates the first silver-meal decision", async ({ page }) => {
  await page.goto("/lot-sizing?d=50,60,90,70,30,100&s=150&h=1");
  await page.getByRole("button", { name: /walk me through it/i }).click();
  await expect(page.getByText(/Lot 1/).first()).toBeVisible();
  await page.getByRole("button", { name: /next/i }).click();
  await expect(page.getByText("$105")).toBeVisible(); // avg after first extension
});

test("eoq mode shows the closed-form optimum", async ({ page }) => {
  await page.goto("/lot-sizing?mode=eoq");
  await expect(page.getByText("Q* = 200.0")).toBeVisible();
  await expect(page.getByText("$1,200").first()).toBeVisible();
});
```

- [ ] **Step 4: Run the smoke tests**

Run (in `web/`): `npm run e2e`
Expected: 3 passed (Playwright boots uvicorn + Vite itself).

- [ ] **Step 5: Commit**

```bash
git add web/playwright.config.ts web/e2e web/package.json web/package-lock.json .gitignore
git commit -m "test: add playwright smoke for lot sizing"
```

---

### Task 14: Docs and final verification

**Files:**
- Modify: `README.md`, `CLAUDE.md`

- [ ] **Step 1: Document the new stack**

In `README.md`, replace the "Run locally" section with:

```markdown
## Run locally

**Classic app (Streamlit, all six modules):**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (use source .venv/bin/activate elsewhere)
pip install -r requirements.txt
streamlit run app/Home.py
```

**New app (React + FastAPI — being rolled out module by module):**

```bash
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
uvicorn api.main:app --port 8000     # serves API + UI at http://localhost:8000
```

Dev mode runs them separately: `uvicorn api.main:app --reload --port 8000`
in one terminal, `cd web && npm run dev` in another (Vite proxies /api).
```

In `CLAUDE.md`, update the Architecture section to:

```markdown
**Strict separation of algorithm logic and UI:**
- `core/` — all solver/algorithm logic as pure Python with **zero Streamlit imports**, independently testable.
- `api/` — FastAPI JSON layer over `core/` (one thin router per module); serves the built frontend.
- `web/` — React + TypeScript + Vite frontend (Clean Lab design system, see `docs/superpowers/specs/2026-06-11-react-redesign-design.md`).
- `app/` — legacy Streamlit UI, kept until the React app reaches feature parity.
- `tests/` — pytest tests for `core/` and `api/`; `web/` has Vitest unit tests and Playwright smoke tests (`npm test`, `npm run e2e` in `web/`).
```

- [ ] **Step 2: Full verification**

Run: `.\.venv\Scripts\python.exe -m pytest -q` — all pass.
Run (in `web/`): `npm test && npm run build && npm run e2e` — all pass.

- [ ] **Step 3: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: document the React + FastAPI stack and dev workflow"
```

---

## Self-review notes

- **Spec coverage:** scaffold ✓ (Tasks 1, 5, 6), Lot Sizing end-to-end ✓ (2–4, 9–11), teaching drawer + `explain` steps in core ✓ (3, 10), input ergonomics ✓ (DemandTable paste Task 8, debounce Task 7, URL state Tasks 7/9, presets Task 9), one-deployable hosting ✓ (12), testing layers ✓ (1–4 API, 7 Vitest, 13 Playwright), docs ✓ (14). NOT in this plan (later phases per spec): other five modules, retiring `app/`, deploy pipeline setup.
- **Type consistency check:** `DynamicInputs` (demands/setupCost/holdingCost) used in urlState, presets, DynamicView, LotSizingPage ✓; API snake_case fields match Pydantic models ✓; `silver_meal_with_steps` name consistent between core, `__init__`, router, and tests ✓; `TeachingDrawer({steps})` placeholder signature matches final ✓.
- **Arrow-key table navigation** from the spec's ergonomics list is deliberately deferred to a later polish task (native inputs already give Tab navigation); noted here so it isn't silently lost.
