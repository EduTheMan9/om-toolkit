"""OEE — Overall Equipment Effectiveness, hand-checked.

Worked example (a classic OEE shift):
  planned time 420 min, downtime 30 min -> run time 390 min.
  Availability = run/planned   = 390/420 = 13/14 ≈ 0.9286.
  ideal cycle 1.0 min/unit, total count 360 ->
  Performance  = ideal·total/run = (1·360)/390 = 12/13 ≈ 0.9231.
  good 340 of 360 ->
  Quality      = good/total      = 340/360 = 17/18 ≈ 0.9444.
  OEE = A·P·Q telescopes to good/planned = 340/420 = 17/21 ≈ 0.8095.
"""
import pytest

from core.productivity.oee import oee_steps, overall_equipment_effectiveness


def test_oee_worked_example():
    r = overall_equipment_effectiveness(
        planned_time=420.0, downtime=30.0, ideal_cycle_time=1.0,
        total_count=360.0, good_count=340.0,
    )
    assert r["run_time"] == pytest.approx(390.0)
    assert r["availability"] == pytest.approx(13 / 14)
    assert r["performance"] == pytest.approx(12 / 13)
    assert r["quality"] == pytest.approx(17 / 18)
    assert r["oee"] == pytest.approx(17 / 21)


def test_oee_is_product_of_the_three_factors():
    r = overall_equipment_effectiveness(480.0, 60.0, 0.5, 800.0, 760.0)
    assert r["oee"] == pytest.approx(r["availability"] * r["performance"] * r["quality"])


def test_oee_steps_narrate_each_factor_then_the_product():
    steps = oee_steps(420.0, 30.0, 1.0, 360.0, 340.0)
    assert [s["kind"] for s in steps] == [
        "availability", "performance", "quality", "oee",
    ]
    assert steps[0]["value"] == pytest.approx(13 / 14)
    assert steps[-1]["value"] == pytest.approx(17 / 21)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        (dict(planned_time=0.0, downtime=0.0, ideal_cycle_time=1.0, total_count=10.0, good_count=10.0), "(?i)planned"),
        (dict(planned_time=420.0, downtime=420.0, ideal_cycle_time=1.0, total_count=10.0, good_count=10.0), "(?i)downtime"),
        (dict(planned_time=420.0, downtime=30.0, ideal_cycle_time=0.0, total_count=10.0, good_count=10.0), "(?i)cycle"),
        (dict(planned_time=420.0, downtime=30.0, ideal_cycle_time=1.0, total_count=0.0, good_count=0.0), "(?i)count"),
        (dict(planned_time=420.0, downtime=30.0, ideal_cycle_time=1.0, total_count=10.0, good_count=11.0), "(?i)good"),
    ],
)
def test_oee_rejects_bad_inputs(kwargs, message):
    with pytest.raises(ValueError, match=message):
        overall_equipment_effectiveness(**kwargs)


def test_oee_flags_impossible_performance_over_100_percent():
    # ideal cycle so large the "ideal" output would exceed what fits in run time
    with pytest.raises(ValueError, match="[Pp]erformance"):
        overall_equipment_effectiveness(400.0, 0.0, 2.0, 300.0, 300.0)
