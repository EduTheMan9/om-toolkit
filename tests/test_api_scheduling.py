"""Scheduling API endpoints, validated against the hand-traced examples
(see tests/test_dispatching.py, tests/test_optimal.py, tests/test_johnson.py)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

DISPATCH_REQUEST = {
    "jobs": [
        {"id": "A", "processing_time": 6, "due_date": 8},
        {"id": "B", "processing_time": 2, "due_date": 6},
        {"id": "C", "processing_time": 8, "due_date": 18},
        {"id": "D", "processing_time": 3, "due_date": 15},
        {"id": "E", "processing_time": 9, "due_date": 23},
    ]
}


def test_dispatch_endpoint_worked_example():
    response = client.post("/api/scheduling/dispatch", json=DISPATCH_REQUEST)
    assert response.status_code == 200
    body = response.json()
    methods = body["methods"]
    assert methods["fcfs"]["avg_completion_time"] == pytest.approx(15.4)
    assert methods["spt"]["sequence"] == ["B", "D", "A", "C", "E"]
    assert methods["spt"]["avg_completion_time"] == pytest.approx(13.0)
    assert methods["edd"]["avg_tardiness"] == pytest.approx(1.2)
    assert methods["edd"]["num_tardy"] == 2
    assert methods["lpt"]["avg_completion_time"] == pytest.approx(20.6)
    assert methods["moore_hodgson"]["num_tardy"] == 1
    assert methods["min_total_tardiness"]["total_tardiness"] == pytest.approx(6.0)
    assert body["optimal_capped"] is False
    # timeline for the Gantt: back-to-back from t = 0
    assert methods["fcfs"]["schedule"][0] == {"id": "A", "start": 0.0, "end": 6.0}


def test_dispatch_skips_exact_dp_beyond_the_cap():
    jobs = [
        {"id": f"J{i:02d}", "processing_time": 1, "due_date": 5} for i in range(16)
    ]
    response = client.post("/api/scheduling/dispatch", json={"jobs": jobs})
    assert response.status_code == 200
    body = response.json()
    assert body["optimal_capped"] is True
    assert "min_total_tardiness" not in body["methods"]
    assert "moore_hodgson" in body["methods"]  # O(n log n), never capped


def test_dispatch_includes_wspt_and_weighted_metrics():
    # weights default to 1 if omitted -> WSPT must match SPT here
    body = client.post("/api/scheduling/dispatch", json=DISPATCH_REQUEST).json()
    assert body["methods"]["wspt"]["sequence"] == body["methods"]["spt"]["sequence"]
    # new metrics are present on every method
    assert "weighted_completion_time" in body["methods"]["fcfs"]
    assert "max_lateness" in body["methods"]["fcfs"]


def test_dispatch_wspt_reorders_under_weights():
    # C is long (8) but important (w=4): WSPT pulls it forward, SPT buries it.
    weighted = {
        "jobs": [
            {"id": "A", "processing_time": 6, "due_date": 8, "weight": 1},
            {"id": "B", "processing_time": 2, "due_date": 6, "weight": 2},
            {"id": "C", "processing_time": 8, "due_date": 18, "weight": 4},
            {"id": "D", "processing_time": 3, "due_date": 15, "weight": 1},
            {"id": "E", "processing_time": 9, "due_date": 23, "weight": 3},
        ]
    }
    body = client.post("/api/scheduling/dispatch", json=weighted).json()
    assert body["methods"]["wspt"]["sequence"] == ["B", "C", "D", "E", "A"]
    assert body["methods"]["wspt"]["weighted_completion_time"] == pytest.approx(151.0)


def test_dispatch_rejects_duplicate_ids_with_core_message():
    bad = {"jobs": [DISPATCH_REQUEST["jobs"][0], DISPATCH_REQUEST["jobs"][0]]}
    response = client.post("/api/scheduling/dispatch", json=bad)
    assert response.status_code == 422
    assert "Duplicate" in response.json()["detail"]


JOHNSON_REQUEST = {
    "jobs": [
        {"id": "J1", "time_m1": 3, "time_m2": 6},
        {"id": "J2", "time_m1": 5, "time_m2": 2},
        {"id": "J3", "time_m1": 1, "time_m2": 2},
        {"id": "J4", "time_m1": 6, "time_m2": 6},
        {"id": "J5", "time_m1": 7, "time_m2": 5},
    ]
}


def test_johnson_endpoint_worked_example():
    response = client.post("/api/scheduling/johnson", json=JOHNSON_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["sequence"] == ["J3", "J1", "J4", "J5", "J2"]
    assert body["makespan"] == pytest.approx(24.0)
    # baseline for the comparison card: run the jobs in the typed order
    assert body["input_order_makespan"] == pytest.approx(27.0)
    assert body["machine2"][0] == {"id": "J3", "start": 1.0, "end": 3.0}
    # pick narration is included for the teaching drawer
    assert body["steps"][0]["job"] == "J3"
    assert body["steps"][-1]["kind"] == "done"


def test_johnson_rejects_nonpositive_time_with_core_message():
    bad = {"jobs": [{"id": "A", "time_m1": 0, "time_m2": 2}]}
    response = client.post("/api/scheduling/johnson", json=bad)
    assert response.status_code == 422
    assert "positive" in response.json()["detail"]
