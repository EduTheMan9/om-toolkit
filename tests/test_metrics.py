import math

import pytest

from core.line_balancing.metrics import (
    balance_delay,
    cycle_time_from_demand,
    line_efficiency,
    smoothness_index,
    theoretical_min_stations,
)
from core.line_balancing.models import Station, Task


def make_stations(*times: float) -> list[Station]:
    return [
        Station(index=i + 1, tasks=[Task(f"T{i}", time)])
        for i, time in enumerate(times)
    ]


def test_cycle_time_from_demand_rounds_down():
    # 480 min available / 70 units = 6.857... -> 6 (course convention: floor,
    # so the line is fast enough to meet demand)
    assert cycle_time_from_demand(available_time=480, demand=70) == 6


def test_cycle_time_exact_division_unchanged():
    assert cycle_time_from_demand(available_time=480, demand=60) == 8


def test_theoretical_min_stations_rounds_up():
    tasks = [Task("A", 5.0), Task("B", 4.0), Task("C", 3.0)]  # sum = 12
    assert theoretical_min_stations(tasks, cycle_time=5.0) == 3  # 12/5 = 2.4 -> 3


def test_line_efficiency():
    stations = make_stations(8.0, 4.0)  # total work 12, capacity 2 * 8 = 16
    assert line_efficiency(stations, cycle_time=8.0) == pytest.approx(0.75)


def test_balance_delay_is_complement_of_efficiency():
    stations = make_stations(8.0, 4.0)
    assert balance_delay(stations, cycle_time=8.0) == pytest.approx(0.25)


def test_smoothness_index_measured_against_cycle_time():
    # Course convention: SI = sqrt(sum((CT - station_time)^2))
    stations = make_stations(8.0, 6.0)
    expected = math.sqrt((10.0 - 8.0) ** 2 + (10.0 - 6.0) ** 2)
    assert smoothness_index(stations, cycle_time=10.0) == pytest.approx(expected)
