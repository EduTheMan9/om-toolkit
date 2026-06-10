"""Shared worked example used to validate all three heuristics.

Precedence diagram (durations in parentheses), cycle time = 10:

    A(5) --> B(3) --> D(2) ----+
      \                         v
       +--> C(4) --> E(6) --> F(4)

Total work = 24, theoretical minimum stations = ceil(24/10) = 3.
Each heuristic's expected result below was traced by hand, step by step;
the trace is documented in the corresponding test file.
"""
from core.line_balancing.models import Station, Task

CYCLE_TIME = 10.0

TASKS = [
    Task("A", 5.0),
    Task("B", 3.0, ("A",)),
    Task("C", 4.0, ("A",)),
    Task("D", 2.0, ("B",)),
    Task("E", 6.0, ("C",)),
    Task("F", 4.0, ("D", "E")),
]


def station_ids(stations: list[Station]) -> list[list[str]]:
    """Stations as plain lists of task IDs, for readable assertions."""
    return [[t.id for t in s.tasks] for s in stations]
