"""Largest Candidate Rule — validated against a hand-traced example.

Candidate list (descending duration, ties by lower ID):
    E(6), A(5), C(4), F(4), B(3), D(2)

Hand trace with cycle time 10:
  Station 1: E blocked (C unassigned) -> A assigned (5 left)
             E still blocked -> C assigned (1 left)
             E fits no longer (6>1), B (3>1), nothing fits -> close {A, C} = 9
  Station 2: E assigned (4 left) -> F blocked (D) -> B assigned (1 left)
             D (2>1) -> close {E, B} = 9
  Station 3: F blocked (D) -> D assigned (8 left) -> F assigned -> {D, F} = 6
"""
import pytest

from core.line_balancing.lcr import largest_candidate_rule
from core.line_balancing.models import Task
from tests.example_problem import CYCLE_TIME, TASKS, station_ids


def test_lcr_worked_example():
    stations = largest_candidate_rule(TASKS, CYCLE_TIME)
    assert station_ids(stations) == [["A", "C"], ["E", "B"], ["D", "F"]]


def test_lcr_ties_broken_by_lower_task_id():
    tasks = [Task("B", 3.0), Task("A", 3.0)]
    stations = largest_candidate_rule(tasks, cycle_time=5.0)
    # A and B tie on duration; A goes first and B no longer fits.
    assert station_ids(stations) == [["A"], ["B"]]


def test_lcr_rejects_invalid_input():
    with pytest.raises(ValueError):
        largest_candidate_rule([Task("A", 99.0)], cycle_time=10.0)
