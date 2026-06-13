# Queueing (VUT) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Queueing (VUT)" tab to the Process Analysis module that computes single- and multi-server queue metrics three ways — the VUT/Sakasegawa approximation alongside exact M/M/1 and M/M/c (Erlang C) — with a utilization→wait curve and a V·U·T factor-breakdown chart.

**Architecture:** Pure solver functions in `core/process_analysis/queueing.py` (zero web imports), exposed through one FastAPI endpoint `POST /api/process-analysis/queueing`, consumed by a new `QueueingView.tsx` tab. The exact Markovian models are the baseline the approximation is compared against; M/M/1 is literally the VUT formula with Ca=Cs=1, c=1. The ρ-sweep for the curve is computed server-side (reusing `vut`) so the formula lives only in Python.

**Tech Stack:** Python 3.11 (math stdlib only), FastAPI + Pydantic, pytest; React 18 + TypeScript, Plotly, Vitest, Playwright.

---

## File structure

- Create: `core/process_analysis/queueing.py` — `mm1`, `mmc`, `vut` pure functions.
- Modify: `core/process_analysis/__init__.py` — export the three functions.
- Modify: `api/routers/process_analysis.py` — add the `/queueing` endpoint + Pydantic models + ρ-sweep.
- Modify: `web/src/lib/api.ts` — add `QueueingResponse` and related types.
- Modify: `web/src/pages/process-analysis/charts.ts` — add `waitCurveTrace`, `operatingPointTrace`, `vutBreakdownTrace`.
- Create: `web/src/pages/process-analysis/QueueingView.tsx` — the tab UI + defaults/presets.
- Modify: `web/src/pages/process-analysis/ProcessAnalysisPage.tsx` — register the `queue` mode/tab.
- Create: `tests/test_queueing.py` — core hand-traced tests.
- Modify: `tests/test_api_process_analysis.py` — endpoint test.
- Modify: `web/src/pages/process-analysis/charts.test.ts` — chart-builder tests.
- Modify: `web/e2e/process-analysis.spec.ts` — smoke step for the new tab.

---

## Task 1: Core — exact M/M/1

**Files:**
- Create: `core/process_analysis/queueing.py`
- Test: `tests/test_queueing.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_queueing.py`:

```python
"""Queueing models, validated against hand traces.

M/M/1 at lambda=8, mu=10 (rho=0.8):
  Lq = rho^2/(1-rho) = 0.64/0.2 = 3.2
  L  = rho/(1-rho)   = 0.8/0.2  = 4.0
  Wq = Lq/lambda     = 3.2/8    = 0.4
  W  = Wq + 1/mu     = 0.4+0.1  = 0.5
  prob an arrival waits = rho = 0.8
"""
import pytest

from core.process_analysis.queueing import mm1


def test_mm1_worked_example():
    r = mm1(8.0, 10.0)
    assert r["rho"] == pytest.approx(0.8)
    assert r["Lq"] == pytest.approx(3.2)
    assert r["L"] == pytest.approx(4.0)
    assert r["Wq"] == pytest.approx(0.4)
    assert r["W"] == pytest.approx(0.5)
    assert r["prob_wait"] == pytest.approx(0.8)


def test_mm1_rejects_unstable_queue():
    with pytest.raises(ValueError, match="unstable"):
        mm1(10.0, 8.0)  # rho = 1.25 >= 1


def test_mm1_rejects_nonpositive():
    with pytest.raises(ValueError, match="positive"):
        mm1(0.0, 10.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_queueing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.process_analysis.queueing'`.

- [ ] **Step 3: Write minimal implementation**

Create `core/process_analysis/queueing.py`:

```python
"""Queueing models for a single station with c parallel servers.

Three views of the same station, all unit-agnostic (rates per the same time
unit):
  - mm1 / mmc : exact Markovian results (Poisson arrivals, exponential service).
  - vut       : the variability-aware G/G/c approximation (Sakasegawa), which
                reduces to Kingman's G/G/1 formula at c=1 and to the exact M/M/1
                result when Ca=Cs=1, c=1.

The exact models are the baseline the approximation is compared against.
"""
from math import factorial, sqrt


def _check_rates(lam: float, mu: float) -> None:
    if lam <= 0 or mu <= 0:
        raise ValueError("Arrival rate and service rate must be positive.")


def _check_stable(rho: float) -> None:
    if rho >= 1:
        raise ValueError(
            f"Queue is unstable: utilization rho={rho:.3f} >= 1. "
            "The waiting line grows without bound."
        )


def mm1(lam: float, mu: float) -> dict:
    """Exact M/M/1: Poisson arrivals (rate lam), one exponential server (rate mu)."""
    _check_rates(lam, mu)
    rho = lam / mu
    _check_stable(rho)
    lq = rho**2 / (1 - rho)
    length = rho / (1 - rho)
    wq = lq / lam
    w = wq + 1 / mu
    return {"rho": rho, "Lq": lq, "L": length, "Wq": wq, "W": w, "prob_wait": rho}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_queueing.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add core/process_analysis/queueing.py tests/test_queueing.py
git commit -m "feat: add exact M/M/1 queueing model"
```

---

## Task 2: Core — exact M/M/c (Erlang C)

**Files:**
- Modify: `core/process_analysis/queueing.py`
- Test: `tests/test_queueing.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_queueing.py`:

```python
from core.process_analysis.queueing import mmc

# M/M/c at lambda=2, mu=1.5, c=2 (Erlang C):
#   a   = lambda/mu = 4/3
#   rho = a/c = 2/3
#   sum_{n=0}^{1} a^n/n! = 1 + 4/3 = 7/3
#   (a^c/c!)*(1/(1-rho)) = (16/9/2)*3 = 8/3
#   P0 = 1/(7/3 + 8/3) = 1/5 = 0.2
#   Pw = (a^c/(c!*(1-rho)))*P0 = (8/3)*0.2 = 8/15
#   Lq = Pw*rho/(1-rho) = (8/15)*2 = 16/15
#   Wq = Lq/lambda = 8/15
#   L  = Lq + a = 16/15 + 20/15 = 36/15 = 2.4
#   W  = Wq + 1/mu = 8/15 + 10/15 = 18/15 = 1.2


def test_mmc_worked_example():
    r = mmc(2.0, 1.5, 2)
    assert r["rho"] == pytest.approx(2 / 3)
    assert r["prob_wait"] == pytest.approx(8 / 15)
    assert r["Lq"] == pytest.approx(16 / 15)
    assert r["Wq"] == pytest.approx(8 / 15)
    assert r["L"] == pytest.approx(2.4)
    assert r["W"] == pytest.approx(1.2)


def test_mmc_with_one_server_matches_mm1():
    one = mmc(8.0, 10.0, 1)
    base = mm1(8.0, 10.0)
    assert one["Wq"] == pytest.approx(base["Wq"])
    assert one["L"] == pytest.approx(base["L"])


def test_mmc_rejects_bad_server_count():
    with pytest.raises(ValueError, match="whole number"):
        mmc(2.0, 1.5, 0)


def test_mmc_rejects_unstable_queue():
    with pytest.raises(ValueError, match="unstable"):
        mmc(4.0, 1.5, 2)  # a=2.667, rho=1.333 >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_queueing.py -k mmc -v`
Expected: FAIL with `ImportError: cannot import name 'mmc'`.

- [ ] **Step 3: Write minimal implementation**

Append to `core/process_analysis/queueing.py`:

```python
def _check_servers(c: int) -> None:
    if not isinstance(c, int) or c < 1:
        raise ValueError("Number of servers must be a whole number >= 1.")


def mmc(lam: float, mu: float, c: int) -> dict:
    """Exact M/M/c via Erlang C: c identical exponential servers (rate mu each)."""
    _check_rates(lam, mu)
    _check_servers(c)
    a = lam / mu  # offered load, in Erlangs
    rho = a / c
    _check_stable(rho)
    # P0: normalising constant for the birth-death chain.
    head = sum(a**n / factorial(n) for n in range(c))
    tail = (a**c / factorial(c)) * (1 / (1 - rho))
    p0 = 1 / (head + tail)
    prob_wait = tail * p0  # Erlang C: probability an arrival has to queue
    lq = prob_wait * rho / (1 - rho)
    wq = lq / lam
    length = lq + a
    w = wq + 1 / mu
    return {
        "rho": rho, "Lq": lq, "L": length, "Wq": wq, "W": w,
        "prob_wait": prob_wait, "P0": p0,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_queueing.py -v`
Expected: PASS (all M/M/1 + M/M/c tests).

- [ ] **Step 5: Commit**

```bash
git add core/process_analysis/queueing.py tests/test_queueing.py
git commit -m "feat: add exact M/M/c queueing model (Erlang C)"
```

---

## Task 3: Core — VUT / Sakasegawa approximation

**Files:**
- Modify: `core/process_analysis/queueing.py`
- Test: `tests/test_queueing.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_queueing.py`:

```python
from core.process_analysis.queueing import vut

# VUT (Sakasegawa G/G/c, reduces to Kingman at c=1):
#   Wq ~= V * U * T
#   V = (Ca^2 + Cs^2)/2
#   U = rho^(sqrt(2(c+1)) - 1) / (c*(1-rho))
#   T = 1/mu
# At lambda=8, mu=10, c=1, Ca=Cs=1: V=1, exponent=sqrt(4)-1=1,
#   U = 0.8/0.2 = 4, T = 0.1 -> Wq = 0.4 == exact M/M/1.


def test_vut_reduces_to_mm1_when_markovian():
    r = vut(8.0, 10.0, 1, 1.0, 1.0)
    assert r["V"] == pytest.approx(1.0)
    assert r["U"] == pytest.approx(4.0)
    assert r["T"] == pytest.approx(0.1)
    assert r["Wq"] == pytest.approx(0.4)
    assert r["Wq"] == pytest.approx(mm1(8.0, 10.0)["Wq"])


def test_vut_low_arrival_variability_cuts_the_wait():
    # Deterministic arrivals (Ca=0), exponential service (Cs=1): V=0.5
    r = vut(8.0, 10.0, 1, 0.0, 1.0)
    assert r["V"] == pytest.approx(0.5)
    assert r["Wq"] == pytest.approx(0.2)


def test_vut_multiserver_approximates_mmc():
    # Same case as the exact M/M/c trace; Sakasegawa is an approximation.
    approx = vut(2.0, 1.5, 2, 1.0, 1.0)["Wq"]
    exact = mmc(2.0, 1.5, 2)["Wq"]
    assert approx == pytest.approx(exact, rel=0.1)


def test_vut_rejects_negative_cv():
    with pytest.raises(ValueError, match="coefficient of variation"):
        vut(8.0, 10.0, 1, -1.0, 1.0)


def test_vut_rejects_unstable_queue():
    with pytest.raises(ValueError, match="unstable"):
        vut(10.0, 8.0, 1, 1.0, 1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_queueing.py -k vut -v`
Expected: FAIL with `ImportError: cannot import name 'vut'`.

- [ ] **Step 3: Write minimal implementation**

Append to `core/process_analysis/queueing.py`:

```python
def vut(lam: float, mu: float, c: int, ca: float, cs: float) -> dict:
    """Sakasegawa G/G/c waiting-time approximation, decomposed as V * U * T.

    V (variability) = (Ca^2 + Cs^2)/2   -- the squared CVs of inter-arrival and
                                           service times.
    U (utilization) = rho^(sqrt(2(c+1)) - 1) / (c*(1-rho))
    T (time)        = 1/mu               -- the mean service time.
    Reduces to Kingman's G/G/1 at c=1, and to exact M/M/1 when Ca=Cs=1, c=1.
    """
    _check_rates(lam, mu)
    _check_servers(c)
    if ca < 0 or cs < 0:
        raise ValueError("Coefficient of variation must be >= 0.")
    rho = lam / (c * mu)
    _check_stable(rho)
    v = (ca**2 + cs**2) / 2
    u = rho ** (sqrt(2 * (c + 1)) - 1) / (c * (1 - rho))
    t = 1 / mu
    wq = v * u * t
    w = wq + t
    lq = lam * wq          # Little's Law on the queue
    length = lam * w       # Little's Law on the system
    return {"rho": rho, "V": v, "U": u, "T": t, "Wq": wq, "W": w, "Lq": lq, "L": length}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_queueing.py -v`
Expected: PASS (all core queueing tests).

- [ ] **Step 5: Commit**

```bash
git add core/process_analysis/queueing.py tests/test_queueing.py
git commit -m "feat: add VUT/Sakasegawa queueing approximation"
```

---

## Task 4: Core — export the functions

**Files:**
- Modify: `core/process_analysis/__init__.py`

- [ ] **Step 1: Add imports and `__all__` entries**

In `core/process_analysis/__init__.py`, add the import (after the `littles_law` import line):

```python
from .queueing import mm1, mmc, vut
```

And add `"mm1"`, `"mmc"`, `"vut"` to the `__all__` list (keep it alphabetised — they slot in before `"optimal_product_mix"` / among the lower-case names):

```python
    "mm1",
    "mmc",
    "vut",
```

- [ ] **Step 2: Verify the package imports cleanly**

Run: `python -c "from core.process_analysis import mm1, mmc, vut; print(mm1(8,10)['Wq'])"`
Expected: prints `0.4`.

- [ ] **Step 3: Commit**

```bash
git add core/process_analysis/__init__.py
git commit -m "chore: export queueing functions from process_analysis package"
```

---

## Task 5: API — `/queueing` endpoint with ρ-sweep

**Files:**
- Modify: `api/routers/process_analysis.py`
- Test: `tests/test_api_process_analysis.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_api_process_analysis.py`:

```python
def test_queueing_mm1_endpoint():
    # lambda=8, mu=10, c=1, Ca=Cs=1 -> exact M/M/1, Wq=0.4
    req = {"lam": 8, "mu": 10, "c": 1, "ca": 1, "cs": 1}
    response = client.post("/api/process-analysis/queueing", json=req)
    assert response.status_code == 200
    body = response.json()
    assert body["vut"]["Wq"] == pytest.approx(0.4)
    assert body["vut"]["V"] == pytest.approx(1.0)
    assert body["exact"]["model"] == "M/M/1"
    assert body["exact"]["Wq"] == pytest.approx(0.4)
    assert body["exact"]["is_exact_for_inputs"] is True
    # curve is a rho-sweep for the chart
    assert len(body["curve"]["rho"]) == len(body["curve"]["wq"]) > 0
    assert body["curve"]["rho"][0] < body["curve"]["rho"][-1]


def test_queueing_mmc_marks_reference_when_variable():
    # c=2 with non-unit CVs: exact block is the Markovian reference, not exact
    req = {"lam": 2, "mu": 1.5, "c": 2, "ca": 2, "cs": 0.5}
    response = client.post("/api/process-analysis/queueing", json=req)
    assert response.status_code == 200
    body = response.json()
    assert body["exact"]["model"] == "M/M/c"
    assert body["exact"]["is_exact_for_inputs"] is False


def test_queueing_rejects_unstable_queue():
    req = {"lam": 10, "mu": 8, "c": 1, "ca": 1, "cs": 1}
    response = client.post("/api/process-analysis/queueing", json=req)
    assert response.status_code == 422
    assert "unstable" in response.json()["detail"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_process_analysis.py -k queueing -v`
Expected: FAIL with 404 (route not registered).

- [ ] **Step 3: Write minimal implementation**

In `api/routers/process_analysis.py`, add `mm1`, `mmc`, `vut` to the `from core.process_analysis import (...)` block (keep alphabetical), then append at the end of the file:

```python
class QueueingRequest(BaseModel):
    lam: float
    mu: float
    c: int = 1
    ca: float = 1.0
    cs: float = 1.0


class VutOut(BaseModel):
    rho: float
    V: float
    U: float
    T: float
    Wq: float
    W: float
    Lq: float
    L: float


class ExactOut(BaseModel):
    model: str  # "M/M/1" | "M/M/c"
    rho: float
    Lq: float
    L: float
    Wq: float
    W: float
    prob_wait: float
    is_exact_for_inputs: bool


class CurveOut(BaseModel):
    rho: list[float]
    wq: list[float]
    lq: list[float]


class QueueingResponse(BaseModel):
    vut: VutOut
    exact: ExactOut
    curve: CurveOut


# rho sampled 0.05..0.95; the curve shows wait exploding as the queue saturates
_SWEEP = [i / 20 for i in range(1, 20)]


@router.post("/queueing", response_model=QueueingResponse)
def queueing(req: QueueingRequest) -> QueueingResponse:
    # core functions validate (their ValueError messages -> 422)
    approx = vut(req.lam, req.mu, req.c, req.ca, req.cs)
    if req.c == 1:
        ex, model = mm1(req.lam, req.mu), "M/M/1"
    else:
        ex, model = mmc(req.lam, req.mu, req.c), "M/M/c"

    # rho-sweep reuses vut so the formula lives only in core; vary lambda to hit
    # each rho at the user's fixed mu, c, and CVs.
    rho, wq, lq = [], [], []
    for r in _SWEEP:
        point = vut(r * req.c * req.mu, req.mu, req.c, req.ca, req.cs)
        rho.append(r)
        wq.append(point["Wq"])
        lq.append(point["Lq"])

    return QueueingResponse(
        vut=VutOut(**approx),
        exact=ExactOut(
            model=model,
            rho=ex["rho"], Lq=ex["Lq"], L=ex["L"], Wq=ex["Wq"], W=ex["W"],
            prob_wait=ex["prob_wait"],
            is_exact_for_inputs=(req.ca == 1 and req.cs == 1),
        ),
        curve=CurveOut(rho=rho, wq=wq, lq=lq),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_process_analysis.py -k queueing -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add api/routers/process_analysis.py tests/test_api_process_analysis.py
git commit -m "feat: add /process-analysis/queueing endpoint with rho-sweep"
```

---

## Task 6: Web — API types

**Files:**
- Modify: `web/src/lib/api.ts`

- [ ] **Step 1: Add the response types**

Append to `web/src/lib/api.ts` (after `LittlesLawResponse`):

```typescript
export interface QueueingResponse {
  vut: {
    rho: number;
    V: number;
    U: number;
    T: number;
    Wq: number;
    W: number;
    Lq: number;
    L: number;
  };
  exact: {
    model: "M/M/1" | "M/M/c";
    rho: number;
    Lq: number;
    L: number;
    Wq: number;
    W: number;
    prob_wait: number;
    is_exact_for_inputs: boolean;
  };
  curve: { rho: number[]; wq: number[]; lq: number[] };
}
```

- [ ] **Step 2: Verify it type-checks**

Run: `cd web && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/lib/api.ts
git commit -m "feat: add QueueingResponse type"
```

---

## Task 7: Web — chart builders

**Files:**
- Modify: `web/src/pages/process-analysis/charts.ts`
- Test: `web/src/pages/process-analysis/charts.test.ts`

- [ ] **Step 1: Write the failing test**

Append to `web/src/pages/process-analysis/charts.test.ts`:

```typescript
import { operatingPointTrace, vutBreakdownTrace, waitCurveTrace } from "./charts";

describe("waitCurveTrace", () => {
  it("plots Wq against utilization as a line", () => {
    const trace = waitCurveTrace({ rho: [0.5, 0.9], wq: [0.1, 0.9], lq: [0.05, 0.81] }) as any;
    expect(trace.type).toBe("scatter");
    expect(trace.mode).toBe("lines");
    expect(trace.x).toEqual([0.5, 0.9]);
    expect(trace.y).toEqual([0.1, 0.9]);
  });
});

describe("operatingPointTrace", () => {
  it("marks the user's operating point", () => {
    const trace = operatingPointTrace(0.8, 0.4) as any;
    expect(trace.mode).toBe("markers");
    expect(trace.x).toEqual([0.8]);
    expect(trace.y).toEqual([0.4]);
  });
});

describe("vutBreakdownTrace", () => {
  it("shows the three factors as bars", () => {
    const trace = vutBreakdownTrace(1, 4, 0.1) as any;
    expect(trace.type).toBe("bar");
    expect(trace.y).toEqual([1, 4, 0.1]);
    expect(trace.x.length).toBe(3);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npx vitest run src/pages/process-analysis/charts.test.ts`
Expected: FAIL — `waitCurveTrace is not a function` / import error.

- [ ] **Step 3: Write minimal implementation**

Append to `web/src/pages/process-analysis/charts.ts`:

```typescript
/** The signature queueing curve: mean wait Wq explodes as utilization -> 1. */
export function waitCurveTrace(curve: { rho: number[]; wq: number[] }): Data {
  return {
    type: "scatter",
    mode: "lines",
    x: curve.rho,
    y: curve.wq,
    line: { color: "#0d9488", width: 2 },
    hovertemplate: "ρ=%{x:.2f}<br>Wq=%{y:.3f}<extra></extra>",
    name: "Wq",
    showlegend: false,
  };
}

/** Red dot marking where the user's inputs sit on the wait curve. */
export function operatingPointTrace(rho: number, wq: number): Data {
  return {
    type: "scatter",
    mode: "markers",
    x: [rho],
    y: [wq],
    marker: { color: "#dc2626", size: 10 },
    hovertemplate: "operating point<br>ρ=%{x:.2f}<br>Wq=%{y:.3f}<extra></extra>",
    showlegend: false,
  };
}

/** V × U × T decomposition of the approximate wait, as three bars. */
export function vutBreakdownTrace(v: number, u: number, t: number): Data {
  return {
    type: "bar",
    x: ["V (variability)", "U (utilization)", "T (time)"],
    y: [v, u, t],
    marker: { color: "#0d9488" },
    text: [v, u, t].map((n) => formatNumber(n)),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npx vitest run src/pages/process-analysis/charts.test.ts`
Expected: PASS (all chart tests, old and new).

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/process-analysis/charts.ts web/src/pages/process-analysis/charts.test.ts
git commit -m "feat: add queueing chart builders (wait curve, VUT breakdown)"
```

---

## Task 8: Web — QueueingView component

**Files:**
- Create: `web/src/pages/process-analysis/QueueingView.tsx`

- [ ] **Step 1: Create the component**

Create `web/src/pages/process-analysis/QueueingView.tsx`:

```typescript
import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { QueueingResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { operatingPointTrace, vutBreakdownTrace, waitCurveTrace } from "./charts";

export interface QueueingInputs {
  lam: number;
  mu: number;
  c: number;
  ca: number;
  cs: number;
}

export const QUEUEING_DEFAULTS: QueueingInputs = {
  lam: 8,
  mu: 10,
  c: 1,
  ca: 1,
  cs: 1,
};

export const QUEUEING_PRESETS: Record<string, QueueingInputs> = {
  "Single server (M/M/1)": { lam: 8, mu: 10, c: 1, ca: 1, cs: 1 },
  "Two servers (M/M/2)": { lam: 2, mu: 1.5, c: 2, ca: 1, cs: 1 },
  "Steady arrivals (low variability)": { lam: 8, mu: 10, c: 1, ca: 0.25, cs: 1 },
};

export function QueueingView({
  inputs,
  onInputs,
}: {
  inputs: QueueingInputs;
  onInputs: (next: QueueingInputs) => void;
}) {
  const [result, setResult] = useState<QueueingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<QueueingResponse>("/process-analysis/queueing", debounced)
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

  const exactLabel = result?.exact.is_exact_for_inputs
    ? `exact ${result.exact.model}`
    : `${result?.exact.model} reference (Ca=Cs=1)`;

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Queueing (VUT)</h1>
          <div className="subtitle module-sub">
            Wq ≈ V × U × T — variability, utilization, and service time set the wait.
          </div>
        </div>
        <NumberField
          label="Arrival rate λ (per time)"
          value={inputs.lam}
          onChange={(lam) => onInputs({ ...inputs, lam })}
        />
        <NumberField
          label="Service rate μ (per server, per time)"
          value={inputs.mu}
          onChange={(mu) => onInputs({ ...inputs, mu })}
        />
        <NumberField
          label="Servers c"
          value={inputs.c}
          onChange={(c) => onInputs({ ...inputs, c })}
        />
        <NumberField
          label="Arrival CV (Ca)"
          value={inputs.ca}
          onChange={(ca) => onInputs({ ...inputs, ca })}
        />
        <NumberField
          label="Service CV (Cs)"
          value={inputs.cs}
          onChange={(cs) => onInputs({ ...inputs, cs })}
        />
        <div className="subtitle" style={{ fontSize: 11 }}>
          CV = 1 is Markovian (exact). CV &lt; 1 is steadier, &gt; 1 is burstier.
        </div>
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = QUEUEING_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(QUEUEING_PRESETS).map((name) => (
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
                Utilization ρ = λ / (c × μ)
              </div>
              <div className="hero-value">
                {Math.round(result.vut.rho * 100)}%{" "}
                <span className="hero-detail">
                  approx wait Wq {formatNumber(result.vut.Wq)} · in system W{" "}
                  {formatNumber(result.vut.W)}
                </span>
              </div>
            </div>
            <div className="hero-orders">Wq = V × U × T</div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="In queue Lq"
              value={formatNumber(result.vut.Lq)}
              detail={`exact ${formatNumber(result.exact.Lq)}`}
            />
            <MetricCard
              label="In system L"
              value={formatNumber(result.vut.L)}
              detail={`exact ${formatNumber(result.exact.L)}`}
            />
            <MetricCard
              label="Wait Wq"
              value={formatNumber(result.vut.Wq)}
              detail={`${exactLabel}: ${formatNumber(result.exact.Wq)}`}
            />
            <MetricCard
              label="In system W"
              value={formatNumber(result.vut.W)}
              detail={`exact ${formatNumber(result.exact.W)}`}
            />
          </div>
        )}
        {result && (
          <PlotCard
            label="Wait vs utilization — the wait explodes as ρ → 1"
            data={[
              waitCurveTrace(result.curve),
              operatingPointTrace(result.vut.rho, result.vut.Wq),
            ]}
            layout={{
              xaxis: { title: { text: "utilization ρ" }, range: [0, 1] },
              yaxis: { title: { text: "Wq (wait)" } },
            }}
            height={260}
          />
        )}
        {result && (
          <PlotCard
            label="VUT breakdown — the three factors multiply to Wq"
            data={[vutBreakdownTrace(result.vut.V, result.vut.U, result.vut.T)]}
            layout={{ yaxis: { title: { text: "factor value" } } }}
            height={220}
          />
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 2: Verify it type-checks**

Run: `cd web && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add web/src/pages/process-analysis/QueueingView.tsx
git commit -m "feat: add QueueingView tab UI"
```

---

## Task 9: Web — register the tab

**Files:**
- Modify: `web/src/pages/process-analysis/ProcessAnalysisPage.tsx`

- [ ] **Step 1: Wire the new mode**

Make these edits to `web/src/pages/process-analysis/ProcessAnalysisPage.tsx`:

Add the import near the other view imports:

```typescript
import { QUEUEING_DEFAULTS, QueueingView } from "./QueueingView";
import type { QueueingInputs } from "./QueueingView";
```

Widen the `Mode` type:

```typescript
type Mode = "capacity" | "littles" | "mix" | "queue";
```

Update the initial-mode read:

```typescript
  const [mode, setMode] = useState<Mode>(() => {
    const m = searchParams.get("mode");
    return m === "littles" || m === "mix" || m === "queue" ? m : "capacity";
  });
```

Add the queue state alongside the others:

```typescript
  const [queue, setQueue] = useState<QueueingInputs>(QUEUEING_DEFAULTS);
```

Add the tab button after the "Product mix (TOC)" button:

```typescript
        <button
          className={mode === "queue" ? "active" : ""}
          onClick={() => switchMode("queue")}
        >
          Queueing (VUT)
        </button>
```

Add the view render after the `mix` line:

```typescript
        {mode === "queue" && <QueueingView inputs={queue} onInputs={setQueue} />}
```

- [ ] **Step 2: Verify it type-checks and builds**

Run: `cd web && npx tsc --noEmit && npm run build`
Expected: type-check clean, build succeeds.

- [ ] **Step 3: Commit**

```bash
git add web/src/pages/process-analysis/ProcessAnalysisPage.tsx
git commit -m "feat: register Queueing (VUT) tab in process analysis"
```

---

## Task 10: Web — e2e smoke + full test sweep

**Files:**
- Modify: `web/e2e/process-analysis.spec.ts`

- [ ] **Step 1: Add the smoke test**

Append to `web/e2e/process-analysis.spec.ts`:

```typescript
// Queueing (tests/test_queueing.py): M/M/1 lambda=8, mu=10 -> rho=80%, Wq=0.4.
test("queueing tab shows the M/M/1 default", async ({ page }) => {
  await page.goto("/process-analysis?mode=queue");
  await expect(page.getByText("80%").first()).toBeVisible(); // utilization
  await expect(page.getByText(/exact M\/M\/1: 0.4/)).toBeVisible(); // Wq metric
});
```

- [ ] **Step 2: Run the new e2e test**

Run: `cd web && npx playwright test process-analysis --grep "queueing tab"`
Expected: PASS (1 test). (If Playwright browsers aren't installed, run `npx playwright install` first.)

- [ ] **Step 3: Run the full backend + frontend suites**

Run: `pytest`
Expected: all backend tests pass (196 = prior 193 + 3 new core groups counted as individual tests; the exact count will be higher — confirm zero failures).

Run: `cd web && npm test`
Expected: all Vitest tests pass.

Run: `cd web && npm run e2e`
Expected: all Playwright specs pass.

- [ ] **Step 4: Commit**

```bash
git add web/e2e/process-analysis.spec.ts
git commit -m "test: add e2e smoke for queueing tab"
```

---

## Task 11: Docs — README + close the plan

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Note the new solver in the README**

Find the Process Analysis bullet/section in `README.md` and add a mention of the queueing tab, matching the surrounding style — e.g. add to the process-analysis feature list:

```markdown
- **Queueing (VUT)** — single/multi-server waiting times via the VUT (Kingman/Sakasegawa) approximation, compared against exact M/M/1 and M/M/c (Erlang C), with the utilization→wait curve.
```

(Match the exact bullet format used by the other Process Analysis entries; if the README groups by module, place it under Process Analysis.)

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: note queueing (VUT) solver in README"
```

---

## Self-review notes (verified against the spec)

- **Spec coverage:** VUT/Sakasegawa (Task 3), exact M/M/1 (Task 1), exact M/M/c Erlang C (Task 2), KPIs ρ/Lq/L/Wq/W + V·U·T (Tasks 3, 8), side-by-side approx-vs-exact KPI table (Task 8), utilization→wait curve + VUT breakdown charts (Tasks 7–8), rates+variability inputs (Task 8), ρ-sweep on backend (Task 5), instability/validation errors → 422 (Tasks 1–3, 5). Out-of-scope models (M/M/1/K, M/G/1) correctly absent.
- **Type consistency:** core dict keys (`rho`, `Lq`, `L`, `Wq`, `W`, `prob_wait`, `P0`, `V`, `U`, `T`) match the Pydantic `VutOut`/`ExactOut` field names and the TS `QueueingResponse` interface; `curve` is `{rho, wq, lq}` everywhere; `is_exact_for_inputs` spelled consistently across API and UI.
- **No placeholders:** every code step is complete; the only judgement call is matching the README's existing bullet format (Task 11), which depends on current README wording.
```
