"""TOC product mix: the most profitable use of a shared bottleneck.

When one resource is the constraint, profit is maximized not by the product
with the highest margin per UNIT, but by the one with the highest margin per
BOTTLENECK-MINUTE — because the minute is the scarce thing being sold. Rank
products by that ratio and greedily fill the bottleneck's time up to each
product's demand.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    name: str
    contribution_margin: float  # $ per unit (price - variable cost)
    bottleneck_time: float      # minutes of the constrained resource per unit
    demand: float               # most units the market will take


def validate_products(products: list[Product], available_minutes: float) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not products:
        raise ValueError("Need at least one product.")
    names = [p.name.strip() for p in products]
    if any(not n for n in names):
        raise ValueError("Every product needs a name.")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate product names in input.")
    for p in products:
        if p.contribution_margin < 0:
            raise ValueError(f"{p.name}: contribution margin cannot be negative.")
        if p.bottleneck_time <= 0:
            raise ValueError(f"{p.name}: bottleneck time must be positive.")
        if p.demand < 0:
            raise ValueError(f"{p.name}: demand cannot be negative.")
    if available_minutes <= 0:
        raise ValueError("Available bottleneck time must be positive.")


def optimal_product_mix(products: list[Product], available_minutes: float) -> dict:
    """Rank by $/bottleneck-minute, then greedily allocate the scarce minutes.

    Returns allocations in priority order (each with units made and what
    limited them), the total contribution, and the leftover idle minutes,
    plus narration steps for the UI.
    """
    validate_products(products, available_minutes)
    # ratio = contribution per bottleneck-minute; ties to the lower name
    ranked = sorted(
        products,
        key=lambda p: (-p.contribution_margin / p.bottleneck_time, p.name),
    )
    ratios = {p.name: p.contribution_margin / p.bottleneck_time for p in ranked}

    steps: list[dict] = [
        {"kind": "rank", "order": [p.name for p in ranked], "ratios": ratios}
    ]
    allocations: list[dict] = []
    remaining = available_minutes
    total_contribution = 0.0
    for p in ranked:
        units_by_time = remaining / p.bottleneck_time
        units = min(p.demand, units_by_time)
        # demand vs capacity: which limit bit first (equal -> demand, the
        # happier reading — we made everything the market wanted)
        limited_by = "demand" if p.demand <= units_by_time else "capacity"
        minutes = units * p.bottleneck_time
        contribution = units * p.contribution_margin
        remaining -= minutes
        total_contribution += contribution
        allocations.append(
            {
                "name": p.name,
                "ratio": ratios[p.name],
                "units": units,
                "minutes": minutes,
                "contribution": contribution,
                "limited_by": limited_by,
            }
        )
        steps.append(
            {
                "kind": "allocate",
                "product": p.name,
                "ratio": ratios[p.name],
                "units": units,
                "minutes": minutes,
                "contribution": contribution,
                "remaining": remaining,
                "limited_by": limited_by,
            }
        )

    steps.append(
        {
            "kind": "total",
            "total_contribution": total_contribution,
            "idle_minutes": remaining,
        }
    )
    return {
        "allocations": allocations,
        "total_contribution": total_contribution,
        "used_minutes": available_minutes - remaining,
        "idle_minutes": remaining,
        "available_minutes": available_minutes,
        "steps": steps,
    }
