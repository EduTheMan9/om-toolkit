"""Kilbridge-Wester column heuristic.

Unlike LCR/RPW, the ranking is structural rather than score-based: tasks are
grouped into the COLUMNS of the precedence diagram (how many precedence
levels deep they sit) and assigned column by column, left to right — work
near the start of the diagram is consumed first. Within a column: largest
duration first, ties by lower task ID (course convention).
"""
from .assignment import assign_in_order
from .models import Station, Task
from .precedence import validate_tasks


def kilbridge_columns(tasks: list[Task]) -> dict[str, int]:
    """Map task ID -> column: 1 for tasks with no predecessors, else
    1 + the deepest column among its predecessors."""
    columns: dict[str, int] = {}
    pending = list(tasks)
    while pending:
        ready = [t for t in pending if all(p in columns for p in t.predecessors)]
        for t in ready:
            columns[t.id] = 1 + max(
                (columns[p] for p in t.predecessors), default=0
            )
        pending = [t for t in pending if t.id not in columns]
    return columns


def kilbridge_wester(tasks: list[Task], cycle_time: float) -> list[Station]:
    validate_tasks(tasks, cycle_time)  # acyclic input keeps the column loop finite
    columns = kilbridge_columns(tasks)
    candidates = sorted(tasks, key=lambda t: (columns[t.id], -t.duration, t.id))
    return assign_in_order(candidates, cycle_time)
