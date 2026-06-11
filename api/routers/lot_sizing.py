"""Lot-sizing endpoints: EOQ and dynamic lot sizing."""
from pydantic import BaseModel

from fastapi import APIRouter

from core.lot_sizing import economic_order_quantity

router = APIRouter(prefix="/api/lot-sizing", tags=["lot-sizing"])

CURVE_POINTS = 200


class EoqRequest(BaseModel):
    demand: float
    ordering_cost: float
    holding_cost: float


class EoqCurve(BaseModel):
    q: list[float]
    ordering: list[float]
    holding: list[float]
    total: list[float]


class EoqResponse(BaseModel):
    quantity: float
    orders_per_period: float
    time_between_orders: float
    ordering_cost_total: float
    holding_cost_total: float
    total_cost: float
    curve: EoqCurve


@router.post("/eoq", response_model=EoqResponse)
def eoq(req: EoqRequest) -> EoqResponse:
    result = economic_order_quantity(req.demand, req.ordering_cost, req.holding_cost)
    # Sample TC(Q) = (D/Q)S + (Q/2)H up to 3*Q* (the interesting region; the
    # 1/Q blow-up at tiny Q is clipped by starting the range above zero).
    q_max = result.quantity * 3
    qs = [q_max * (i + 1) / CURVE_POINTS for i in range(CURVE_POINTS)]
    ordering = [(req.demand / q) * req.ordering_cost for q in qs]
    holding = [(q / 2) * req.holding_cost for q in qs]
    return EoqResponse(
        quantity=result.quantity,
        orders_per_period=result.orders_per_period,
        time_between_orders=result.time_between_orders,
        ordering_cost_total=result.ordering_cost_total,
        holding_cost_total=result.holding_cost_total,
        total_cost=result.total_cost,
        curve=EoqCurve(
            q=qs,
            ordering=ordering,
            holding=holding,
            total=[o + h for o, h in zip(ordering, holding)],
        ),
    )
