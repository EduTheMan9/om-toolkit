"""Cell formation and grouping efficacy — hand-traced (see Phase 5 spec).

Example A: cells {M1,M3}x{P1,P4} and {M2,M4}x{P2,P3,P5};
e = 9 ones, 0 exceptional, 1 void (M4-P5) -> efficacy 9/10.

Example B: cells {M1,M3}x{P1,P4} and {M2,M4}x{P2,P3};
e = 8, 1 exceptional (M2-P4), 1 void (M3-P4) -> efficacy 7/9.
P4 ties 1-1 between the cells and goes to the earlier one.
"""
import pytest

from core.cellular.cells import MAX_PARTITION_MACHINES, evaluate_cells, find_best_cells
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
