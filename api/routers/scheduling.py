"""Scheduling endpoints: single-machine dispatching and Johnson flow shop."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.scheduling import (
    MAX_OPTIMAL_JOBS,
    RULES,
    FlowShopJob,
    Job,
    build_schedule,
    flow_shop_schedule,
    johnson_sequence_with_steps,
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
    weight: float = 1.0


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
    weighted_completion_time: float
    avg_tardiness: float
    total_tardiness: float
    max_tardiness: float
    max_lateness: float
    num_tardy: int


class DispatchResponse(BaseModel):
    methods: dict[str, MethodResult]
    optimal_capped: bool


@router.post("/dispatch", response_model=DispatchResponse)
def dispatch(req: DispatchRequest) -> DispatchResponse:
    jobs = [Job(j.id, j.processing_time, j.due_date, j.weight) for j in req.jobs]
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


class FlowShopJobIn(BaseModel):
    id: str
    time_m1: float
    time_m2: float


class JohnsonRequest(BaseModel):
    jobs: list[FlowShopJobIn]


class JohnsonResponse(BaseModel):
    sequence: list[str]
    machine1: list[ScheduledJobOut]
    machine2: list[ScheduledJobOut]
    makespan: float
    input_order_makespan: float
    steps: list[dict]


@router.post("/johnson", response_model=JohnsonResponse)
def johnson(req: JohnsonRequest) -> JohnsonResponse:
    jobs = [FlowShopJob(j.id, j.time_m1, j.time_m2) for j in req.jobs]
    sequence, steps = johnson_sequence_with_steps(jobs)  # validates first
    schedule = flow_shop_schedule(sequence)
    # the "do nothing" baseline: run the jobs in the order they were typed
    input_order_makespan = flow_shop_schedule(jobs).makespan
    return JohnsonResponse(
        sequence=[j.id for j in sequence],
        machine1=[
            ScheduledJobOut(id=s.id, start=s.start, end=s.end)
            for s in schedule.machine1
        ],
        machine2=[
            ScheduledJobOut(id=s.id, start=s.start, end=s.end)
            for s in schedule.machine2
        ],
        makespan=schedule.makespan,
        input_order_makespan=input_order_makespan,
        steps=steps,
    )
