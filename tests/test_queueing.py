"""Queueing models, validated against hand traces.

M/M/1 at lambda=8, mu=10 (rho=0.8):
  Lq = rho^2/(1-rho) = 0.64/0.2 = 3.2
  L  = rho/(1-rho)   = 0.8/0.2  = 4.0
  Wq = Lq/lambda     = 3.2/8    = 0.4
  W  = Wq + 1/mu     = 0.4+0.1  = 0.5
  prob an arrival waits = rho = 0.8
"""
import pytest

from core.process_analysis.queueing import mm1


def test_mm1_worked_example():
    r = mm1(8.0, 10.0)
    assert r["rho"] == pytest.approx(0.8)
    assert r["Lq"] == pytest.approx(3.2)
    assert r["L"] == pytest.approx(4.0)
    assert r["Wq"] == pytest.approx(0.4)
    assert r["W"] == pytest.approx(0.5)
    assert r["prob_wait"] == pytest.approx(0.8)


def test_mm1_rejects_unstable_queue():
    with pytest.raises(ValueError, match="unstable"):
        mm1(10.0, 8.0)  # rho = 1.25 >= 1


def test_mm1_rejects_nonpositive():
    with pytest.raises(ValueError, match="positive"):
        mm1(0.0, 10.0)
