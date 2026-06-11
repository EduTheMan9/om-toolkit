"""Rank Order Clustering — hand-traced validation (see Phase 5 spec).

Example A (4 machines x 5 parts): row binary values (P1 = MSB) are
18, 13, 18, 12 -> stable descending sort gives M1, M3, M2, M4; column
values then 12, 3, 3, 12, 2 -> P1, P4, P2, P3, P5. Second pass: no change.

Example B (4 x 4): rows 9, 7, 8, 6 -> M1, M3, M2, M4; columns then
12, 3, 3, 10 -> P1, P4, P2, P3.
"""
import pytest

from core.cellular.roc import rank_order_clustering, reorder_matrix, validate_matrix

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


def test_roc_worked_example_a():
    result = rank_order_clustering(MATRIX_A)
    assert result.row_order == [0, 2, 1, 3]
    assert result.col_order == [0, 3, 1, 2, 4]


def test_roc_worked_example_b():
    result = rank_order_clustering(MATRIX_B)
    assert result.row_order == [0, 2, 1, 3]
    assert result.col_order == [0, 3, 1, 2]


def test_roc_reordered_matrix_is_block_diagonal_for_example_a():
    result = rank_order_clustering(MATRIX_A)
    assert reorder_matrix(MATRIX_A, result.row_order, result.col_order) == [
        [1, 1, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1],
        [0, 0, 1, 1, 0],
    ]


def test_roc_already_sorted_matrix_converges_in_one_iteration():
    sorted_matrix = [
        [1, 1, 0, 0],
        [0, 0, 1, 1],
    ]
    result = rank_order_clustering(sorted_matrix)
    assert result.row_order == [0, 1]
    assert result.col_order == [0, 1, 2, 3]
    assert result.iterations == 1


def test_roc_ties_keep_current_order():
    # identical rows (and identical columns) must not be swapped
    result = rank_order_clustering([[1, 1], [1, 1]])
    assert result.row_order == [0, 1]
    assert result.col_order == [0, 1]


@pytest.mark.parametrize(
    "matrix, message",
    [
        ([], "at least one"),
        ([[]], "at least one"),
        ([[1, 0], [1]], "same number"),
        ([[1, 2], [0, 1]], "0 or 1"),
        ([[1, 1], [0, 0]], "processes no parts"),
        ([[1, 0], [1, 0]], "visits no machines"),
    ],
)
def test_invalid_matrices_rejected(matrix, message):
    with pytest.raises(ValueError, match=message):
        validate_matrix(matrix)
