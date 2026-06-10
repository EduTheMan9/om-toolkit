import pytest

from core.line_balancing.models import Station, Task
from core.line_balancing.precedence import (
    eligible_tasks,
    fits_in_station,
    validate_tasks,
)


def test_duplicate_task_ids_rejected():
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        validate_tasks([Task("A", 1.0), Task("A", 2.0)], cycle_time=10.0)


def test_unknown_predecessor_rejected():
    with pytest.raises(ValueError, match="unknown predecessor"):
        validate_tasks([Task("A", 1.0, ("Z",))], cycle_time=10.0)


def test_non_positive_duration_rejected():
    with pytest.raises(ValueError, match="positive"):
        validate_tasks([Task("A", 0.0)], cycle_time=10.0)


def test_duration_exceeding_cycle_time_rejected():
    with pytest.raises(ValueError, match="cycle time"):
        validate_tasks([Task("A", 12.0)], cycle_time=10.0)


def test_circular_precedence_rejected():
    tasks = [Task("A", 1.0, ("B",)), Task("B", 1.0, ("A",))]
    with pytest.raises(ValueError, match="[Cc]ircular"):
        validate_tasks(tasks, cycle_time=10.0)


def test_valid_input_passes():
    tasks = [Task("A", 2.0), Task("B", 3.0, ("A",))]
    validate_tasks(tasks, cycle_time=10.0)  # must not raise


def test_eligible_tasks_respects_predecessors():
    tasks = [Task("A", 2.0), Task("B", 3.0, ("A",)), Task("C", 1.0, ("A", "B"))]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids=set())] == ["A"]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids={"A"})] == ["B"]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids={"A", "B"})] == ["C"]


def test_fits_in_station():
    s = Station(index=1, tasks=[Task("A", 7.0)])
    assert fits_in_station(Task("B", 3.0), s, cycle_time=10.0)
    assert not fits_in_station(Task("C", 4.0), s, cycle_time=10.0)
