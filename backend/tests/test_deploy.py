import base64

from fastapi.testclient import TestClient

from app.api import app as api_app
from app.deploy import BasicAuth, with_frontend


def _basic(user, password):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


def test_password_gates_everything_except_health():
    client = TestClient(BasicAuth(api_app, user="team", password="s3cret", required=True))
    assert client.get("/api/health").status_code == 200
    denied = client.get("/api/scenario")
    assert denied.status_code == 401 and denied.headers["www-authenticate"].startswith("Basic")
    assert client.get("/api/scenario", headers=_basic("team", "wrong")).status_code == 401
    assert client.get("/api/scenario", headers=_basic("other", "s3cret")).status_code == 401
    assert client.get("/api/scenario", headers={"Authorization": "Basic !!!"}).status_code == 401
    assert client.get("/api/scenario", headers=_basic("team", "s3cret")).status_code == 200


def test_required_auth_without_password_fails_closed():
    client = TestClient(BasicAuth(api_app, user="team", password="", required=True))
    assert client.get("/api/scenario", headers=_basic("team", "")).status_code == 503


def test_auth_is_off_when_neither_password_nor_requirement_is_set():
    client = TestClient(BasicAuth(api_app, user="team", password="", required=False))
    assert client.get("/api/scenario").status_code == 200


def test_frontend_is_served_beside_the_api(tmp_path):
    (tmp_path / "index.html").write_text("<div id=root></div>")
    client = TestClient(with_frontend(api_app, tmp_path))
    assert "root" in client.get("/").text
    assert client.get("/api/scenario").json()["network"]["kind"] == "synthetic"
    assert client.get("/api/jobs/missing").status_code == 404
