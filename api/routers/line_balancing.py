"""Line-balancing endpoint: all three heuristics, metrics, and diagram layout."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.line_balancing import (
    Station,
    Task,
    balance_delay,
    cycle_time_from_demand,
    kilbridge_columns,
    kilbridge_wester,
    largest_candidate_rule,
    line_efficiency,
    positional_weights,
    ranked_positional_weight_with_steps,
    smoothness_index,
    theoretical_min_stations,
)

router = APIRouter(prefix="/api/line-balancing", tags=["line-balancing"])


class TaskIn(BaseModel):
    id: str
    duration: float
    predecessors: list[str] = []


class SolveRequest(BaseModel):
    tasks: list[TaskIn]
    cycle_time: float | None = None
    available_time: float | None = None
    demand: int | None = None


class StationOut(BaseModel):
    index: int
    task_ids: list[str]
    total_time: float
    idle_time: float


class HeuristicResult(BaseModel):
    stations: list[StationOut]
    num_stations: int
    efficiency: float
    balance_delay: float
    smoothness_index: float


class SolveResponse(BaseModel):
    cycle_time: float
    total_work: float
    min_stations: int
    columns: dict[str, int]
    weights: dict[str, float]
    heuristics: dict[str, HeuristicResult]
    steps: list[dict]


def _resolve_cycle_time(req: SolveRequest) -> float:
    if req.cycle_time is not None:
        return req.cycle_time
    if req.available_time is not None and req.demand is not None:
        if req.available_time <= 0 or req.demand <= 0:
            raise ValueError("Available time and demand must be positive.")
        # course convention: floor, so the line is fast enough to meet demand
        return float(cycle_time_from_demand(req.available_time, req.demand))
    raise ValueError("Provide a cycle time, or available time and demand.")


def _result(stations: list[Station], cycle_time: float) -> HeuristicResult:
    return HeuristicResult(
        stations=[
            StationOut(
                index=s.index,
                task_ids=[t.id for t in s.tasks],
                total_time=s.total_time,
                idle_time=s.idle_time(cycle_time),
            )
            for s in stations
        ],
        num_stations=len(stations),
        efficiency=line_efficiency(stations, cycle_time),
        balance_delay=balance_delay(stations, cycle_time),
        smoothness_index=smoothness_index(stations, cycle_time),
    )


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest) -> SolveResponse:
    if not req.tasks:
        raise ValueError("Provide at least one task.")
    cycle_time = _resolve_cycle_time(req)
    tasks = [Task(t.id, t.duration, tuple(t.predecessors)) for t in req.tasks]
    # RPW runs first: its validate_tasks call is the input gate for all three
    rpw_stations, steps = ranked_positional_weight_with_steps(tasks, cycle_time)
    solutions = {
        "lcr": largest_candidate_rule(tasks, cycle_time),
        "rpw": rpw_stations,
        "kilbridge_wester": kilbridge_wester(tasks, cycle_time),
    }
    return SolveResponse(
        cycle_time=cycle_time,
        total_work=sum(t.duration for t in tasks),
        min_stations=theoretical_min_stations(tasks, cycle_time),
        columns=kilbridge_columns(tasks),
        weights=positional_weights(tasks),
        heuristics={
            name: _result(stations, cycle_time)
            for name, stations in solutions.items()
        },
        steps=steps,
    )
