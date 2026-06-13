"""Single-machine dispatching rules and their performance metrics.

Each rule is just a sort key over the job list; ties always break to the
lower job ID (course convention). FCFS keeps the input order, which is what
"first come" means when the table rows are the arrival order.
"""
from .models import Job, ScheduledJob


def validate_jobs(jobs: list[Job]) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not jobs:
        raise ValueError("Provide at least one job.")
    ids = [j.id.strip() for j in jobs]
    if any(not i for i in ids):
        raise ValueError("Every job needs an ID.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate job IDs in input.")
    for j in jobs:
        if j.processing_time <= 0:
            raise ValueError(f"Job {j.id}: processing time must be positive.")
        if j.due_date is None:
            raise ValueError(f"Job {j.id}: a due date is required.")
        if j.weight <= 0:
            raise ValueError(f"Job {j.id}: weight must be positive.")


RULES = {
    "FCFS": lambda jobs: list(jobs),
    "SPT": lambda jobs: sorted(jobs, key=lambda j: (j.processing_time, j.id)),
    "LPT": lambda jobs: sorted(jobs, key=lambda j: (-j.processing_time, j.id)),
    "EDD": lambda jobs: sorted(jobs, key=lambda j: (j.due_date, j.id)),
    # WSPT (Smith's rule): shortest weighted processing time first. Provably
    # minimizes total weighted completion time Σ w·C. Collapses to SPT when
    # every weight is 1.
    "WSPT": lambda jobs: sorted(jobs, key=lambda j: (j.processing_time / j.weight, j.id)),
}


def build_schedule(jobs_in_order: list[Job]) -> list[ScheduledJob]:
    """Run the jobs back to back from t = 0."""
    schedule, clock = [], 0.0
    for j in jobs_in_order:
        schedule.append(ScheduledJob(j.id, clock, clock + j.processing_time))
        clock += j.processing_time
    return schedule


def schedule_metrics(schedule: list[ScheduledJob], jobs: list[Job]) -> dict:
    """Standard single-machine performance measures.

    Tardiness is max(0, completion - due): finishing early earns no credit,
    which is what distinguishes it from lateness.
    """
    due = {j.id: j.due_date for j in jobs}
    weight = {j.id: j.weight for j in jobs}
    completions = [s.end for s in schedule]
    lateness = [s.end - due[s.id] for s in schedule]  # may be negative (early)
    tardiness = [max(0.0, late) for late in lateness]
    return {
        "avg_completion_time": sum(completions) / len(completions),
        "weighted_completion_time": sum(weight[s.id] * s.end for s in schedule),
        "avg_tardiness": sum(tardiness) / len(tardiness),
        "total_tardiness": sum(tardiness),
        "max_tardiness": max(tardiness),
        # L_max: lateness keeps its sign, so finishing everything early shows a
        # negative max — distinct from tardiness, which floors at zero.
        "max_lateness": max(lateness),
        "num_tardy": sum(1 for t in tardiness if t > 0),
    }
