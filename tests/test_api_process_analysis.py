"""Process-analysis API endpoints, validated against the hand-traced
example in tests/test_capacity.py (A 10minx2, B 6min, C 4min; demand 0.15/min)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SOLVE_REQUEST = {
    "resources": [
        {"name": "A", "processing_time": 10, "servers": 2},
        {"name": "B", "processing_time": 6},
        {"name": "C", "processing_time": 4},
    ],
    "demand": 0.15,
}


def test_solve_endpoint_worked_example():
    response = client.post("/api/process-analysis/solve", json=SOLVE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["bottleneck"] == "B"
    assert body["process_capacity"] == pytest.approx(1 / 6)
    assert body["flow_rate"] == pytest.approx(0.15)
    assert body["constraint"] == "demand"
    assert body["unloaded_flow_time"] == pytest.approx(20.0)
    a = body["resources"][0]
    assert a["capacity"] == pytest.approx(0.2)
    assert a["utilization"] == pytest.approx(0.75)
    assert a["implied_utilization"] == pytest.approx(0.75)
    # narration for the teaching drawer
    assert body["steps"][0]["kind"] == "capacity"
    assert body["steps"][3] == {
        "kind": "bottleneck", "resource": "B", "capacity": pytest.approx(1 / 6),
    }


def test_solve_without_demand_is_capacity_constrained():
    request = {"resources": SOLVE_REQUEST["resources"]}
    response = client.post("/api/process-analysis/solve", json=request)
    assert response.status_code == 200
    body = response.json()
    assert body["constraint"] == "capacity"
    assert body["flow_rate"] == pytest.approx(1 / 6)
    assert body["resources"][0]["implied_utilization"] is None


def test_solve_rejects_duplicate_names_with_core_message():
    bad = {"resources": [{"name": "A", "processing_time": 5},
                         {"name": "A", "processing_time": 3}]}
    response = client.post("/api/process-analysis/solve", json=bad)
    assert response.status_code == 422
    assert "uplicate" in response.json()["detail"]


def test_solve_rejects_fractional_servers():
    bad = {"resources": [{"name": "A", "processing_time": 5, "servers": 1.5}]}
    response = client.post("/api/process-analysis/solve", json=bad)
    assert response.status_code == 422
    assert "whole number" in response.json()["detail"]


def test_littles_law_solves_the_missing_variable():
    response = client.post(
        "/api/process-analysis/littles-law",
        json={"inventory": 20, "flow_rate": 4},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["solved_for"] == "flow_time"
    assert body["flow_time"] == pytest.approx(5.0)
    assert body["inventory"] == pytest.approx(20.0)
    assert body["flow_rate"] == pytest.approx(4.0)


def test_littles_law_requires_exactly_one_unknown():
    response = client.post(
        "/api/process-analysis/littles-law", json={"inventory": 20}
    )
    assert response.status_code == 422
    assert "exactly one" in response.json()["detail"]


# --- TOC product mix (1500 bottleneck min; P3,P2,P1 by $/min; total $5900) ---
PRODUCT_MIX_REQUEST = {
    "products": [
        {"name": "P1", "contribution_margin": 30, "bottleneck_time": 10, "demand": 100},
        {"name": "P2", "contribution_margin": 24, "bottleneck_time": 6, "demand": 100},
        {"name": "P3", "contribution_margin": 20, "bottleneck_time": 4, "demand": 100},
    ],
    "available_minutes": 1500,
}


def test_product_mix_endpoint_worked_example():
    response = client.post("/api/process-analysis/product-mix", json=PRODUCT_MIX_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert [a["name"] for a in body["allocations"]] == ["P3", "P2", "P1"]
    assert body["total_contribution"] == pytest.approx(5900.0)
    p1 = next(a for a in body["allocations"] if a["name"] == "P1")
    assert p1["units"] == pytest.approx(50.0)  # highest unit margin, made last & partial
    assert p1["limited_by"] == "capacity"
    assert body["steps"][0]["kind"] == "rank"


def test_product_mix_rejects_nonpositive_bottleneck_time():
    bad = {**PRODUCT_MIX_REQUEST, "products": [
        {"name": "X", "contribution_margin": 10, "bottleneck_time": 0, "demand": 5},
    ]}
    response = client.post("/api/process-analysis/product-mix", json=bad)
    assert response.status_code == 422
    assert "bottleneck" in response.json()["detail"]
