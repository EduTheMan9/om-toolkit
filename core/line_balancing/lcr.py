"""Largest Candidate Rule.

Priority order: descending task duration (big awkward tasks placed early,
small tasks left to plug station gaps). Ties broken by lower task ID
(course convention).
"""
from .assignment import assign_in_order
from .models import Station, Task
from .precedence import validate_tasks


def largest_candidate_rule(tasks: list[Task], cycle_time: float) -> list[Station]:
    validate_tasks(tasks, cycle_time)
    candidates = sorted(tasks, key=lambda t: (-t.duration, t.id))
    return assign_in_order(candidates, cycle_time)
