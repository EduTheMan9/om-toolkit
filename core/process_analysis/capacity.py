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
