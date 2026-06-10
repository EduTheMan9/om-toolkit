"""The greedy station-filling loop shared by all line balancing heuristics.

Every classic heuristic (LCR, RPW, Kilbridge-Wester) is this same loop run
over a differently ordered candidate list:

    repeatedly assign the FIRST task in priority order that is unassigned,
    precedence-eligible, and fits in the open station; when none does,
    close the station and open a new one.

Restarting from the top of the list after each assignment matters: assigning
a task can unlock a higher-priority task that was precedence-blocked before.
"""
from .models import Station, Task
from .precedence import fits_in_station


def assign_in_order(ordered_tasks: list[Task], cycle_time: float) -> list[Station]:
    stations = [Station(index=1)]
    assigned: set[str] = set()
    while len(assigned) < len(ordered_tasks):
        station = stations[-1]
        pick = next(
            (
                t
                for t in ordered_tasks
                if t.id not in assigned
                and all(p in assigned for p in t.predecessors)
                and fits_in_station(t, station, cycle_time)
            ),
            None,
        )
        if pick is None:
            # Nothing fits: close this station, open the next. A valid task
            # always fits an empty station (validate_tasks guarantees
            # duration <= cycle time), so this cannot loop forever.
            stations.append(Station(index=len(stations) + 1))
        else:
            station.tasks.append(pick)
            assigned.add(pick.id)
    return stations
