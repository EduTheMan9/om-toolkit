"""Kilbridge-Wester — hand-traced validation.

Column = position in the precedence diagram: tasks with no predecessors are
column 1; otherwise 1 + max(column of predecessors).
For the shared example: A:1, B:2, C:2, D:3, E:3, F:4.

Priority order (by column, then largest duration, then lower ID):
    A | C(4), B(3) | E(6), D(2) | F  ->  A, C, B, E, D, F

Hand trace with cycle time 10:
  Station 1: A (5 left) -> C (1 left) -> B (3>1), E blocked anyway
             -> close {A, C} = 9
  Station 2: B (7 left) -> E (1 left) -> D (2>1) -> close {B, E} = 9
  Station 3: D (8 left) -> F -> {D, F} = 6

Note station 2 is {B, E} here vs {E, B} under LCR/RPW: same grouping can be
reached in different assignment order by different heuristics.
"""
import pytest

from core.line_balancing.kilbridge_wester import kilbridge_columns, kilbridge_wester
from core.line_balancing.models import Task
from tests.example_problem import CYCLE_TIME, TASKS, station_ids


def test_columns_follow_precedence_depth():
    assert kilbridge_columns(TASKS) == {"A": 1, "B": 2, "C": 2, "D": 3, "E": 3, "F": 4}


def test_kilbridge_wester_worked_example():
    stations = kilbridge_wester(TASKS, CYCLE_TIME)
    assert station_ids(stations) == [["A", "C"], ["B", "E"], ["D", "F"]]


def test_kw_rejects_invalid_input():
    with pytest.raises(ValueError):
        kilbridge_wester([Task("A", 99.0)], cycle_time=10.0)
