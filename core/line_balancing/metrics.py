"""Line-balance performance metrics.

Conventions follow the owner's course (see design spec):
- cycle time from demand is rounded DOWN so demand is always met
- smoothness index is measured against the cycle time, not the max station
"""
import math

from .models import Station, Task


def cycle_time_from_demand(available_time: float, demand: int) -> int:
    return math.floor(available_time / demand)


def theoretical_min_stations(tasks: list[Task], cycle_time: float) -> int:
    return math.ceil(sum(t.duration for t in tasks) / cycle_time)


def line_efficiency(stations: list[Station], cycle_time: float) -> float:
    total_work = sum(s.total_time for s in stations)
    return total_work / (len(stations) * cycle_time)


def balance_delay(stations: list[Station], cycle_time: float) -> float:
    # By definition the complement of efficiency: the share of paid
    # station time that sits idle.
    return 1.0 - line_efficiency(stations, cycle_time)


def smoothness_index(stations: list[Station], cycle_time: float) -> float:
    return math.sqrt(sum((cycle_time - s.total_time) ** 2 for s in stations))
