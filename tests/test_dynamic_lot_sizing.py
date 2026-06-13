"""Dynamic lot sizing — hand-traced validation (see Phase 4 spec).

Demands [50, 60, 90, 70, 30, 100], S = 150, h = 1:
- Lot-for-lot: 6 setups, total 900.
- Silver-Meal: lots cover p1-2 / p3-5 / p6 -> orders [110,0,190,0,0,100],
  total 450 + 190 = 640.
- Wagner-Whitin DP: f = [150, 210, 360, 430, 490, 640] -> same plan, 640.
"""
import pytest

from core.lot_sizing.dynamic import (
    evaluate_plan,
    lot_for_lot,
    silver_meal,
    validate_inputs,
    wagner_whitin,
    wagner_whitin_backlog,
)

DEMANDS = [50.0, 60.0, 90.0, 70.0, 30.0, 100.0]
S, H = 150.0, 1.0


def test_lot_for_lot_orders_each_periods_demand():
    orders = lot_for_lot(DEMANDS, S, H)
    assert orders == DEMANDS
    cost = evaluate_plan(DEMANDS, orders, S, H)
    assert cost["setups"] == 6
    assert cost["holding_cost"] == pytest.approx(0.0)
    assert cost["total_cost"] == pytest.approx(900.0)


def test_lot_for_lot_skips_zero_demand_periods():
    orders = lot_for_lot([50.0, 0.0, 30.0], S, H)
    assert orders == [50.0, 0.0, 30.0]
    assert evaluate_plan([50.0, 0.0, 30.0], orders, S, H)["setups"] == 2


def test_silver_meal_worked_example():
    orders = silver_meal(DEMANDS, S, H)
    assert orders == [110.0, 0.0, 190.0, 0.0, 0.0, 100.0]
    cost = evaluate_plan(DEMANDS, orders, S, H)
    assert cost["holding_cost"] == pytest.approx(190.0)
    assert cost["total_cost"] == pytest.approx(640.0)


def test_wagner_whitin_worked_example_is_optimal():
    orders = wagner_whitin(DEMANDS, S, H)
    assert orders == [110.0, 0.0, 190.0, 0.0, 0.0, 100.0]
    assert evaluate_plan(DEMANDS, orders, S, H)["total_cost"] == pytest.approx(640.0)


def test_wagner_whitin_never_worse_than_silver_meal():
    ww = evaluate_plan(DEMANDS, wagner_whitin(DEMANDS, S, H), S, H)
    sm = evaluate_plan(DEMANDS, silver_meal(DEMANDS, S, H), S, H)
    assert ww["total_cost"] <= sm["total_cost"]


def test_evaluate_plan_tracks_ending_inventory():
    cost = evaluate_plan(DEMANDS, [110.0, 0.0, 190.0, 0.0, 0.0, 100.0], S, H)
    assert cost["ending_inventory"] == [60.0, 0.0, 100.0, 30.0, 0.0, 0.0]


def test_evaluate_plan_rejects_shortages():
    with pytest.raises(ValueError, match="[Ss]hortage"):
        evaluate_plan([50.0, 60.0], [50.0, 0.0], S, H)


@pytest.mark.parametrize(
    "demands, setup, holding, message",
    [
        ([], S, H, "at least one"),
        ([10.0, -5.0], S, H, "negative"),
        ([10.0], 0.0, H, "positive"),
        ([10.0], S, 0.0, "positive"),
    ],
)
def test_invalid_inputs_rejected(demands, setup, holding, message):
    with pytest.raises(ValueError, match=message):
        validate_inputs(demands, setup, holding)


# --- Backlogging --------------------------------------------------------------------
# demands [10, 0, 30], S=50, h=1, b=2. With backlog allowed the optimum is to
# produce ONCE in period 3 (qty 40), backordering period-1 demand for 2 periods:
#   setup 50 + backlog 2 * 10 * 2 periods (40) + holding 0 = 90.
# Cheaper than two setups (100) or one early setup that holds 30 for 2 periods
# (110). Hand-traced in the plan doc.
BL_DEMANDS = [10.0, 0.0, 30.0]
BL_S, BL_H, BL_B = 50.0, 1.0, 2.0


def test_evaluate_plan_costs_backorders_when_allowed():
    cost = evaluate_plan(BL_DEMANDS, [0.0, 0.0, 40.0], BL_S, BL_H, backlog_cost=BL_B)
    assert cost["setups"] == 1
    assert cost["holding_cost"] == pytest.approx(0.0)
    assert cost["backlog_cost"] == pytest.approx(40.0)
    assert cost["total_cost"] == pytest.approx(90.0)
    assert cost["ending_inventory"] == [-10.0, -10.0, 0.0]  # negative = backordered


def test_evaluate_plan_still_rejects_shortage_without_backlog_cost():
    # default backlog_cost = 0 keeps the no-shortage rule
    with pytest.raises(ValueError, match="[Ss]hortage"):
        evaluate_plan(BL_DEMANDS, [0.0, 0.0, 40.0], BL_S, BL_H)


def test_evaluate_plan_rejects_plan_that_never_covers_demand():
    with pytest.raises(ValueError, match="[Cc]over|[Bb]acklog"):
        evaluate_plan([10.0, 30.0], [10.0, 0.0], BL_S, BL_H, backlog_cost=BL_B)


def test_wagner_whitin_backlog_finds_the_backorder_optimum():
    orders = wagner_whitin_backlog(BL_DEMANDS, BL_S, BL_H, BL_B)
    assert orders == [0.0, 0.0, 40.0]
    cost = evaluate_plan(BL_DEMANDS, orders, BL_S, BL_H, backlog_cost=BL_B)
    assert cost["total_cost"] == pytest.approx(90.0)


def test_wagner_whitin_backlog_matches_classic_when_backlog_is_expensive():
    # a huge backlog penalty makes backordering never worth it, so the backlog
    # DP must reproduce the no-shortage Wagner-Whitin plan
    huge_b = 10_000.0
    assert wagner_whitin_backlog(DEMANDS, S, H, huge_b) == wagner_whitin(DEMANDS, S, H)


def test_silver_meal_with_steps_narrates_the_worked_example():
    """Hand trace: lot 1 avg 150 -> 105 (extend) -> 130 (stop);
    lot 2 avg 150 -> 110 -> 93.33 (extend twice) -> 145 (stop); lot 3 = p6."""
    from core.lot_sizing.dynamic import silver_meal_with_steps

    orders, steps = silver_meal_with_steps(DEMANDS, S, H)
    assert orders == silver_meal(DEMANDS, S, H)

    decisions = [s["decision"] for s in steps if s["kind"] == "try_extend"]
    assert decisions == ["extend", "stop", "extend", "extend", "stop"]

    closes = [
        (s["lot"], s["start"], s["end"], s["quantity"])
        for s in steps
        if s["kind"] == "close_lot"
    ]
    assert closes == [(1, 1, 2, 110.0), (2, 3, 5, 190.0), (3, 6, 6, 100.0)]

    first_try = next(s for s in steps if s["kind"] == "try_extend")
    assert first_try["avg_current"] == pytest.approx(150.0)
    assert first_try["avg_extended"] == pytest.approx(105.0)
    assert steps[0] == {"kind": "open_lot", "lot": 1, "period": 1}
