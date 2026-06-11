# Design: Cellular Manufacturing module (Phase 5)

**Date:** 2026-06-11
**Status:** Implementing (per the amended direct-implementation workflow)

## Goal

Fifth OM Toolkit module: **Rank Order Clustering** (King, 1980) on a binary
machine–part incidence matrix, plus cell formation and the standard quality
metric (**grouping efficacy**) so the result is more than a pretty reordering.

## Definitions and conventions

- **Input:** binary matrix, rows = machines, columns = parts;
  `a[i][j] = 1` if part j visits machine i.
- **ROC:** read each row as a binary word (leftmost column = most significant
  bit) and sort rows by decreasing value; then the same for columns (topmost
  row = MSB). One iteration = one row sort + one column sort. Repeat until an
  iteration changes nothing. Ties keep their current relative order (stable
  sort) — the ROC analogue of the course's lower-ID tie-break.
- **Cell formation (after ROC ordering):** machines are split into
  *consecutive* groups; we enumerate all `2^(m-1)` boundary choices and keep
  the partition with the highest grouping efficacy. Each part joins the cell
  where it has the most 1s (tie → the earlier cell). Enumeration is capped
  (MAX_PARTITION_MACHINES = 16) like the scheduling module's exact optimizer.
- **Grouping efficacy:** `μ = (e − e_out) / (e + e_void)` where e = total 1s,
  e_out = exceptional elements (1s outside every cell), e_void = voids
  (0s inside a cell). μ = 1 is a perfect block diagonal.
- Validation rejects: empty matrix, ragged rows, non-binary entries, and
  all-zero rows/columns (a machine no part visits, or a part visiting no
  machine, doesn't belong in the analysis).

## Architecture

```
core/cellular/
    __init__.py   # public API
    roc.py        # validate_matrix(); rank_order_clustering() -> RocResult
    cells.py      # evaluate_cells(); find_best_cells() (exact enumeration)
app/
    pages/5_Cellular.py  # before/after matrix heatmaps, cells, efficacy
    cell_charts.py       # incidence-matrix heatmap with cell outlines
```

## Hand-traced validation examples

### Example A — perfect blocks (4 machines × 5 parts)

```
     P1 P2 P3 P4 P5        row values (P1 = MSB):
M1:   1  0  0  1  0        M1 = 10010 = 18
M2:   0  1  1  0  1        M2 = 01101 = 13
M3:   1  0  0  1  0        M3 = 18,  M4 = 01100 = 12
M4:   0  1  1  0  0
```

Row sort (desc, stable): M1, M3, M2, M4. Column values then read
P1 = 1100 = 12, P2 = 3, P3 = 3, P4 = 12, P5 = 2 → column order
P1, P4, P2, P3, P5. A second iteration changes nothing.

Result: perfect blocks {M1,M3}×{P1,P4} and {M2,M4}×{P2,P3,P5};
e = 9, exceptional = 0, voids = 1 (M4–P5) → μ = 9/10 = 0.9.

### Example B — one exceptional element (4 × 4)

```
     P1 P2 P3 P4
M1:   1  0  0  1       rows: 9, 7, 8, 6 -> order M1, M3, M2, M4
M2:   0  1  1  1       cols then: 12, 3, 3, 10 -> order P1, P4, P2, P3
M3:   1  0  0  0
M4:   0  1  1  0
```

Converged matrix has cells {M1,M3}×{P1,P4} (P4 ties 1–1 between cells →
earlier cell) and {M2,M4}×{P2,P3}. e = 8, exceptional = 1 (M2–P4),
voids = 1 (M3–P4) → μ = 7/9 ≈ 0.778. Enumeration confirms no other
consecutive partition beats it (one big cell: 8/16 = 0.5; splitting
either pair only adds exceptional elements).

## Testing

Validation tests (empty, ragged, non-binary, zero row/column); ROC orders +
convergence on both examples; evaluate_cells counts (ones, exceptional,
voids, efficacy) on a known assignment; find_best_cells recovers the traced
partition on A and B; single-machine edge case (one cell, μ from formula).
