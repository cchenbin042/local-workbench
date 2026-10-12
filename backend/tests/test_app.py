import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(config):
    from workbench.app import create_app

    with TestClient(create_app(config), base_url="http://127.0.0.1:8765") as client:
        yield client


def test_health_and_local_origin(client, config):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health", headers={"Origin": "https://example.test"}).status_code == 403
    assert client.get("/api/health", headers={"Host": "example.test:8765"}).status_code == 403
    assert not config.state_path.exists()


@pytest.mark.parametrize("host", ["127.0.0.1:8765", "localhost:8765"])
def test_local_hosts_are_accepted(client, host):
    assert client.get("/api/health", headers={"Host": host}).status_code == 200


@pytest.mark.parametrize("host", ["127.0.0.1:80", "localhost.evil:8765", "127.0.0.1:8765@evil", "", "127.0.0.2:8765"])
def test_invalid_hosts_are_rejected(client, host):
    response = client.get("/api/health", headers={"Host": host})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LOCAL_ACCESS_DENIED"


def test_duplicate_host_is_rejected(client):
    assert client.get("/api/health", headers=[("Host", "127.0.0.1:8765"), ("Host", "evil.test")]).status_code == 403


@pytest.mark.parametrize("origin", ["null", "https://localhost:8765", "http://localhost:8765/", "http://localhost:5174", "http://localhost:5173.evil", ""])
def test_invalid_origins_are_rejected(client, origin):
    assert client.get("/api/health", headers={"Origin": origin}).status_code == 403


def test_local_preflight_and_duplicate_origin(client):
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"}
    response = client.options("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert client.options("/api/health", headers={**headers, "Origin": "https://evil.test"}).status_code == 403
    assert client.get("/api/health", headers=[("Origin", "http://localhost:5173"), ("Origin", "https://evil.test")]).status_code == 403


def test_custom_port_is_used(tmp_path):
    from workbench.app import create_app
    from workbench.config import AppConfig

    with TestClient(create_app(AppConfig(app_root=tmp_path, port=9123)), base_url="http://127.0.0.1:9123") as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/health", headers={"Origin": "http://localhost:9123"}).status_code == 200
        assert client.get("/api/health", headers={"Host": "localhost:8765"}).status_code == 403


def test_openapi_and_structured_errors(client):
    from workbench.errors import WorkbenchError

    @client.app.get("/test-error", include_in_schema=False)
    def fail():
        raise WorkbenchError("WORKSPACE_NOT_FOUND", "工作区不存在", 404)

    assert "/api/health" in client.get("/openapi.json").json()["paths"]
    response = client.get("/test-error")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "WORKSPACE_NOT_FOUND", "message": "工作区不存在"}}
    assert client.get("/missing").json()["error"]["code"] == "HTTP_ERROR"


def test_validation_error_does_not_echo_input(client, valid_task_input):
    from workbench.contracts import TaskCreate

    @client.app.post("/test-contract", include_in_schema=False)
    def contract(request: TaskCreate):
        return request

    response = client.post("/test-contract", json={**valid_task_input, "apiKey": "secret-must-not-echo"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert "secret-must-not-echo" not in response.text
