"""TOC product mix — hand-traced.

Theory of Constraints: with a shared bottleneck, the profit-maximizing mix
ranks products by contribution margin PER BOTTLENECK-MINUTE, not by margin
per unit. The seductive-but-wrong move is to favor the highest unit margin.

Worked example — 1500 bottleneck minutes available:
  P1: margin $30/u, 10 min/u, demand 100 -> $3.0 per min
  P2: margin $24/u,  6 min/u, demand 100 -> $4.0 per min
  P3: margin $20/u,  4 min/u, demand 100 -> $5.0 per min
Rank by $/min desc: P3, P2, P1.
  P3: make 100 (demand) -> 400 min, $2000, 1100 min left
  P2: make 100 (demand) -> 600 min, $2400,  500 min left
  P1: only 500 min left / 10 = make 50 of 100 -> $1500, 0 left
Total contribution = $5900. P1 — the highest UNIT margin — is made last and
only half, because per scarce minute it is the worst.
"""
import pytest

from core.process_analysis.product_mix import Product, optimal_product_mix

PRODUCTS = [
    Product("P1", contribution_margin=30.0, bottleneck_time=10.0, demand=100.0),
    Product("P2", contribution_margin=24.0, bottleneck_time=6.0, demand=100.0),
    Product("P3", contribution_margin=20.0, bottleneck_time=4.0, demand=100.0),
]


def test_ranks_by_contribution_per_bottleneck_minute():
    result = optimal_product_mix(PRODUCTS, available_minutes=1500.0)
    assert [a["name"] for a in result["allocations"]] == ["P3", "P2", "P1"]


def test_total_contribution_and_partial_last_product():
    result = optimal_product_mix(PRODUCTS, available_minutes=1500.0)
    assert result["total_contribution"] == pytest.approx(5900.0)
    assert result["idle_minutes"] == pytest.approx(0.0)
    by_name = {a["name"]: a for a in result["allocations"]}
    assert by_name["P3"]["units"] == pytest.approx(100.0)
    assert by_name["P1"]["units"] == pytest.approx(50.0)        # capacity-limited
    assert by_name["P1"]["limited_by"] == "capacity"
    assert by_name["P3"]["limited_by"] == "demand"


def test_slack_capacity_meets_all_demand():
    # 3000 min easily covers all demand (needs 400+600+1000 = 2000)
    result = optimal_product_mix(PRODUCTS, available_minutes=3000.0)
    assert all(a["units"] == pytest.approx(100.0) for a in result["allocations"])
    assert result["idle_minutes"] == pytest.approx(1000.0)
    assert result["total_contribution"] == pytest.approx(7400.0)


def test_steps_rank_then_allocate_then_total():
    steps = optimal_product_mix(PRODUCTS, available_minutes=1500.0)["steps"]
    assert steps[0]["kind"] == "rank"
    assert steps[0]["order"] == ["P3", "P2", "P1"]
    assert [s["kind"] for s in steps[1:4]] == ["allocate", "allocate", "allocate"]
    assert steps[-1]["kind"] == "total"
    assert steps[-1]["total_contribution"] == pytest.approx(5900.0)


@pytest.mark.parametrize(
    "products, available, message",
    [
        ([], 1000.0, "at least one"),
        ([Product("", 10.0, 5.0, 10.0)], 1000.0, "name"),
        ([Product("A", 10.0, 5.0, 10.0), Product("A", 1.0, 1.0, 1.0)], 1000.0, "[Dd]uplicate"),
        ([Product("A", 10.0, 0.0, 10.0)], 1000.0, "bottleneck"),
        ([Product("A", 10.0, 5.0, 10.0)], 0.0, "(?i)available"),
    ],
)
def test_rejects_bad_inputs(products, available, message):
    with pytest.raises(ValueError, match=message):
        optimal_product_mix(products, available)
