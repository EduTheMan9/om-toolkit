"""Economic Order Quantity — the classic continuous-demand trade-off.

Ordering often means many small orders (high ordering cost, low inventory);
ordering rarely means few large orders (low ordering cost, high inventory).
EOQ is the quantity where the two annual costs are equal, which minimizes
their sum: Q* = sqrt(2DS/H).
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class EOQResult:
    quantity: float            # Q*, the optimal order size
    orders_per_period: float   # D / Q*
    time_between_orders: float  # Q* / D, as a fraction of the period
    ordering_cost_total: float  # (D/Q*) * S
    holding_cost_total: float   # (Q*/2) * H — average inventory is Q/2
    total_cost: float           # ordering + holding (purchase cost excluded:
    #                             it doesn't depend on Q, so it can't change Q*)


def economic_order_quantity(
    demand: float, ordering_cost: float, holding_cost: float
) -> EOQResult:
    """All three inputs must share the same time basis (e.g. per year)."""
    if demand <= 0 or ordering_cost <= 0 or holding_cost <= 0:
        raise ValueError("Demand, ordering cost, and holding cost must be positive.")

    quantity = math.sqrt(2 * demand * ordering_cost / holding_cost)
    ordering_total = (demand / quantity) * ordering_cost
    holding_total = (quantity / 2) * holding_cost
    return EOQResult(
        quantity=quantity,
        orders_per_period=demand / quantity,
        time_between_orders=quantity / demand,
        ordering_cost_total=ordering_total,
        holding_cost_total=holding_total,
        total_cost=ordering_total + holding_total,
    )
