"""Cell formation on a ROC-ordered matrix, scored by grouping efficacy.

ROC only reorders the matrix - it never says where one cell ends and the
next begins. Here machines are split into consecutive groups (consecutive
in the ROC order, where related machines already sit together), every
possible split is tried, and the one with the highest grouping efficacy
wins: mu = (e - exceptional) / (e + voids), which is 1 for perfect blocks.
"""
from .roc import validate_matrix

# 2^(m-1) consecutive partitions are enumerated; like the scheduling
# module's exact optimizer, cap the exponent at course-problem sizes.
MAX_PARTITION_MACHINES = 16


def evaluate_cells(
    matrix: list[list[int]], machine_cells: list[int], part_cells: list[int]
) -> dict:
    """Score a cell assignment (indexed by ORIGINAL matrix positions):
    exceptional = 1s outside every cell (parts that must travel between
    cells), voids = 0s inside a cell (idle machine-part pairings)."""
    validate_matrix(matrix)
    total_ones = exceptional = voids = 0
    for i, row in enumerate(matrix):
        for j, entry in enumerate(row):
            same_cell = machine_cells[i] == part_cells[j]
            if entry == 1:
                total_ones += 1
                if not same_cell:
                    exceptional += 1
            elif same_cell:
                voids += 1
    return {
        "total_ones": total_ones,
        "exceptional": exceptional,
        "voids": voids,
        "grouping_efficacy": (total_ones - exceptional) / (total_ones + voids),
    }


def _assign_parts(
    matrix: list[list[int]], machine_cells: list[int], n_cells: int
) -> list[int]:
    """Each part joins the cell where it has the most 1s; ties go to the
    earlier cell (the ROC analogue of the course's lower-ID tie-break)."""
    part_cells = []
    for j in range(len(matrix[0])):
        ones_per_cell = [0] * n_cells
        for i, row in enumerate(matrix):
            ones_per_cell[machine_cells[i]] += row[j]
        part_cells.append(max(range(n_cells), key=lambda c: (ones_per_cell[c], -c)))
    return part_cells


def find_best_cells(
    matrix: list[list[int]], row_order: list[int]
) -> tuple[list[int], list[int]]:
    """Best consecutive-machine partition by grouping efficacy (exact).

    A boundary bitmask picks where the machine sequence is cut: bit b set
    means a new cell starts after position b of row_order. All 2^(m-1)
    masks are tried; mask 0 is the single-cell baseline.
    """
    validate_matrix(matrix)
    m = len(row_order)
    if m > MAX_PARTITION_MACHINES:
        raise ValueError(
            f"Exact cell search is limited to {MAX_PARTITION_MACHINES} machines."
        )

    best: tuple[list[int], list[int]] | None = None
    best_efficacy = -1.0
    for mask in range(2 ** (m - 1)):
        machine_cells = [0] * m  # indexed by original machine position
        cell = 0
        for position, machine in enumerate(row_order):
            if position > 0 and mask & (1 << (position - 1)):
                cell += 1
            machine_cells[machine] = cell
        part_cells = _assign_parts(matrix, machine_cells, cell + 1)
        efficacy = evaluate_cells(matrix, machine_cells, part_cells)["grouping_efficacy"]
        if efficacy > best_efficacy:
            best_efficacy = efficacy
            best = (machine_cells, part_cells)

    assert best is not None  # mask 0 always evaluated
    return best
