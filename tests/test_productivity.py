"""Productivity metrics — hand-checked (see Phase 6 spec).

500 units in 200 labor-hours -> 2.5 units/hour.
Output value $5,000 over costs $1,500 + $1,000 + $500 -> 5000/3000 = 5/3.
Labor productivity 2.0 -> 2.5 -> change (2.5 - 2.0)/2.0 = +0.25.
"""
import pytest

from core.productivity.metrics import (
    multifactor_productivity,
    productivity_change,
    single_factor_productivity,
)


def test_single_factor_worked_example():
    assert single_factor_productivity(500.0, 200.0) == pytest.approx(2.5)


def test_multifactor_worked_example():
    costs = {"Labor": 1500.0, "Materials": 1000.0, "Overhead": 500.0}
    assert multifactor_productivity(5000.0, costs) == pytest.approx(5 / 3)


def test_multifactor_with_one_input_equals_single_factor():
    assert multifactor_productivity(5000.0, {"Labor": 1500.0}) == pytest.approx(
        single_factor_productivity(5000.0, 1500.0)
    )


def test_productivity_change_worked_example():
    assert productivity_change(2.0, 2.5) == pytest.approx(0.25)


def test_productivity_change_can_be_negative():
    assert productivity_change(2.5, 2.0) == pytest.approx(-0.2)


@pytest.mark.parametrize(
    "output, input_amount",
    [(500.0, 0.0), (500.0, -1.0), (-5.0, 200.0)],
)
def test_single_factor_rejects_bad_inputs(output, input_amount):
    with pytest.raises(ValueError):
        single_factor_productivity(output, input_amount)


@pytest.mark.parametrize(
    "costs, message",
    [
        ({}, "at least one"),
        ({"Labor": -1.0}, "negative"),
        ({"Labor": 0.0, "Materials": 0.0}, "positive"),
    ],
)
def test_multifactor_rejects_bad_costs(costs, message):
    with pytest.raises(ValueError, match=message):
        multifactor_productivity(5000.0, costs)


def test_change_rejects_non_positive_previous():
    with pytest.raises(ValueError, match="positive"):
        productivity_change(0.0, 2.5)
