"""Process-analysis endpoints: capacity/bottleneck analysis and Little's Law.

Unit-agnostic like core/: capacities come out in units per the same time
unit as processing_time. The frontend sends minutes and shows units/hour.
"""
from pydantic import BaseModel

from fastapi import APIRouter

from core.process_analysis import (
    Resource,
    bottleneck,
    capacity_steps,
    flow_rate,
    implied_utilization,
    process_capacity,
    solve_littles_law,
    unloaded_flow_time,
    utilization,
)

router = APIRouter(prefix="/api/process-analysis", tags=["process-analysis"])


class ResourceIn(BaseModel):
    name: str
    processing_time: float
    # float so a typed "1.5" reaches our check below and fails with a human
    # message instead of pydantic's structured 422
    servers: float = 1


class SolveRequest(BaseModel):
    resources: list[ResourceIn]
    demand: float | None = None


class ResourceOut(BaseModel):
    name: str
    processing_time: float
    servers: int
    capacity: float
    utilization: float
    implied_utilization: float | None


class SolveResponse(BaseModel):
    bottleneck: str
    process_capacity: float
    flow_rate: float
    constraint: str  # "demand" | "capacity"
    unloaded_flow_time: float
    resources: list[ResourceOut]
    steps: list[dict]


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    for r in req.resources:
        if r.servers != int(r.servers):
            raise ValueError(f"Resource {r.name}: servers must be a whole number.")
    resources = [
        Resource(r.name, r.processing_time, int(r.servers)) for r in req.resources
    ]
    if req.demand is not None and req.demand <= 0:
        raise ValueError("Demand must be positive.")
    # capacity_steps validates the resources (core's message -> 422)
    steps = capacity_steps(resources, req.demand)
    rate = flow_rate(resources, req.demand)
    flow_step = next(s for s in steps if s["kind"] == "flow_rate")
    return SolveResponse(
        bottleneck=bottleneck(resources).name,
        process_capacity=process_capacity(resources),
        flow_rate=rate,
        constraint=flow_step["constraint"],
        unloaded_flow_time=unloaded_flow_time(resources),
        resources=[
            ResourceOut(
                name=r.name,
                processing_time=r.processing_time,
                servers=r.servers,
                capacity=r.capacity,
                utilization=utilization(r, rate),
                implied_utilization=(
                    None if req.demand is None else implied_utilization(r, req.demand)
                ),
            )
            for r in resources
        ],
        steps=steps,
    )


class LittlesLawRequest(BaseModel):
    inventory: float | None = None
    flow_rate: float | None = None
    flow_time: float | None = None


class LittlesLawResponse(BaseModel):
    solved_for: str
    inventory: float
    flow_rate: float
    flow_time: float


@router.post("/littles-law", response_model=LittlesLawResponse)
def littles_law(req: LittlesLawRequest) -> LittlesLawResponse:
    value = solve_littles_law(req.inventory, req.flow_rate, req.flow_time)
    known = {
        "inventory": req.inventory,
        "flow_rate": req.flow_rate,
        "flow_time": req.flow_time,
    }
    solved_for = next(name for name, v in known.items() if v is None)
    known[solved_for] = value
    return LittlesLawResponse(solved_for=solved_for, **known)
