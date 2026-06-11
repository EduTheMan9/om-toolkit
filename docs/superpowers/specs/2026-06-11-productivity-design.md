# Design: Productivity Metrics module (Phase 6)

**Date:** 2026-06-11
**Status:** Implementing (per the amended direct-implementation workflow)

## Goal

Sixth and final roadmap module. The kickoff names it without detail, so the
scope is the standard coursework trio (Stevenson / Heizer & Render):

1. **Single-factor (partial) productivity** — output per unit of ONE input
   (e.g. units per labor-hour). Unit-agnostic: the caller picks the units.
2. **Multifactor productivity** — output value per unit of combined input
   cost; only meaningful when inputs share a unit (money), so the API takes
   named input costs.
3. **Productivity change** — fractional change between two periods,
   `(current − previous) / previous`.

## Definitions and conventions

- Productivity is a ratio, never a difference: `P = output / input`.
- Single-factor: output may be physical or monetary; input must be positive.
- Multifactor: output value and per-factor input costs in the same currency;
  at least one factor, no negative costs, total cost positive.
- Change is returned as a fraction (0.25 = +25%); previous must be positive.
- The two-period comparison table in the UI is plain iteration over these
  primitives (display logic, not algorithm logic), so it lives in the page.

## Architecture

```
core/productivity/
    __init__.py   # public API
    metrics.py    # single_factor_productivity(); multifactor_productivity();
                  #   productivity_change()
app/
    pages/6_Productivity.py   # calculator + two-period comparison table
    productivity_charts.py    # per-factor change bar chart
```

## Hand-traced validation example

A shop sells 500 units at $10 in a week (output value $5,000):

- Labor was 200 hours → single-factor labor productivity
  = 500 / 200 = **2.5 units/hour**.
- Input costs: labor $1,500, materials $1,000, overhead $500 (total $3,000)
  → multifactor = 5000 / 3000 = **5/3 ≈ 1.667** ($ output per $ input).
- Last week labor productivity was 2.0 → change = (2.5 − 2.0) / 2.0
  = **+0.25 (25%)**.

## Testing

The three hand-checked values above; validation (non-positive input,
negative output, empty/negative/zero-total input costs, non-positive
previous productivity); multifactor equals single-factor when there is
exactly one input cost.
