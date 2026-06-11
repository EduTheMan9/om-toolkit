"""Lot-sizing API endpoints, validated against the hand-traced examples
(see tests/test_eoq.py and tests/test_dynamic_lot_sizing.py)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_eoq_endpoint_worked_example():
    response = client.post(
        "/api/lot-sizing/eoq",
        json={"demand": 1200.0, "ordering_cost": 100.0, "holding_cost": 6.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == pytest.approx(200.0)
    assert body["total_cost"] == pytest.approx(1200.0)
    assert body["ordering_cost_total"] == pytest.approx(body["holding_cost_total"])
    # cost curve for the chart: parallel arrays, same length, total = sum
    curve = body["curve"]
    assert len(curve["q"]) == len(curve["total"]) == 200
    assert curve["total"][50] == pytest.approx(
        curve["ordering"][50] + curve["holding"][50]
    )


def test_eoq_endpoint_rejects_bad_input_with_core_message():
    response = client.post(
        "/api/lot-sizing/eoq",
        json={"demand": 0.0, "ordering_cost": 100.0, "holding_cost": 6.0},
    )
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]


DYNAMIC_REQUEST = {
    "demands": [50.0, 60.0, 90.0, 70.0, 30.0, 100.0],
    "setup_cost": 150.0,
    "holding_cost": 1.0,
}


def test_dynamic_endpoint_worked_example():
    response = client.post("/api/lot-sizing/dynamic", json=DYNAMIC_REQUEST)
    assert response.status_code == 200
    body = response.json()
    plans = body["plans"]
    assert plans["wagner_whitin"]["total_cost"] == pytest.approx(640.0)
    assert plans["wagner_whitin"]["orders"] == [110.0, 0.0, 190.0, 0.0, 0.0, 100.0]
    assert plans["silver_meal"]["total_cost"] == pytest.approx(640.0)
    assert plans["lot_for_lot"]["total_cost"] == pytest.approx(900.0)
    assert plans["lot_for_lot"]["setups"] == 6
    # silver-meal narration is included for the teaching drawer
    kinds = {s["kind"] for s in body["steps"]}
    assert kinds == {"open_lot", "try_extend", "close_lot"}


def test_dynamic_endpoint_rejects_shortage_free_invalid_input():
    bad = dict(DYNAMIC_REQUEST, setup_cost=0.0)
    response = client.post("/api/lot-sizing/dynamic", json=bad)
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]
