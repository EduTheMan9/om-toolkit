"""Little's Law: inventory = flow_rate x flow_time (I = R x T).

Holds for any stable process regardless of arrival pattern or discipline,
which is what makes it the workhorse of process analysis.
"""


def solve_littles_law(
    inventory: float | None = None,
    flow_rate: float | None = None,
    flow_time: float | None = None,
) -> float:
    """Return the one missing variable given the other two."""
    known = {
        "inventory": inventory,
        "flow_rate": flow_rate,
        "flow_time": flow_time,
    }
    unknowns = [name for name, value in known.items() if value is None]
    if len(unknowns) != 1:
        raise ValueError(
            "Provide exactly two of inventory, flow_rate, flow_time "
            "(exactly one unknown)."
        )
    if any(value is not None and value <= 0 for value in known.values()):
        raise ValueError("Known values must be positive.")

    match unknowns[0]:
        case "inventory":
            return flow_rate * flow_time
        case "flow_rate":
            return inventory / flow_time
        case _:
            return inventory / flow_rate
