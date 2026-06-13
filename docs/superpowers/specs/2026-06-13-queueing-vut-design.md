# Queueing (VUT) — Design

**Date:** 2026-06-13
**Module:** Process Analysis (new tab, alongside Process / Little's Law / Product Mix)
**Status:** Approved, ready for implementation plan

## Purpose

Add an interactive queueing solver to the Process Analysis module. Queueing is
the textbook continuation of Little's Law (`L = λ·W`), which already lives in
this module, so the two sit together pedagogically.

The headline concept is the **VUT decomposition** (Variability × Utilization ×
Time) — the variability-aware G/G/c waiting-time approximation. The exact
Markovian models (M/M/1, M/M/c) are included as the baseline the approximation
is compared against, so the user can *see* how good the approximation is. That
comparison is the core learning payoff and the kind of nuance an interviewer
probes.

### Learning goal

The user (3rd-year IEM student) must be able to explain every formula. The key
insight the tab makes concrete: **M/M/1 is just the VUT formula with
Ca = Cs = 1 and c = 1** (so V = 1) — they are the *same* equation. M/M/c, by
contrast, is exact only via **Erlang C**; the VUT/Sakasegawa formula merely
*approximates* it.

## Scope

In scope:

- **VUT / Kingman (G/G/1) and Sakasegawa (G/G/c) approximation** — the headline.
- **Exact M/M/1** — single-server Markovian.
- **Exact M/M/c (Erlang C)** — multi-server Markovian.
- KPIs: ρ (utilization), Lq, L, Wq, W, plus the V·U·T factor breakdown.
- Two charts: utilization→wait curve, and a VUT factor breakdown bar.

Out of scope (deferred to backlog, YAGNI):

- M/M/1/K (finite buffer), M/G/1 (Pollaczek–Khinchine), finite-population
  (M/M/c/K/N) models.

## Inputs

Rates + variability convention (unifies cleanly with the rate-based Markovian
models):

| Field | Symbol | Meaning |
|-------|--------|---------|
| Arrival rate | λ (`lam`) | customers per unit time |
| Service rate | μ (`mu`) | service completions per unit time **per server** |
| Servers | c (`c`) | number of parallel identical servers (≥1) |
| Arrival CV | Ca (`ca`) | coefficient of variation of interarrival times |
| Service CV | Cs (`cs`) | coefficient of variation of service times |

Utilization is computed: ρ = λ / (c·μ). CVs default to 1 (Markovian) in the UI.

## Architecture

Strict core / api / web separation, following the existing module pattern.

### 1. Core solver — `core/process_analysis/queueing.py`

Pure functions, zero web imports, each independently hand-traceable.

**`mm1(lam, mu)` → exact single-server**

```
ρ  = λ / μ
Lq = ρ² / (1 − ρ)
L  = ρ / (1 − ρ)
Wq = Lq / λ          (= ρ / (μ·(1 − ρ)))
W  = Wq + 1/μ        (= 1 / (μ − λ))
```

**`mmc(lam, mu, c)` → exact multi-server (Erlang C)**

```
a   = λ / μ                      (offered load, in Erlangs)
ρ   = a / c                      (utilization per server)
P0  = [ Σ_{n=0}^{c−1} aⁿ/n!  +  (a^c / c!)·(1/(1−ρ)) ]⁻¹
Pw  = (a^c / (c!·(1−ρ)))·P0      (Erlang C: probability an arrival waits)
Lq  = Pw · ρ / (1 − ρ)
Wq  = Lq / λ
L   = Lq + a
W   = Wq + 1/μ
```

**`vut(lam, mu, c, ca, cs)` → Sakasegawa G/G/c approximation**

Reduces exactly to Kingman G/G/1 when c = 1.

```
ρ = λ / (c·μ)
V = (Ca² + Cs²) / 2
U = ρ^(√(2(c+1)) − 1) / (c·(1 − ρ))
T = 1/μ
Wq ≈ V · U · T
```

Sanity check of the reduction at c = 1: exponent √(2·2) − 1 = 1, so
U = ρ/(1−ρ); with Ca = Cs = 1, V = 1, giving Wq = ρ/(μ(1−ρ)) = the exact M/M/1
result. For c > 1 with Ca = Cs = 1, Sakasegawa is an *approximation* to M/M/c —
this gap is the teaching point.

The function returns the three factors (V, U, T) separately, plus Wq, W, Lq, L,
so the UI can render the decomposition.

**Validation (all functions):** raise `ValueError` if any input ≤ 0, if c is not
a positive integer, or if ρ ≥ 1 (unstable queue — wait time diverges).

### 2. API — `api/routers/process_analysis.py`

One new endpoint: `POST /api/process-analysis/queueing`.

Request body:

```json
{ "lam": 8, "mu": 10, "c": 1, "ca": 1, "cs": 1 }
```

Response includes, where applicable:

- `vut`: { rho, V, U, T, Wq, W, Lq, L } — always present.
- `exact`: the matching exact model — M/M/1 when c == 1, M/M/c when c ≥ 1.
  Flagged `is_exact_for_inputs: true` only when Ca == Cs == 1 (otherwise the
  exact block is shown as the "Markovian reference", clearly labelled).
- `curve`: a server-side ρ-sweep for the chart — arrays of (rho, Wq, Lq) with ρ
  sampled (e.g. 0.05 → 0.95) holding λ as the varied driver against fixed μ, c,
  CVs, so the frontend just plots. Computing on the backend keeps the formula in
  one place (Python) rather than duplicating it in TypeScript.

Pydantic request/response models live in the router file, matching the existing
endpoints in this router.

### 3. Frontend — `web/src/pages/process-analysis/QueueingView.tsx`

- Register the tab in `ProcessAnalysisPage.tsx`; add a preset to `presets.ts`.
- Inputs: λ, μ, servers c, Ca, Cs (CVs default to 1).
- **KPI table:** ρ, Lq, L, Wq, W — VUT approximation column beside the exact
  M/M column, so they read side by side. When CVs ≠ 1, the exact column is
  labelled "Markovian reference (Ca=Cs=1)".
- **Chart 1 — utilization→wait curve:** Wq and Lq vs ρ over the sweep, with the
  user's operating point marked. Shows the nonlinear "explosion" as ρ → 1.
- **Chart 2 — VUT bar breakdown:** V × U × T → Wq, reinforcing the
  decomposition.
- Chart data prep lives in `charts.ts` (pure, testable), mirroring the existing
  pattern.

### 4. Tests

Following the validation rule: each solver is validated against a worked example
traced by hand, with the trace in the test/docstring **before** the test is
written.

- `tests/test_queueing.py`:
  - M/M/1 trace: λ = 8, μ = 10 → ρ = 0.8, Lq = 3.2, L = 4, Wq = 0.4, W = 0.5.
  - M/M/c trace: a small Erlang C case worked by hand (e.g. λ = 2, μ = 1.5,
    c = 2 → compute a, ρ, P0, Pw, Lq, Wq).
  - VUT reduces to M/M/1: `vut(8, 10, 1, 1, 1).Wq == mm1(8, 10).Wq`.
  - VUT with variability: a case with Ca, Cs ≠ 1 traced by hand.
  - Instability guard: ρ ≥ 1 raises `ValueError`; non-positive inputs raise.
- `tests/test_api.py` (or the process-analysis API test file): one happy-path
  request to the new endpoint asserting the response shape.
- `web/`: a Vitest test for the chart-data builders in `charts.ts`; one
  Playwright smoke step exercising the new tab.

## Data flow

```
User inputs (λ, μ, c, Ca, Cs)
  → QueueingView  → POST /api/process-analysis/queueing
  → router validates, calls core.queueing.{vut, mm1|mmc} + builds ρ-sweep
  → JSON { vut, exact, curve }
  → QueueingView renders KPI table + charts.ts builds both Plotly figures
```

## Error handling

- Core raises `ValueError` for non-positive inputs, non-integer/<1 server count,
  and unstable queues (ρ ≥ 1). The router maps these to HTTP 400 with the
  message, matching how the other process-analysis endpoints surface errors.
- The UI shows the error message inline near the inputs (existing pattern).
