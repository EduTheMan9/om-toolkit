"""Ranked Positional Weight (Helgeson-Birnie).

A task's positional weight is its own duration plus the durations of every
task that (directly or indirectly) depends on it. Ranking by weight places
tasks that sit at the head of long work chains early, so their long tails
of followers are never left waiting at the end of the line.

Ties broken by lower task ID (course convention).
"""
from .assignment import assign_in_order
from .models import Station, Task
from .precedence import validate_tasks


def positional_weights(tasks: list[Task]) -> dict[str, float]:
    """Map task ID -> own duration + durations of all transitive followers."""
    direct_followers: dict[str, list[str]] = {t.id: [] for t in tasks}
    for t in tasks:
        for p in t.predecessors:
            direct_followers[p].append(t.id)
    durations = {t.id: t.duration for t in tasks}

    memo: dict[str, set[str]] = {}

    def all_followers(tid: str) -> set[str]:
        if tid not in memo:
            found: set[str] = set()
            for follower in direct_followers[tid]:
                found.add(follower)
                found |= all_followers(follower)
            memo[tid] = found
        return memo[tid]

    return {
        tid: durations[tid] + sum(durations[f] for f in all_followers(tid))
        for tid in durations
    }


def ranked_positional_weight(tasks: list[Task], cycle_time: float) -> list[Station]:
    validate_tasks(tasks, cycle_time)  # also guarantees the recursion above terminates
    weights = positional_weights(tasks)
    candidates = sorted(tasks, key=lambda t: (-weights[t.id], t.id))
    return assign_in_order(candidates, cycle_time)
