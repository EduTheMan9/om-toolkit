# Design: MRP & Lot Sizing module (Phase 4)

**Date:** 2026-06-11
**Status:** Implementing (per the amended direct-implementation workflow)

## Goal

Fourth OM Toolkit module, the lot-sizing methods named in the kickoff:

1. **EOQ** — continuous, constant demand: optimal order quantity and the
   ordering/holding cost trade-off curve.
2. **Dynamic lot sizing** — period-by-period demand with setup cost S and
   holding cost h: **lot-for-lot**, **Silver–Meal** (heuristic), and
   **Wagner–Whitin** (exact DP), compared side by side.

(BOM explosion / multi-level MRP is out of scope: the kickoff's parenthetical
defines the module as these four methods.)

## Definitions and conventions

- **EOQ:** `Q* = sqrt(2DS/H)`; total relevant cost `TC = (D/Q)S + (Q/2)H`;
  at Q* the two terms are equal. D, S, H are per the same period (e.g. a year).
- **Dynamic models:** orders arrive at the start of a period; holding cost h
  is charged on **end-of-period inventory** (units consumed in their arrival
  period incur no holding). Carrying d_k from period j to k costs `h·(k−j)·d_k`.
- **Silver–Meal:** extend the current lot one period at a time while the
  *average cost per period covered* decreases; stop at the first increase.
  (Myopic — usually near-optimal, not guaranteed.)
- **Wagner–Whitin:** `f(t) = min over j≤t of f(j−1) + c(j,t)` where `c(j,t)`
  = setup + holding to cover periods j..t from one order at j. Provably optimal.
- Lot-for-lot incurs a setup only in periods with positive demand.
- No shortages allowed; plan evaluation raises on any negative inventory.

## Architecture

```
core/lot_sizing/
    __init__.py    # public API
    eoq.py         # EOQResult dataclass + economic_order_quantity()
    dynamic.py     # validation; evaluate_plan(); lot_for_lot();
                   #   silver_meal(); wagner_whitin()
app/
    pages/4_Lot_Sizing.py   # two tabs: EOQ / dynamic lot sizing
    lot_charts.py           # EOQ cost curve; per-period orders+inventory chart
```

All three dynamic methods return the same shape — an order quantity per
period — so one `evaluate_plan(demands, orders, S, h)` computes setups,
holding, totals, and ending inventory for any of them (and for the UI).

## Hand-traced validation example

Demands [50, 60, 90, 70, 30, 100], S = 150, h = 1:

- **Lot-for-lot:** 6 setups → 900, holding 0, total **900**.
- **Silver–Meal:** lot 1 covers p1–2 (avg 150 → 105 → stop at 130);
  lot 2 covers p3–5 (150 → 110 → 93.3 → stop at 145); lot 3 covers p6.
  Orders [110, 0, 190, 0, 0, 100]; setups 450, holding 60+70+2·30 = 190,
  total **640**.
- **Wagner–Whitin:** f = [150, 210, 360, 430, 490, **640**]; reconstruction
  gives the same plan [110, 0, 190, 0, 0, 100]. (On this instance the
  heuristic happens to hit the optimum; WW's guarantee is the point.)
- **EOQ check:** D=1200, S=100, H=6 → Q* = sqrt(40000) = 200,
  TC = 600 + 600 = 1200, 6 orders/period.

## Testing

EOQ closed-form case; evaluate_plan accumulation + shortage rejection;
one test per method asserting orders and total cost from the traces above;
WW ≤ Silver–Meal on any instance (asserted on the example); validation
tests (empty demands, negative demand, non-positive costs).
