"""Optimal single-machine sequencing — hand-traced validation.

Moore-Hodgson on the shared example A(6,8) B(2,6) C(8,18) D(3,15) E(9,23):
EDD order B,A,D,C,E. B(C=2), A(C=8), D(C=11) all on time; adding C makes
C=19 > 18, so drop the longest job so far (C itself, p=8). E then finishes
at 20 <= 23. Result: B,A,D,E on time + C rejected -> only ONE tardy job
(EDD itself leaves two tardy).

Exact total-tardiness DP on A(p4,d4) B(p3,d5) C(p2,d6): EDD order A,B,C has
total tardiness 5, but A,C,B achieves 4 (A: C=4 T0, C: C=6 T0, B: C=9 T4) —
checked by enumerating all six sequences by hand. This is the classic proof
that EDD is NOT optimal for total tardiness.
"""
import pytest

from core.scheduling.dispatching import RULES, build_schedule, schedule_metrics
from core.scheduling.models import Job
from core.scheduling.optimal import (
    MAX_OPTIMAL_JOBS,
    min_total_tardiness,
    moore_hodgson,
)

JOBS = [
    Job("A", 6.0, due_date=8.0),
    Job("B", 2.0, due_date=6.0),
    Job("C", 8.0, due_date=18.0),
    Job("D", 3.0, due_date=15.0),
    Job("E", 9.0, due_date=23.0),
]


def test_moore_hodgson_minimizes_tardy_jobs():
    sequence = moore_hodgson(JOBS)
    assert [j.id for j in sequence] == ["B", "A", "D", "E", "C"]
    metrics = schedule_metrics(build_schedule(sequence), JOBS)
    assert metrics["num_tardy"] == 1  # EDD leaves 2 tardy on the same jobs


def test_moore_hodgson_all_on_time_keeps_edd_order():
    easy = [Job("X", 2.0, 10.0), Job("Y", 3.0, 20.0)]
    assert [j.id for j in moore_hodgson(easy)] == ["X", "Y"]


def test_min_total_tardiness_beats_edd_when_edd_is_suboptimal():
    jobs = [Job("A", 4.0, 4.0), Job("B", 3.0, 5.0), Job("C", 2.0, 6.0)]
    sequence, total = min_total_tardiness(jobs)
    assert [j.id for j in sequence] == ["A", "C", "B"]
    assert total == pytest.approx(4.0)
    edd = schedule_metrics(build_schedule(RULES["EDD"](jobs)), jobs)
    assert edd["avg_tardiness"] * len(jobs) == pytest.approx(5.0)


def test_min_total_tardiness_on_worked_example_matches_edd_optimum():
    # On the shared 5-job example EDD happens to be optimal (total 6);
    # the DP must find a sequence no worse than that.
    _, total = min_total_tardiness(JOBS)
    assert total == pytest.approx(6.0)


def test_min_total_tardiness_rejects_oversized_input():
    too_many = [Job(f"J{i:02d}", 1.0, 5.0) for i in range(MAX_OPTIMAL_JOBS + 1)]
    with pytest.raises(ValueError, match="jobs"):
        min_total_tardiness(too_many)
