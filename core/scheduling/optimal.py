"""Exact (optimal) single-machine sequencing.

Two true optimizers, complementing the dispatching RULES (which are optimal
only for their own objectives — SPT for average completion time, EDD for
maximum lateness):

- Moore-Hodgson: minimizes the NUMBER of tardy jobs, in O(n log n).
- min_total_tardiness: minimizes TOTAL tardiness. That problem is NP-hard,
  so this is a dynamic program over subsets — exact, but limited to
  MAX_OPTIMAL_JOBS inputs (2^n states).
"""
from .dispatching import validate_jobs
from .models import Job

MAX_OPTIMAL_JOBS = 15  # 2^15 = 32768 DP states: instant; growth is exponential


def moore_hodgson(jobs: list[Job]) -> list[Job]:
    """Sequence with the provably minimal number of tardy jobs.

    Walk the jobs in EDD order; whenever the running schedule makes the
    current job late, eject the LONGEST job scheduled so far (freeing the
    most time at the cost of exactly one late job). Ejected jobs run at the
    end, where they are late anyway.
    """
    validate_jobs(jobs)
    on_time: list[Job] = []
    rejected: list[Job] = []
    clock = 0.0
    for j in sorted(jobs, key=lambda x: (x.due_date, x.id)):
        on_time.append(j)
        clock += j.processing_time
        if clock > j.due_date:
            # max() keeps the first on ties, i.e. earliest in EDD order
            worst = max(on_time, key=lambda x: x.processing_time)
            on_time.remove(worst)
            rejected.append(worst)
            clock -= worst.processing_time
    return on_time + rejected


def min_total_tardiness(jobs: list[Job]) -> tuple[list[Job], float]:
    """Exact minimum-total-tardiness sequence via subset DP.

    Key fact making this work: whichever set S of jobs runs first, the job
    placed LAST within S always completes at sum of S's processing times —
    independent of the order inside S. So dp[S] = best total tardiness for
    scheduling exactly the set S first, built by choosing each member of S
    as its last job.
    """
    validate_jobs(jobs)
    n = len(jobs)
    if n > MAX_OPTIMAL_JOBS:
        raise ValueError(
            f"Exact optimization is limited to {MAX_OPTIMAL_JOBS} jobs "
            f"(got {n}): the search space doubles with every job."
        )

    full = (1 << n) - 1
    # completion time of each subset = total processing time of its members
    subset_time = [0.0] * (full + 1)
    for mask in range(1, full + 1):
        low = (mask & -mask).bit_length() - 1
        subset_time[mask] = subset_time[mask ^ (1 << low)] + jobs[low].processing_time

    dp = [float("inf")] * (full + 1)
    dp[0] = 0.0
    last = [-1] * (full + 1)
    for mask in range(1, full + 1):
        finish = subset_time[mask]
        for j in range(n):
            if not mask & (1 << j):
                continue
            tardiness = max(0.0, finish - jobs[j].due_date)
            candidate = dp[mask ^ (1 << j)] + tardiness
            if candidate < dp[mask]:
                dp[mask] = candidate
                last[mask] = j

    sequence: list[Job] = []
    mask = full
    while mask:
        j = last[mask]
        sequence.append(jobs[j])
        mask ^= 1 << j
    sequence.reverse()
    return sequence, dp[full]
