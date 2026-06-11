"""Rank Order Clustering (King, 1980) on a machine-part incidence matrix.

Read each row as a binary number (leftmost part = most significant bit) and
sort rows by decreasing value; then do the same to columns. Repeat until a
full pass changes nothing. Ones drift toward the diagonal, exposing the
machine cells / part families hidden in the original row order.
"""
from dataclasses import dataclass


def validate_matrix(matrix: list[list[int]]) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not matrix or not matrix[0]:
        raise ValueError("Need at least one machine and one part.")
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("Every machine row must have the same number of parts.")
    if any(cell not in (0, 1) for row in matrix for cell in row):
        raise ValueError("Matrix entries must be 0 or 1.")
    for i, row in enumerate(matrix):
        if not any(row):
            raise ValueError(f"Machine {i + 1} processes no parts - remove it.")
    for j in range(width):
        if not any(row[j] for row in matrix):
            raise ValueError(f"Part {j + 1} visits no machines - remove it.")


@dataclass(frozen=True)
class RocResult:
    row_order: list[int]   # original machine indices, top to bottom
    col_order: list[int]   # original part indices, left to right
    iterations: int        # passes until a full pass changed nothing


def _sorted_by_binary_value(vectors: list[list[int]], current: list[int]) -> list[int]:
    """Reorder `current` indices by decreasing binary value of their vectors.
    The sort is stable, so ties keep their current relative order (the ROC
    analogue of the course's lower-ID tie-break)."""
    def value(index: int) -> int:
        bits = 0
        for bit in vectors[index]:
            bits = bits * 2 + bit
        return bits

    return sorted(current, key=value, reverse=True)


def rank_order_clustering(matrix: list[list[int]]) -> RocResult:
    validate_matrix(matrix)
    n_rows, n_cols = len(matrix), len(matrix[0])
    row_order = list(range(n_rows))
    col_order = list(range(n_cols))

    iterations = 0
    while True:
        iterations += 1
        # Row pass: each row read left-to-right in the CURRENT column order.
        rows = [[matrix[i][j] for j in col_order] for i in range(n_rows)]
        new_rows = _sorted_by_binary_value(rows, row_order)
        # Column pass: each column read top-to-bottom in the NEW row order.
        cols = [[matrix[i][j] for i in new_rows] for j in range(n_cols)]
        new_cols = _sorted_by_binary_value(cols, col_order)

        if new_rows == row_order and new_cols == col_order:
            return RocResult(row_order, col_order, iterations)
        row_order, col_order = new_rows, new_cols


def reorder_matrix(
    matrix: list[list[int]], row_order: list[int], col_order: list[int]
) -> list[list[int]]:
    return [[matrix[i][j] for j in col_order] for i in row_order]
