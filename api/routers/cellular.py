"""Cellular manufacturing endpoint: Rank Order Clustering + cell formation.

The response echoes the input matrix so the frontend renders the heatmaps
from one consistent payload - the page input is debounced, and the orders
must index into the matrix they were computed from, not the current edit.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.cellular import solve_cells

router = APIRouter(prefix="/api/cellular", tags=["cellular"])


class SolveRequest(BaseModel):
    matrix: list[list[int]]


class SolveResponse(BaseModel):
    matrix: list[list[int]]
    row_order: list[int]
    col_order: list[int]
    iterations: int
    machine_cells: list[int]
    part_cells: list[int]
    n_cells: int
    total_ones: int
    exceptional: int
    voids: int
    grouping_efficacy: float
    steps: list[dict]


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    # solve_cells validates the matrix (core's ValueError message -> 422)
    return SolveResponse(matrix=req.matrix, **solve_cells(req.matrix))
