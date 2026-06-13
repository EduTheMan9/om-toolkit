"""Productivity endpoint: two-period multifactor comparison.

The single-factor calculator (output / input in arbitrary units) is display
math and lives client-side, per the module spec.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.productivity import compare_periods, oee_steps, overall_equipment_effectiveness

router = APIRouter(prefix="/api/productivity", tags=["productivity"])


class InputRow(BaseModel):
    name: str
    previous: float
    current: float


class CompareRequest(BaseModel):
    previous_output: float
    current_output: float
    inputs: list[InputRow]


class MultifactorOut(BaseModel):
    previous: float
    current: float
    change: float


class FactorOut(BaseModel):
    name: str
    previous: float | None
    current: float | None
    change: float | None


class CompareResponse(BaseModel):
    multifactor: MultifactorOut
    factors: list[FactorOut]
    steps: list[dict]


@router.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest) -> CompareResponse:
    # compare_periods validates (core's ValueError message -> 422)
    return CompareResponse(**compare_periods(
        req.previous_output,
        req.current_output,
        [(r.name, r.previous, r.current) for r in req.inputs],
    ))


class OeeRequest(BaseModel):
    planned_time: float
    downtime: float
    ideal_cycle_time: float
    total_count: float
    good_count: float


class OeeResponse(BaseModel):
    run_time: float
    availability: float
    performance: float
    quality: float
    oee: float
    steps: list[dict]


@router.post("/oee", response_model=OeeResponse)
def oee(req: OeeRequest) -> OeeResponse:
    args = (
        req.planned_time, req.downtime, req.ideal_cycle_time,
        req.total_count, req.good_count,
    )
    # overall_equipment_effectiveness validates (core's ValueError -> 422)
    result = overall_equipment_effectiveness(*args)
    return OeeResponse(**result, steps=oee_steps(*args))
