"""Productivity API, validated against the bakery example in
tests/test_productivity.py: 5000/3000 -> 6000/3250, change +7/65."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

REQUEST = {
    "previous_output": 5000,
    "current_output": 6000,
    "inputs": [
        {"name": "Labor", "previous": 1500, "current": 1600},
        {"name": "Materials", "previous": 1000, "current": 1150},
        {"name": "Overhead", "previous": 500, "current": 500},
    ],
}


def test_compare_endpoint_worked_example():
    response = client.post("/api/productivity/compare", json=REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["multifactor"]["previous"] == pytest.approx(5 / 3)
    assert body["multifactor"]["current"] == pytest.approx(24 / 13)
    assert body["multifactor"]["change"] == pytest.approx(7 / 65)
    assert body["factors"][0]["change"] == pytest.approx(0.125)
    assert body["steps"][0]["kind"] == "totals"
    assert body["steps"][2]["kind"] == "change"


def test_compare_zero_cost_factor_returns_nulls():
    request = {
        "previous_output": 5000, "current_output": 6000,
        "inputs": [{"name": "Labor", "previous": 1500, "current": 1600},
                   {"name": "Robot", "previous": 0, "current": 2000}],
    }
    body = client.post("/api/productivity/compare", json=request).json()
    assert body["factors"][1] == {
        "name": "Robot", "previous": None, "current": None, "change": None
    }


def test_compare_rejects_empty_inputs_with_core_message():
    request = {"previous_output": 5000, "current_output": 6000, "inputs": []}
    response = client.post("/api/productivity/compare", json=request)
    assert response.status_code == 422
    assert "at least one" in response.json()["detail"]


def test_compare_rejects_duplicate_names():
    request = {
        "previous_output": 5000, "current_output": 6000,
        "inputs": [{"name": "Labor", "previous": 1, "current": 1},
                   {"name": "Labor", "previous": 2, "current": 2}],
    }
    response = client.post("/api/productivity/compare", json=request)
    assert response.status_code == 422
    assert "uplicate" in response.json()["detail"]
