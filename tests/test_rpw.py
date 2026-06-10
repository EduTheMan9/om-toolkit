"""Ranked Positional Weight (Helgeson-Birnie) — hand-traced validation.

Positional weight = own duration + durations of ALL transitive followers.
For the shared example (see tests/example_problem.py):
    A: 5 + (3+4+2+6+4) = 24      D: 2 + 4         = 6
    B: 3 + (2+4)       = 9       E: 6 + 4         = 10
    C: 4 + (6+4)       = 14      F: 4             = 4
Priority order: A(24), C(14), E(10), B(9), D(6), F(4).

Hand trace with cycle time 10:
  Station 1: A (5 left) -> C (1 left) -> E (6>1), B (3>1) -> close {A, C} = 9
  Station 2: E (4 left) -> B (1 left) -> D (2>1) -> close {E, B} = 9
  Station 3: D (8 left) -> F -> {D, F} = 6
"""
import pytest

from core.line_balancing.models import Task
from core.line_balancing.rpw import positional_weights, ranked_positional_weight
from tests.example_problem import CYCLE_TIME, TASKS, station_ids


def test_positional_weights_sum_own_and_all_followers():
    weights = positional_weights(TASKS)
    assert weights == {"A": 24.0, "B": 9.0, "C": 14.0, "D": 6.0, "E": 10.0, "F": 4.0}


def test_rpw_worked_example():
    stations = ranked_positional_weight(TASKS, CYCLE_TIME)
    assert station_ids(stations) == [["A", "C"], ["E", "B"], ["D", "F"]]


def test_rpw_rejects_invalid_input():
    with pytest.raises(ValueError):
        ranked_positional_weight([Task("A", 99.0)], cycle_time=10.0)
