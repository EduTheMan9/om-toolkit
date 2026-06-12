"""Cell formation and grouping efficacy — hand-traced (see Phase 5 spec).

Example A: cells {M1,M3}x{P1,P4} and {M2,M4}x{P2,P3,P5};
e = 9 ones, 0 exceptional, 1 void (M4-P5) -> efficacy 9/10.

Example B: cells {M1,M3}x{P1,P4} and {M2,M4}x{P2,P3};
e = 8, 1 exceptional (M2-P4), 1 void (M3-P4) -> efficacy 7/9.
P4 ties 1-1 between the cells and goes to the earlier one.
"""
import pytest

from core.cellular.cells import (
    MAX_PARTITION_MACHINES,
    evaluate_cells,
    find_best_cells,
    solve_cells,
)
from core.cellular.roc import rank_order_clustering

MATRIX_A = [
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
]

MATRIX_B = [
    [1, 0, 0, 1],
    [0, 1, 1, 1],
    [1, 0, 0, 0],
    [0, 1, 1, 0],
]


def test_evaluate_cells_worked_example_b():
    # machine_cells / part_cells indexed by ORIGINAL matrix position
    metrics = evaluate_cells(MATRIX_B, [0, 1, 0, 1], [0, 1, 1, 0])
    assert metrics["total_ones"] == 8
    assert metrics["exceptional"] == 1
    assert metrics["voids"] == 1
    assert metrics["grouping_efficacy"] == pytest.approx(7 / 9)


def test_evaluate_cells_perfect_blocks_scores_one():
    matrix = [[1, 1, 0], [0, 0, 1]]
    metrics = evaluate_cells(matrix, [0, 1], [0, 0, 1])
    assert metrics["exceptional"] == 0
    assert metrics["voids"] == 0
    assert metrics["grouping_efficacy"] == pytest.approx(1.0)


def test_find_best_cells_worked_example_a():
    roc = rank_order_clustering(MATRIX_A)
    machine_cells, part_cells = find_best_cells(MATRIX_A, roc.row_order)
    assert machine_cells == [0, 1, 0, 1]
    assert part_cells == [0, 1, 1, 0, 1]
    metrics = evaluate_cells(MATRIX_A, machine_cells, part_cells)
    assert metrics["grouping_efficacy"] == pytest.approx(0.9)


def test_find_best_cells_worked_example_b():
    roc = rank_order_clustering(MATRIX_B)
    machine_cells, part_cells = find_best_cells(MATRIX_B, roc.row_order)
    assert machine_cells == [0, 1, 0, 1]
    assert part_cells == [0, 1, 1, 0]
    metrics = evaluate_cells(MATRIX_B, machine_cells, part_cells)
    assert metrics["grouping_efficacy"] == pytest.approx(7 / 9)


def test_single_machine_forms_one_cell():
    machine_cells, part_cells = find_best_cells([[1, 1]], [0])
    assert machine_cells == [0]
    assert part_cells == [0, 0]
    metrics = evaluate_cells([[1, 1]], machine_cells, part_cells)
    assert metrics["grouping_efficacy"] == pytest.approx(1.0)


def test_find_best_cells_rejects_oversized_instances():
    n = MAX_PARTITION_MACHINES + 1
    # diagonal matrix: machine i processes only part i (valid, just big)
    matrix = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    with pytest.raises(ValueError, match="machines"):
        find_best_cells(matrix, list(range(n)))


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
