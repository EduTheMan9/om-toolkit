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


def assign_in_order_with_steps(
    ordered_tasks: list[Task], cycle_time: float
) -> tuple[list[Station], list[dict]]:
    """The greedy loop, recording its decisions so the UI can replay them:
    each scan walks the priority list, skipping tasks that are precedence-
    blocked or don't fit, until it assigns one or closes the station.

    Closing cannot loop forever: a valid task always fits an empty station
    (validate_tasks guarantees duration <= cycle time)."""
    stations = [Station(index=1)]
    steps: list[dict] = []
    assigned: set[str] = set()
    while len(assigned) < len(ordered_tasks):
        station = stations[-1]
        remaining = cycle_time - station.total_time
        pick = None
        for t in ordered_tasks:
            if t.id in assigned:
                continue
            missing = [p for p in t.predecessors if p not in assigned]
            if missing:
                steps.append(
                    {"kind": "skip", "station": station.index, "task": t.id,
                     "reason": "blocked", "missing": missing}
                )
                continue
            if not fits_in_station(t, station, cycle_time):
                steps.append(
                    {"kind": "skip", "station": station.index, "task": t.id,
                     "reason": "no_fit", "duration": t.duration,
                     "remaining": remaining}
                )
                continue
            pick = t
            break
        if pick is None:
            steps.append(_close_step(station, cycle_time))
            stations.append(Station(index=len(stations) + 1))
        else:
            station.tasks.append(pick)
            assigned.add(pick.id)
            steps.append(
                {"kind": "assign", "station": station.index, "task": pick.id,
                 "duration": pick.duration,
                 "remaining": cycle_time - station.total_time}
            )
    steps.append(_close_step(stations[-1], cycle_time))
    return stations, steps


def _close_step(station: Station, cycle_time: float) -> dict:
    return {
        "kind": "close",
        "station": station.index,
        "tasks": [t.id for t in station.tasks],
        "total": station.total_time,
        "idle": station.idle_time(cycle_time),
    }


def assign_in_order(ordered_tasks: list[Task], cycle_time: float) -> list[Station]:
    stations, _ = assign_in_order_with_steps(ordered_tasks, cycle_time)
    return stations
