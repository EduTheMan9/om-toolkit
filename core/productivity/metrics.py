"""Productivity metrics: output per unit of input.

Productivity is always a ratio, never a difference - it answers "how much
do we get per unit of what we put in", which is comparable across plants,
periods, and company sizes in a way raw output never is.
"""


def single_factor_productivity(output: float, input_amount: float) -> float:
    """Output per unit of ONE input (e.g. units per labor-hour).
    Unit-agnostic: caller decides whether output/input are physical or money."""
    if input_amount <= 0:
        raise ValueError("Input amount must be positive.")
    if output < 0:
        raise ValueError("Output cannot be negative.")
    return output / input_amount


def multifactor_productivity(output_value: float, input_costs: dict[str, float]) -> float:
    """Output value per unit of combined input cost. Inputs can only be
    added when they share a unit, so everything must be in money."""
    if not input_costs:
        raise ValueError("Need at least one input cost.")
    if any(cost < 0 for cost in input_costs.values()):
        raise ValueError("Input costs cannot be negative.")
    total = sum(input_costs.values())
    if total <= 0:
        raise ValueError("Total input cost must be positive.")
    if output_value < 0:
        raise ValueError("Output value cannot be negative.")
    return output_value / total


def productivity_change(previous: float, current: float) -> float:
    """Fractional change between periods: 0.25 means +25%."""
    if previous <= 0:
        raise ValueError("Previous productivity must be positive.")
    return (current - previous) / previous
