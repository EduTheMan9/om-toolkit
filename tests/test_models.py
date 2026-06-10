from core.line_balancing.models import Station, Task


def test_task_holds_id_duration_predecessors():
    t = Task(id="B", duration=4.0, predecessors=("A",))
    assert t.id == "B"
    assert t.duration == 4.0
    assert t.predecessors == ("A",)


def test_task_predecessors_default_to_empty():
    assert Task(id="A", duration=2.0).predecessors == ()


def test_station_total_and_idle_time():
    s = Station(index=1)
    s.tasks.extend([Task("A", 5.0), Task("B", 3.0)])
    assert s.total_time == 8.0
    assert s.idle_time(cycle_time=10.0) == 2.0
