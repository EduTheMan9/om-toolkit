"""Johnson's rule for the two-machine flow shop (provably minimal makespan).

Repeatedly take the smallest remaining processing time anywhere:
- if it is on machine 1, the job goes to the FRONT of the sequence
  (get it onto machine 2 quickly so machine 2 starts working early);
- if it is on machine 2, the job goes to the BACK
  (its short finish won't leave machine 2 idle at the end).

Conventions: a job whose own two times tie counts as machine-1-side (front);
ties between jobs break toward the machine-1-side job, then lower job ID.
"""
from dataclasses import dataclass

from .models import FlowShopJob, ScheduledJob


def validate_flow_shop_jobs(jobs: list[FlowShopJob]) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not jobs:
        raise ValueError("Provide at least one job.")
    ids = [j.id.strip() for j in jobs]
    if any(not i for i in ids):
        raise ValueError("Every job needs an ID.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate job IDs in input.")
    for j in jobs:
        if j.time_m1 <= 0 or j.time_m2 <= 0:
            raise ValueError(f"Job {j.id}: processing times must be positive.")


def johnson_sequence(jobs: list[FlowShopJob]) -> list[FlowShopJob]:
    validate_flow_shop_jobs(jobs)
    front: list[FlowShopJob] = []
    back: list[FlowShopJob] = []  # built in reverse, flipped at the end
    remaining = list(jobs)
    while remaining:
        best = min(
            remaining,
            key=lambda j: (
                min(j.time_m1, j.time_m2),
                0 if j.time_m1 <= j.time_m2 else 1,  # M1-side wins ties
                j.id,
            ),
        )
        remaining.remove(best)
        if best.time_m1 <= best.time_m2:
            front.append(best)
        else:
            back.append(best)
    return front + back[::-1]


@dataclass(frozen=True)
class TwoMachineSchedule:
    machine1: list[ScheduledJob]
    machine2: list[ScheduledJob]

    @property
    def makespan(self) -> float:
        return self.machine2[-1].end


def flow_shop_schedule(sequence: list[FlowShopJob]) -> TwoMachineSchedule:
    """Timeline for a given sequence: machine 1 runs back to back; machine 2
    starts each job when both the job's machine-1 pass and machine 2 itself
    are free — any gap on machine 2 is visible idle time."""
    m1, m2 = [], []
    m1_free = m2_free = 0.0
    for j in sequence:
        m1.append(ScheduledJob(j.id, m1_free, m1_free + j.time_m1))
        m1_free += j.time_m1
        start2 = max(m1_free, m2_free)
        m2.append(ScheduledJob(j.id, start2, start2 + j.time_m2))
        m2_free = start2 + j.time_m2
    return TwoMachineSchedule(machine1=m1, machine2=m2)
