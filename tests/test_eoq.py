"""EOQ — closed-form hand check.

D = 1200 units/yr, S = 100 per order, H = 6 per unit per yr:
Q* = sqrt(2*1200*100 / 6) = sqrt(40000) = 200.
Annual ordering cost = (1200/200)*100 = 600 = annual holding (200/2)*6.
"""
import pytest

from core.lot_sizing.eoq import economic_order_quantity


def test_eoq_worked_example():
    r = economic_order_quantity(demand=1200.0, ordering_cost=100.0, holding_cost=6.0)
    assert r.quantity == pytest.approx(200.0)
    assert r.orders_per_period == pytest.approx(6.0)
    assert r.time_between_orders == pytest.approx(1 / 6)
    assert r.ordering_cost_total == pytest.approx(600.0)
    assert r.holding_cost_total == pytest.approx(600.0)
    assert r.total_cost == pytest.approx(1200.0)


def test_eoq_ordering_and_holding_costs_balance_at_optimum():
    r = economic_order_quantity(demand=977.0, ordering_cost=31.0, holding_cost=2.3)
    assert r.ordering_cost_total == pytest.approx(r.holding_cost_total)


@pytest.mark.parametrize("bad", [
    {"demand": 0.0, "ordering_cost": 100.0, "holding_cost": 6.0},
    {"demand": 1200.0, "ordering_cost": -1.0, "holding_cost": 6.0},
    {"demand": 1200.0, "ordering_cost": 100.0, "holding_cost": 0.0},
])
def test_eoq_rejects_non_positive_inputs(bad):
    with pytest.raises(ValueError, match="positive"):
        economic_order_quantity(**bad)
