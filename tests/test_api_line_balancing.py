"""Line-balancing API endpoint, validated against the shared hand-traced
example (see tests/example_problem.py and the three heuristic test files)."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SOLVE_REQUEST = {
    "tasks": [
        {"id": "A", "duration": 5},
        {"id": "B", "duration": 3, "predecessors": ["A"]},
        {"id": "C", "duration": 4, "predecessors": ["A"]},
        {"id": "D", "duration": 2, "predecessors": ["B"]},
        {"id": "E", "duration": 6, "predecessors": ["C"]},
        {"id": "F", "duration": 4, "predecessors": ["D", "E"]},
    ],
    "cycle_time": 10,
}


def test_solve_endpoint_worked_example():
    response = client.post("/api/line-balancing/solve", json=SOLVE_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["cycle_time"] == 10.0
    assert body["total_work"] == 24.0
    assert body["min_stations"] == 3
    # layout data for the precedence diagram + RPW teaching numbers
    assert body["columns"] == {"A": 1, "B": 2, "C": 2, "D": 3, "E": 3, "F": 4}
    assert body["weights"]["A"] == pytest.approx(24.0)
    h = body["heuristics"]
    assert [s["task_ids"] for s in h["lcr"]["stations"]] == [
        ["A", "C"], ["E", "B"], ["D", "F"],
    ]
    assert [s["task_ids"] for s in h["kilbridge_wester"]["stations"]] == [
        ["A", "C"], ["B", "E"], ["D", "F"],
    ]
    assert h["rpw"]["num_stations"] == 3
    assert h["rpw"]["efficiency"] == pytest.approx(0.8)
    assert h["rpw"]["balance_delay"] == pytest.approx(0.2)
    assert h["rpw"]["smoothness_index"] == pytest.approx(4.2426, abs=1e-3)
    assert h["lcr"]["stations"][0]["total_time"] == pytest.approx(9.0)
    assert h["lcr"]["stations"][0]["idle_time"] == pytest.approx(1.0)
    # RPW narration for the teaching drawer
    assert body["steps"][0]["kind"] == "rank"
    assert body["steps"][0]["order"] == ["A", "C", "E", "B", "D", "F"]


def test_solve_derives_cycle_time_from_demand():
    request = {k: v for k, v in SOLVE_REQUEST.items() if k != "cycle_time"}
    request["available_time"] = 480
    request["demand"] = 70
    response = client.post("/api/line-balancing/solve", json=request)
    assert response.status_code == 200
    # course convention: floor(480/70) = 6, so demand is always met
    assert response.json()["cycle_time"] == 6.0


def test_solve_requires_a_cycle_time_or_demand_pair():
    request = {"tasks": SOLVE_REQUEST["tasks"]}
    response = client.post("/api/line-balancing/solve", json=request)
    assert response.status_code == 422
    assert "cycle time" in response.json()["detail"].lower()


def test_solve_rejects_unknown_predecessor_with_core_message():
    bad = {
        "tasks": [{"id": "A", "duration": 5, "predecessors": ["Z"]}],
        "cycle_time": 10,
    }
    response = client.post("/api/line-balancing/solve", json=bad)
    assert response.status_code == 422
    assert "unknown predecessor" in response.json()["detail"]
