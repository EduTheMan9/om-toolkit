"""Process capacity analysis — hand-traced validation.

Example process (processing times in minutes per unit):
    A: 10 min x 2 servers -> capacity 2/10 = 0.2 /min
    B:  6 min x 1 server  -> capacity 1/6  = 0.1667 /min   <- bottleneck
    C:  4 min x 1 server  -> capacity 1/4  = 0.25 /min

Process capacity = 1/6 per min. With demand 0.15/min the flow rate is 0.15
(demand-constrained), so utilizations are A 75%, B 90%, C 60%.
With demand 0.2/min the process is capacity-constrained: implied
utilization of B = 0.2 / (1/6) = 120%.
"""
import pytest

from core.process_analysis.capacity import (
    bottleneck,
    capacity_steps,
    flow_rate,
    implied_utilization,
    process_capacity,
    unloaded_flow_time,
    utilization,
    validate_resources,
)
from core.process_analysis.models import Resource

RESOURCES = [
    Resource("A", processing_time=10.0, servers=2),
    Resource("B", processing_time=6.0),
    Resource("C", processing_time=4.0),
]


def test_resource_capacity_is_servers_over_processing_time():
    assert RESOURCES[0].capacity == pytest.approx(0.2)
    assert RESOURCES[1].capacity == pytest.approx(1 / 6)


def test_bottleneck_is_lowest_capacity_resource():
    assert bottleneck(RESOURCES).name == "B"


def test_bottleneck_tie_goes_to_first_in_process_order():
    tied = [Resource("X", 5.0), Resource("Y", 5.0)]
    assert bottleneck(tied).name == "X"


def test_process_capacity_is_min_resource_capacity():
    assert process_capacity(RESOURCES) == pytest.approx(1 / 6)


def test_flow_rate_is_demand_when_demand_constrained():
    assert flow_rate(RESOURCES, demand=0.15) == pytest.approx(0.15)


def test_flow_rate_is_capacity_when_capacity_constrained_or_no_demand():
    assert flow_rate(RESOURCES, demand=0.2) == pytest.approx(1 / 6)
    assert flow_rate(RESOURCES) == pytest.approx(1 / 6)


def test_utilization_per_resource():
    rate = flow_rate(RESOURCES, demand=0.15)
    assert utilization(RESOURCES[0], rate) == pytest.approx(0.75)
    assert utilization(RESOURCES[1], rate) == pytest.approx(0.90)
    assert utilization(RESOURCES[2], rate) == pytest.approx(0.60)


def test_implied_utilization_can_exceed_one():
    assert implied_utilization(RESOURCES[1], demand=0.2) == pytest.approx(1.2)


def test_unloaded_flow_time_sums_processing_times():
    assert unloaded_flow_time(RESOURCES) == pytest.approx(20.0)


def test_capacity_steps_narrate_the_worked_example():
    """The docstring trace above as recorded steps: capacities in process
    order, then the bottleneck, the flow-rate decision, and utilizations."""
    steps = capacity_steps(RESOURCES, demand=0.15)
    assert [s["kind"] for s in steps] == [
        "capacity", "capacity", "capacity", "bottleneck", "flow_rate",
        "utilization", "utilization", "utilization",
    ]
    assert steps[0] == {
        "kind": "capacity", "resource": "A", "processing_time": 10.0,
        "servers": 2, "capacity": pytest.approx(0.2),
    }
    assert steps[3] == {
        "kind": "bottleneck", "resource": "B", "capacity": pytest.approx(1 / 6),
    }
    flow = steps[4]
    assert flow["demand"] == pytest.approx(0.15)
    assert flow["rate"] == pytest.approx(0.15)
    assert flow["constraint"] == "demand"
    util_b = steps[6]
    assert util_b["resource"] == "B"
    assert util_b["utilization"] == pytest.approx(0.90)
    assert util_b["implied"] == pytest.approx(0.90)  # rate = demand here


def test_capacity_steps_without_demand_are_capacity_constrained():
    steps = capacity_steps(RESOURCES)
    flow = next(s for s in steps if s["kind"] == "flow_rate")
    assert flow["demand"] is None
    assert flow["constraint"] == "capacity"
    assert flow["rate"] == pytest.approx(1 / 6)
    utils = [s for s in steps if s["kind"] == "utilization"]
    assert utils[0]["implied"] is None
    # flow rate = bottleneck capacity -> the bottleneck runs flat out
    assert utils[1]["utilization"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "bad, message",
    [
        ([], "at least one"),
        ([Resource("", 5.0)], "name"),
        ([Resource("A", 5.0), Resource("A", 3.0)], "[Dd]uplicate"),
        ([Resource("A", 0.0)], "positive"),
        ([Resource("A", 5.0, servers=0)], "server"),
    ],
)
def test_invalid_resources_rejected(bad, message):
    with pytest.raises(ValueError, match=message):
        validate_resources(bad)
