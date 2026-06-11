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
