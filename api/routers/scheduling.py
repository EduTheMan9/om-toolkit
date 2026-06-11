"""Scheduling endpoints: single-machine dispatching and Johnson flow shop."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.scheduling import (
    MAX_OPTIMAL_JOBS,
    RULES,
    Job,
    build_schedule,
    min_total_tardiness,
    moore_hodgson,
    schedule_metrics,
    validate_jobs,
)

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])


class DispatchJobIn(BaseModel):
    id: str
    processing_time: float
    due_date: float


class DispatchRequest(BaseModel):
    jobs: list[DispatchJobIn]


class ScheduledJobOut(BaseModel):
    id: str
    start: float
    end: float


class MethodResult(BaseModel):
    sequence: list[str]
    schedule: list[ScheduledJobOut]
    avg_completion_time: float
    avg_tardiness: float
    total_tardiness: float
    max_tardiness: float
    num_tardy: int


class DispatchResponse(BaseModel):
    methods: dict[str, MethodResult]
    optimal_capped: bool


@router.post("/dispatch", response_model=DispatchResponse)
def dispatch(req: DispatchRequest) -> DispatchResponse:
    jobs = [Job(j.id, j.processing_time, j.due_date) for j in req.jobs]
    # RULES are bare sort keys; validate explicitly so bad input fails fast
    # with core's human-readable message (the ValueError handler maps it to 422).
    validate_jobs(jobs)
    sequences = {name.lower(): rule(jobs) for name, rule in RULES.items()}
    sequences["moore_hodgson"] = moore_hodgson(jobs)
    capped = len(jobs) > MAX_OPTIMAL_JOBS  # the subset DP doubles per job
    if not capped:
        sequences["min_total_tardiness"], _ = min_total_tardiness(jobs)
    methods = {}
    for name, seq in sequences.items():
        schedule = build_schedule(seq)
        methods[name] = MethodResult(
            sequence=[j.id for j in seq],
            schedule=[
                ScheduledJobOut(id=s.id, start=s.start, end=s.end) for s in schedule
            ],
            **schedule_metrics(schedule, jobs),
        )
    return DispatchResponse(methods=methods, optimal_capped=capped)
