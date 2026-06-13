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


def test_unknown_api_path_returns_json_404(tmp_path, monkeypatch):
    """An unmatched /api/* call must 404 as JSON, not fall through to the SPA
    and return index.html — otherwise the frontend gets HTML where it parses JSON."""
    import api.main as main

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>spa</html>")
    monkeypatch.setattr(main, "DIST_DIR", dist)

    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "spa" not in response.text
