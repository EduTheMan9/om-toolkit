"""Johnson's rule — hand-traced validation (see Phase 3 spec).

Jobs (M1, M2): J1(3,6) J2(5,2) J3(1,2) J4(6,6) J5(7,5).
Trace: smallest time 1 (J3 on M1) -> front. Then 2 (J2 on M2) -> back.
Then 3 (J1 on M1) -> front. Then 5 (J5 on M2) -> back, before J2.
J4 fills the middle. Sequence: J3, J1, J4, J5, J2.

Machine 1 runs back to back 0-22; machine 2 waits for each job's M1 finish:
J3 1-3, J1 4-10, J4 10-16, J5 17-22, J2 22-24. Makespan 24.
"""
import pytest

from core.scheduling.johnson import (
    flow_shop_schedule,
    johnson_sequence,
    validate_flow_shop_jobs,
)
from core.scheduling.models import FlowShopJob

JOBS = [
    FlowShopJob("J1", 3.0, 6.0),
    FlowShopJob("J2", 5.0, 2.0),
    FlowShopJob("J3", 1.0, 2.0),
    FlowShopJob("J4", 6.0, 6.0),
    FlowShopJob("J5", 7.0, 5.0),
]


def test_johnson_sequence_worked_example():
    assert [j.id for j in johnson_sequence(JOBS)] == ["J3", "J1", "J4", "J5", "J2"]


def test_flow_shop_schedule_and_makespan():
    schedule = flow_shop_schedule(johnson_sequence(JOBS))
    assert [(s.id, s.start, s.end) for s in schedule.machine1] == [
        ("J3", 0.0, 1.0),
        ("J1", 1.0, 4.0),
        ("J4", 4.0, 10.0),
        ("J5", 10.0, 17.0),
        ("J2", 17.0, 22.0),
    ]
    assert [(s.id, s.start, s.end) for s in schedule.machine2] == [
        ("J3", 1.0, 3.0),
        ("J1", 4.0, 10.0),
        ("J4", 10.0, 16.0),
        ("J5", 17.0, 22.0),
        ("J2", 22.0, 24.0),
    ]
    assert schedule.makespan == pytest.approx(24.0)


def test_equal_m1_m2_time_counts_as_front():
    # a job whose own times tie goes to the front block (M1-side convention)
    jobs = [FlowShopJob("A", 4.0, 4.0), FlowShopJob("B", 5.0, 6.0)]
    assert [j.id for j in johnson_sequence(jobs)] == ["A", "B"]


def test_johnson_with_steps_narrates_the_worked_example():
    """Hand trace of the picks: 1 (J3,M1)->front slot 1; 2 (J2,M2)->back slot 5;
    3 (J1,M1)->front slot 2; 5 (J5,M2)->back slot 4; 6 (J4, tie->M1)->front slot 3."""
    from core.scheduling.johnson import johnson_sequence_with_steps

    sequence, steps = johnson_sequence_with_steps(JOBS)
    assert [j.id for j in sequence] == ["J3", "J1", "J4", "J5", "J2"]

    picks = [
        (s["job"], s["machine"], s["placement"], s["slot"])
        for s in steps
        if s["kind"] == "pick"
    ]
    assert picks == [
        ("J3", 1, "front", 1),
        ("J2", 2, "back", 5),
        ("J1", 1, "front", 2),
        ("J5", 2, "back", 4),
        ("J4", 1, "front", 3),
    ]
    assert steps[0]["time"] == pytest.approx(1.0)
    assert steps[-1] == {"kind": "done", "sequence": ["J3", "J1", "J4", "J5", "J2"]}


@pytest.mark.parametrize(
    "bad, message",
    [
        ([], "at least one"),
        ([FlowShopJob("", 1.0, 2.0)], "ID"),
        ([FlowShopJob("A", 1.0, 2.0), FlowShopJob("A", 2.0, 1.0)], "[Dd]uplicate"),
        ([FlowShopJob("A", 0.0, 2.0)], "positive"),
    ],
)
def test_invalid_flow_shop_jobs_rejected(bad, message):
    with pytest.raises(ValueError, match=message):
        validate_flow_shop_jobs(bad)
