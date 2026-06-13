"""Dispatching rules — hand-traced validation (see Phase 3 spec).

Jobs (processing time, due date): A(6,8) B(2,6) C(8,18) D(3,15) E(9,23).
Completion times and tardiness per rule are traced in the spec.
"""
import pytest

from core.scheduling.dispatching import (
    RULES,
    build_schedule,
    schedule_metrics,
    validate_jobs,
)
from core.scheduling.models import Job

JOBS = [
    Job("A", 6.0, due_date=8.0),
    Job("B", 2.0, due_date=6.0),
    Job("C", 8.0, due_date=18.0),
    Job("D", 3.0, due_date=15.0),
    Job("E", 9.0, due_date=23.0),
]


def order_of(rule_name: str) -> list[str]:
    return [j.id for j in RULES[rule_name](JOBS)]


def test_fcfs_keeps_input_order():
    assert order_of("FCFS") == ["A", "B", "C", "D", "E"]


def test_spt_sorts_by_processing_time():
    assert order_of("SPT") == ["B", "D", "A", "C", "E"]


def test_edd_sorts_by_due_date():
    assert order_of("EDD") == ["B", "A", "D", "C", "E"]


def test_lpt_sorts_by_longest_processing_time():
    assert order_of("LPT") == ["E", "C", "A", "D", "B"]


def test_sorting_ties_broken_by_lower_job_id():
    tied = [Job("Z", 4.0, 10.0), Job("Y", 4.0, 10.0)]
    assert [j.id for j in RULES["SPT"](tied)] == ["Y", "Z"]
    assert [j.id for j in RULES["EDD"](tied)] == ["Y", "Z"]


def test_build_schedule_accumulates_completion_times():
    schedule = build_schedule(RULES["SPT"](JOBS))
    assert [(s.id, s.start, s.end) for s in schedule] == [
        ("B", 0.0, 2.0),
        ("D", 2.0, 5.0),
        ("A", 5.0, 11.0),
        ("C", 11.0, 19.0),
        ("E", 19.0, 28.0),
    ]


def test_metrics_fcfs():
    m = schedule_metrics(build_schedule(RULES["FCFS"](JOBS)), JOBS)
    assert m["avg_completion_time"] == pytest.approx(15.4)
    assert m["avg_tardiness"] == pytest.approx(2.2)
    assert m["max_tardiness"] == pytest.approx(5.0)
    assert m["num_tardy"] == 3


def test_metrics_edd_minimizes_tardy_count_here():
    m = schedule_metrics(build_schedule(RULES["EDD"](JOBS)), JOBS)
    assert m["avg_tardiness"] == pytest.approx(1.2)
    assert m["num_tardy"] == 2


def test_metrics_spt_minimizes_avg_completion():
    m = schedule_metrics(build_schedule(RULES["SPT"](JOBS)), JOBS)
    assert m["avg_completion_time"] == pytest.approx(13.0)


@pytest.mark.parametrize(
    "bad, message",
    [
        ([], "at least one"),
        ([Job("", 5.0, 10.0)], "ID"),
        ([Job("A", 5.0, 10.0), Job("A", 3.0, 8.0)], "[Dd]uplicate"),
        ([Job("A", 0.0, 10.0)], "positive"),
        ([Job("A", 5.0, None)], "due date"),
        ([Job("A", 5.0, 10.0, 0.0)], "[Ww]eight"),
    ],
)
def test_invalid_jobs_rejected(bad, message):
    with pytest.raises(ValueError, match=message):
        validate_jobs(bad)


# --- WSPT (Smith's rule) and weighted metrics -------------------------------------
# Jobs (p, w): A(6,1) B(2,2) C(8,4) D(3,1) E(9,3). Ratios p/w: A6 B1 C2 D3 E3.
# WSPT order (ascending ratio, ties to lower id): B, C, D, E, A.
# Completions B2 C10 D13 E22 A28 -> weighted Σ w·C = 4+40+13+66+28 = 151.
WEIGHTED = [
    Job("A", 6.0, 8.0, 1.0),
    Job("B", 2.0, 6.0, 2.0),
    Job("C", 8.0, 18.0, 4.0),
    Job("D", 3.0, 15.0, 1.0),
    Job("E", 9.0, 23.0, 3.0),
]


def test_wspt_sorts_by_processing_over_weight():
    assert [j.id for j in RULES["WSPT"](WEIGHTED)] == ["B", "C", "D", "E", "A"]


def test_wspt_equals_spt_when_all_weights_equal():
    assert [j.id for j in RULES["WSPT"](JOBS)] == [j.id for j in RULES["SPT"](JOBS)]


def test_weighted_completion_time_metric():
    m = schedule_metrics(build_schedule(RULES["WSPT"](WEIGHTED)), WEIGHTED)
    assert m["weighted_completion_time"] == pytest.approx(151.0)


def test_max_lateness_can_be_negative_when_all_jobs_finish_early():
    # one short job, generous due date -> lateness = 5 - 100 = -95
    jobs = [Job("A", 5.0, 100.0)]
    m = schedule_metrics(build_schedule(jobs), jobs)
    assert m["max_lateness"] == pytest.approx(-95.0)
    assert m["max_tardiness"] == pytest.approx(0.0)  # tardiness floors at 0
