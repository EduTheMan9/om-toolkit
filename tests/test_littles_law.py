"""Little's Law: I = R x T. Hand-checkable cases:
20 units in process at 4 units/min -> each spends 5 min (T = I/R).
"""
import pytest

from core.process_analysis.littles_law import solve_littles_law


def test_solve_inventory():
    assert solve_littles_law(flow_rate=4.0, flow_time=5.0) == pytest.approx(20.0)


def test_solve_flow_rate():
    assert solve_littles_law(inventory=20.0, flow_time=5.0) == pytest.approx(4.0)


def test_solve_flow_time():
    assert solve_littles_law(inventory=20.0, flow_rate=4.0) == pytest.approx(5.0)


def test_exactly_one_unknown_required():
    with pytest.raises(ValueError, match="exactly one"):
        solve_littles_law(inventory=20.0)
    with pytest.raises(ValueError, match="exactly one"):
        solve_littles_law(inventory=20.0, flow_rate=4.0, flow_time=5.0)


def test_known_values_must_be_positive():
    with pytest.raises(ValueError, match="positive"):
        solve_littles_law(inventory=-1.0, flow_rate=4.0)
