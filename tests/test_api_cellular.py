"""Cellular API endpoint, validated against the hand-traced Example A
(tests/test_cells.py): ROC orders M1,M3,M2,M4 / P1,P4,P2,P3,P5; 2 cells;
e = 9, 0 exceptional, 1 void -> grouping efficacy 0.9."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

MATRIX_A = [
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 1],
    [1, 0, 0, 1, 0],
    [0, 1, 1, 0, 0],
]


def test_solve_endpoint_worked_example():
    response = client.post("/api/cellular/solve", json={"matrix": MATRIX_A})
    assert response.status_code == 200
    body = response.json()
    assert body["matrix"] == MATRIX_A  # echoed for consistent rendering
    assert body["row_order"] == [0, 2, 1, 3]
    assert body["col_order"] == [0, 3, 1, 2, 4]
    assert body["iterations"] == 2
    assert body["machine_cells"] == [0, 1, 0, 1]
    assert body["part_cells"] == [0, 1, 1, 0, 1]
    assert body["n_cells"] == 2
    assert body["exceptional"] == 0
    assert body["voids"] == 1
    assert body["grouping_efficacy"] == pytest.approx(0.9)
    # narration for the teaching drawer
    assert body["steps"][0]["kind"] == "rows"
    assert body["steps"][0]["values"] == [18, 13, 18, 12]
    assert body["steps"][-1]["kind"] == "efficacy"


def test_solve_rejects_non_binary_matrix_with_core_message():
    response = client.post("/api/cellular/solve", json={"matrix": [[1, 2], [0, 1]]})
    assert response.status_code == 422
    assert "0 or 1" in response.json()["detail"]


def test_solve_rejects_zero_row_with_core_message():
    response = client.post("/api/cellular/solve", json={"matrix": [[1, 1], [0, 0]]})
    assert response.status_code == 422
    assert "processes no parts" in response.json()["detail"]


def test_solve_rejects_oversized_instances():
    # 17 machines x 1 part: valid matrix, but past the exact-search cap
    response = client.post("/api/cellular/solve", json={"matrix": [[1]] * 17})
    assert response.status_code == 422
    assert "16" in response.json()["detail"]
