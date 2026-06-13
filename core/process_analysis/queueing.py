"""Queueing models for a single station with c parallel servers.

Three views of the same station, all unit-agnostic (rates per the same time
unit):
  - mm1 / mmc : exact Markovian results (Poisson arrivals, exponential service).
  - vut       : the variability-aware G/G/c approximation (Sakasegawa), which
                reduces to Kingman's G/G/1 formula at c=1 and to the exact M/M/1
                result when Ca=Cs=1, c=1.

The exact models are the baseline the approximation is compared against.
"""
from math import factorial, sqrt


def _check_rates(lam: float, mu: float) -> None:
    if lam <= 0 or mu <= 0:
        raise ValueError("Arrival rate and service rate must be positive.")


def _check_stable(rho: float) -> None:
    if rho >= 1:
        raise ValueError(
            f"Queue is unstable: utilization rho={rho:.3f} >= 1. "
            "The waiting line grows without bound."
        )


def mm1(lam: float, mu: float) -> dict:
    """Exact M/M/1: Poisson arrivals (rate lam), one exponential server (rate mu)."""
    _check_rates(lam, mu)
    rho = lam / mu
    _check_stable(rho)
    lq = rho**2 / (1 - rho)
    length = rho / (1 - rho)
    wq = lq / lam
    w = wq + 1 / mu
    return {"rho": rho, "Lq": lq, "L": length, "Wq": wq, "W": w, "prob_wait": rho}


def _check_servers(c: int) -> None:
    if not isinstance(c, int) or c < 1:
        raise ValueError("Number of servers must be a whole number >= 1.")


def mmc(lam: float, mu: float, c: int) -> dict:
    """Exact M/M/c via Erlang C: c identical exponential servers (rate mu each)."""
    _check_rates(lam, mu)
    _check_servers(c)
    a = lam / mu  # offered load, in Erlangs
    rho = a / c
    _check_stable(rho)
    # P0: normalising constant for the birth-death chain.
    head = sum(a**n / factorial(n) for n in range(c))
    tail = (a**c / factorial(c)) * (1 / (1 - rho))
    p0 = 1 / (head + tail)
    prob_wait = tail * p0  # Erlang C: probability an arrival has to queue
    lq = prob_wait * rho / (1 - rho)
    wq = lq / lam
    length = lq + a
    w = wq + 1 / mu
    return {
        "rho": rho, "Lq": lq, "L": length, "Wq": wq, "W": w,
        "prob_wait": prob_wait, "P0": p0,
    }
