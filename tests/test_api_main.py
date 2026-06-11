"""API skeleton: health check and ValueError -> 422 mapping."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_spa_fallback_serves_index_for_client_routes(tmp_path, monkeypatch):
    """Deep links like /lot-sizing must serve the SPA's index.html."""
    import api.main as main

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "DIST_DIR", dist)

    response = client.get("/lot-sizing")
    assert response.status_code == 200
    assert "spa" in response.text
