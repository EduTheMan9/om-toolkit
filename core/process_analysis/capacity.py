"""Capacity analysis: bottleneck, flow rate, utilization."""
from .models import Resource


def validate_resources(resources: list[Resource]) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not resources:
        raise ValueError("A process needs at least one resource.")
    names = [r.name.strip() for r in resources]
    if any(not n for n in names):
        raise ValueError("Every resource needs a name.")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate resource names in input.")
    for r in resources:
        if r.processing_time <= 0:
            raise ValueError(f"Resource {r.name}: processing time must be positive.")
        if r.servers < 1:
            raise ValueError(f"Resource {r.name}: needs at least one server.")


def bottleneck(resources: list[Resource]) -> Resource:
    """The lowest-capacity resource; ties go to the first in process order."""
    return min(resources, key=lambda r: r.capacity)


def process_capacity(resources: list[Resource]) -> float:
    return bottleneck(resources).capacity


def flow_rate(resources: list[Resource], demand: float | None = None) -> float:
    """Actual throughput: the process can't do more than its bottleneck,
    and won't do more than demand asks for."""
    capacity = process_capacity(resources)
    return capacity if demand is None else min(demand, capacity)


def utilization(resource: Resource, rate: float) -> float:
    return rate / resource.capacity


def implied_utilization(resource: Resource, demand: float) -> float:
    """Demand relative to capacity — unlike utilization, this may exceed 1,
    showing how overloaded a resource WOULD be if demand had to be met."""
    return demand / resource.capacity


def unloaded_flow_time(resources: list[Resource]) -> float:
    """Time one unit spends in an empty process (no queueing): the sum of
    processing times along the line."""
    return sum(r.processing_time for r in resources)


def capacity_steps(resources: list[Resource], demand: float | None = None) -> list[dict]:
    """Narrate the capacity analysis as structured steps for the UI player,
    in the order you'd compute it by hand: each resource's capacity, the
    minimum (bottleneck), the flow-rate decision, then utilizations."""
    validate_resources(resources)
    steps: list[dict] = [
        {
            "kind": "capacity",
            "resource": r.name,
            "processing_time": r.processing_time,
            "servers": r.servers,
            "capacity": r.capacity,
        }
        for r in resources
    ]
    bn = bottleneck(resources)
    steps.append({"kind": "bottleneck", "resource": bn.name, "capacity": bn.capacity})
    rate = flow_rate(resources, demand)
    constrained_by_demand = demand is not None and demand < bn.capacity
    steps.append(
        {
            "kind": "flow_rate",
            "capacity": bn.capacity,
            "demand": demand,
            "rate": rate,
            "constraint": "demand" if constrained_by_demand else "capacity",
        }
    )
    for r in resources:
        steps.append(
            {
                "kind": "utilization",
                "resource": r.name,
                "utilization": utilization(r, rate),
                "implied": None if demand is None else implied_utilization(r, demand),
            }
        )
    return steps
