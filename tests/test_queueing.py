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


from core.process_analysis.queueing import mmc

# M/M/c at lambda=2, mu=1.5, c=2 (Erlang C):
#   a   = lambda/mu = 4/3
#   rho = a/c = 2/3
#   sum_{n=0}^{1} a^n/n! = 1 + 4/3 = 7/3
#   (a^c/c!)*(1/(1-rho)) = (16/9/2)*3 = 8/3
#   P0 = 1/(7/3 + 8/3) = 1/5 = 0.2
#   Pw = (a^c/(c!*(1-rho)))*P0 = (8/3)*0.2 = 8/15
#   Lq = Pw*rho/(1-rho) = (8/15)*2 = 16/15
#   Wq = Lq/lambda = 8/15
#   L  = Lq + a = 16/15 + 20/15 = 36/15 = 2.4
#   W  = Wq + 1/mu = 8/15 + 10/15 = 18/15 = 1.2


def test_mmc_worked_example():
    r = mmc(2.0, 1.5, 2)
    assert r["rho"] == pytest.approx(2 / 3)
    assert r["prob_wait"] == pytest.approx(8 / 15)
    assert r["Lq"] == pytest.approx(16 / 15)
    assert r["Wq"] == pytest.approx(8 / 15)
    assert r["L"] == pytest.approx(2.4)
    assert r["W"] == pytest.approx(1.2)


def test_mmc_with_one_server_matches_mm1():
    one = mmc(8.0, 10.0, 1)
    base = mm1(8.0, 10.0)
    assert one["Wq"] == pytest.approx(base["Wq"])
    assert one["L"] == pytest.approx(base["L"])


def test_mmc_rejects_bad_server_count():
    with pytest.raises(ValueError, match="whole number"):
        mmc(2.0, 1.5, 0)


def test_mmc_rejects_unstable_queue():
    with pytest.raises(ValueError, match="unstable"):
        mmc(4.0, 1.5, 2)  # a=2.667, rho=1.333 >= 1
