"""Dynamic lot sizing: period demands, setup cost S, holding cost h.

Conventions (see the Phase 4 spec): orders arrive at the start of a period,
holding is charged on end-of-period inventory, and no shortages are allowed.
So carrying demand d_k from an order in period j costs h * (k - j) * d_k.

All three methods return the same shape — an order quantity per period —
so one evaluate_plan() costs any of them, and the UI can compare them.
"""


def validate_inputs(demands: list[float], setup_cost: float, holding_cost: float) -> None:
    """Raise ValueError describing the first problem found in the input."""
    if not demands:
        raise ValueError("Need at least one period of demand.")
    if any(d < 0 for d in demands):
        raise ValueError("Demand cannot be negative.")
    if setup_cost <= 0 or holding_cost <= 0:
        raise ValueError("Setup cost and holding cost must be positive.")


def evaluate_plan(
    demands: list[float], orders: list[float], setup_cost: float, holding_cost: float
) -> dict:
    """Cost out any ordering plan: setups, holding on end-of-period inventory."""
    validate_inputs(demands, setup_cost, holding_cost)
    if len(orders) != len(demands):
        raise ValueError("Orders and demands must cover the same periods.")

    inventory = 0.0
    ending_inventory: list[float] = []
    setups = 0
    holding_total = 0.0
    for demand, order in zip(demands, orders):
        if order > 0:
            setups += 1
        inventory += order - demand
        if inventory < 0:
            raise ValueError(
                f"Shortage in period {len(ending_inventory) + 1}: "
                "orders do not cover demand."
            )
        ending_inventory.append(inventory)
        holding_total += holding_cost * inventory

    setup_total = setups * setup_cost
    return {
        "setups": setups,
        "setup_cost": setup_total,
        "holding_cost": holding_total,
        "total_cost": setup_total + holding_total,
        "ending_inventory": ending_inventory,
    }


def lot_for_lot(demands: list[float], setup_cost: float, holding_cost: float) -> list[float]:
    """Order exactly each period's demand: zero holding, a setup whenever
    demand is positive. The baseline the smarter methods are judged against."""
    validate_inputs(demands, setup_cost, holding_cost)
    return list(demands)


def _lot_cost(
    demands: list[float], j: int, t: int, setup_cost: float, holding_cost: float
) -> float:
    """c(j, t): one order in period j covering periods j..t (0-indexed).
    Demand d_k waits (k - j) periods in stock. No demand => no order needed."""
    if not any(demands[j : t + 1]):
        return 0.0
    holding = sum(holding_cost * (k - j) * demands[k] for k in range(j + 1, t + 1))
    return setup_cost + holding


def silver_meal_with_steps(
    demands: list[float], setup_cost: float, holding_cost: float
) -> tuple[list[float], list[dict]]:
    """Silver-Meal that records its own decisions while it runs, so the UI
    can replay the algorithm step by step on the user's data.
    Periods in steps are 1-based to match course notation."""
    validate_inputs(demands, setup_cost, holding_cost)
    n = len(demands)
    orders = [0.0] * n
    steps: list[dict] = []
    lot = 0
    j = 0
    while j < n:
        if demands[j] == 0:  # nothing to cover; no order, no setup
            j += 1
            continue
        lot += 1
        steps.append({"kind": "open_lot", "lot": lot, "period": j + 1})
        t = j
        avg = _lot_cost(demands, j, t, setup_cost, holding_cost)  # 1 period covered
        while t + 1 < n:
            next_avg = _lot_cost(demands, j, t + 1, setup_cost, holding_cost) / (t + 2 - j)
            decision = "stop" if next_avg >= avg else "extend"
            steps.append(
                {
                    "kind": "try_extend",
                    "lot": lot,
                    "period": t + 2,
                    "avg_current": avg,
                    "avg_extended": next_avg,
                    "decision": decision,
                }
            )
            if decision == "stop":
                break
            avg = next_avg
            t += 1
        orders[j] = sum(demands[j : t + 1])
        steps.append(
            {"kind": "close_lot", "lot": lot, "start": j + 1, "end": t + 1, "quantity": orders[j]}
        )
        j = t + 1
    return orders, steps


def silver_meal(demands: list[float], setup_cost: float, holding_cost: float) -> list[float]:
    """Extend the current lot one period at a time while the average cost
    per period covered keeps falling; stop at the first increase. Myopic —
    usually near-optimal, but not guaranteed (that's Wagner-Whitin's job)."""
    orders, _ = silver_meal_with_steps(demands, setup_cost, holding_cost)
    return orders


def wagner_whitin(demands: list[float], setup_cost: float, holding_cost: float) -> list[float]:
    """Exact DP: f(t) = min over j <= t of f(j-1) + c(j, t), i.e. the best
    plan through period t ends with one order at some j covering j..t.
    Optimal because every plan must split into such lots."""
    validate_inputs(demands, setup_cost, holding_cost)
    n = len(demands)
    best_cost = [0.0] * (n + 1)  # best_cost[t] covers the first t periods
    best_start = [0] * (n + 1)   # j of the final lot in that best plan
    for t in range(1, n + 1):
        candidates = (
            (best_cost[j] + _lot_cost(demands, j, t - 1, setup_cost, holding_cost), j)
            for j in range(t)
        )
        best_cost[t], best_start[t] = min(candidates)

    # Walk the split points backwards to recover the actual orders.
    orders = [0.0] * n
    t = n
    while t > 0:
        j = best_start[t]
        orders[j] = sum(demands[j:t])
        t = j
    return orders
