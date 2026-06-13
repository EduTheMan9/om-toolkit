"""OEE — Overall Equipment Effectiveness.

The standard equipment KPI: OEE = Availability x Performance x Quality, where
each factor is a fraction of the loss-free ideal.

  Availability = run time / planned time        (how much of the plan we ran)
  Performance  = ideal cycle x total count / run time  (how fast vs the ideal)
  Quality      = good count / total count        (how much we made right)

The three multiply because they are independent losses stacked on the same
planned time: stop losses, speed losses, then defect losses.
"""


def _validate(
    planned_time: float, downtime: float, ideal_cycle_time: float,
    total_count: float, good_count: float,
) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if planned_time <= 0:
        raise ValueError("Planned production time must be positive.")
    if downtime < 0 or downtime >= planned_time:
        raise ValueError("Downtime must be between 0 and the planned time.")
    if ideal_cycle_time <= 0:
        raise ValueError("Ideal cycle time must be positive.")
    if total_count <= 0:
        raise ValueError("Total count must be positive.")
    if good_count < 0 or good_count > total_count:
        raise ValueError("Good count must be between 0 and the total count.")
    # The "ideal" output can never need more than the run time we actually had;
    # if it does, the ideal cycle time or the count is wrong, not a real >100%.
    if ideal_cycle_time * total_count > planned_time - downtime:
        raise ValueError(
            "Performance exceeds 100%: ideal cycle time x total count is more "
            "than the run time — check the cycle time or counts."
        )


def overall_equipment_effectiveness(
    planned_time: float, downtime: float, ideal_cycle_time: float,
    total_count: float, good_count: float,
) -> dict:
    """The three factors and their product. All times share one unit."""
    _validate(planned_time, downtime, ideal_cycle_time, total_count, good_count)
    run_time = planned_time - downtime
    availability = run_time / planned_time
    performance = (ideal_cycle_time * total_count) / run_time
    quality = good_count / total_count
    return {
        "run_time": run_time,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": availability * performance * quality,
    }


def oee_steps(
    planned_time: float, downtime: float, ideal_cycle_time: float,
    total_count: float, good_count: float,
) -> list[dict]:
    """Narrate the three factors in computation order, then the product, so
    the UI can replay how each loss whittles the planned time down."""
    r = overall_equipment_effectiveness(
        planned_time, downtime, ideal_cycle_time, total_count, good_count
    )
    return [
        {
            "kind": "availability", "planned_time": planned_time,
            "downtime": downtime, "run_time": r["run_time"],
            "value": r["availability"],
        },
        {
            "kind": "performance", "ideal_cycle_time": ideal_cycle_time,
            "total_count": total_count, "run_time": r["run_time"],
            "value": r["performance"],
        },
        {
            "kind": "quality", "good_count": good_count,
            "total_count": total_count, "value": r["quality"],
        },
        {
            "kind": "oee", "availability": r["availability"],
            "performance": r["performance"], "quality": r["quality"],
            "value": r["oee"],
        },
    ]
