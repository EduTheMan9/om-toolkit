"""Two-period productivity comparison: the display-ready composition of the
three primitives. Lives in core so the API router stays thin and the
narration steps are emitted next to the math they explain."""
from .metrics import (
    multifactor_productivity,
    productivity_change,
    single_factor_productivity,
)


def compare_periods(
    previous_output: float,
    current_output: float,
    inputs: list[tuple[str, float, float]],
) -> dict:
    """inputs = (name, previous_cost, current_cost) per factor, all in money.
    A factor with zero cost in either period has no defined ratio or change."""
    names = [name for name, _, _ in inputs]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate input names - each factor must appear once.")

    previous_costs = {name: prev for name, prev, _ in inputs}
    current_costs = {name: cur for name, _, cur in inputs}
    previous_mfp = multifactor_productivity(previous_output, previous_costs)
    current_mfp = multifactor_productivity(current_output, current_costs)
    change = productivity_change(previous_mfp, current_mfp)

    steps: list[dict] = [
        {
            "kind": "totals", "period": "previous", "output": previous_output,
            "total": sum(previous_costs.values()), "mfp": previous_mfp,
        },
        {
            "kind": "totals", "period": "current", "output": current_output,
            "total": sum(current_costs.values()), "mfp": current_mfp,
        },
        {"kind": "change", "previous": previous_mfp, "current": current_mfp, "change": change},
    ]
    factors: list[dict] = []
    for name, prev_cost, cur_cost in inputs:
        if prev_cost > 0 and cur_cost > 0:
            prev_p = single_factor_productivity(previous_output, prev_cost)
            cur_p = single_factor_productivity(current_output, cur_cost)
            factor = {
                "name": name, "previous": prev_p, "current": cur_p,
                "change": productivity_change(prev_p, cur_p),
            }
        else:
            factor = {"name": name, "previous": None, "current": None, "change": None}
        factors.append(factor)
        steps.append({"kind": "factor", **factor})

    return {
        "multifactor": {"previous": previous_mfp, "current": current_mfp, "change": change},
        "factors": factors,
        "steps": steps,
    }
