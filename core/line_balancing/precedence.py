"""Input validation and precedence helpers shared by all heuristics."""
from .models import Station, Task


def validate_tasks(tasks: list[Task], cycle_time: float) -> None:
    """Raise ValueError describing the first problem found in the input."""
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task IDs in input.")
    id_set = set(ids)
    for t in tasks:
        if t.duration <= 0:
            raise ValueError(f"Task {t.id}: duration must be positive.")
        if t.duration > cycle_time:
            raise ValueError(
                f"Task {t.id}: duration {t.duration} exceeds cycle time "
                f"{cycle_time}; it can never fit in a station."
            )
        for p in t.predecessors:
            if p not in id_set:
                raise ValueError(f"Task {t.id} references unknown predecessor {p}.")
    _check_acyclic(tasks)


def _check_acyclic(tasks: list[Task]) -> None:
    # Kahn-style elimination: keep removing tasks whose predecessors are all
    # removed. If we get stuck with tasks remaining, those form a cycle.
    remaining = {t.id: set(t.predecessors) for t in tasks}
    while remaining:
        free = [tid for tid, preds in remaining.items() if not preds]
        if not free:
            raise ValueError(
                f"Circular precedence among tasks: {sorted(remaining)}"
            )
        for tid in free:
            del remaining[tid]
        for preds in remaining.values():
            preds.difference_update(free)


def eligible_tasks(tasks: list[Task], assigned_ids: set[str]) -> list[Task]:
    """Unassigned tasks whose predecessors have all been assigned."""
    return [
        t
        for t in tasks
        if t.id not in assigned_ids
        and all(p in assigned_ids for p in t.predecessors)
    ]


def fits_in_station(task: Task, station: Station, cycle_time: float) -> bool:
    return station.total_time + task.duration <= cycle_time
