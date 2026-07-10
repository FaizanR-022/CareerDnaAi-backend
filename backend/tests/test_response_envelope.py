"""
Test Suite — app.core.response_envelope
Success wrapping, all three error-handler shapes, status codes. Uses the
built-in /health and / routes (always present, no auth) plus a couple of
deliberately-triggered error paths — no real DB needed for this file.

Run: pytest tests/test_response_envelope.py
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.response_envelope import register_response_envelope


def _tiny_app() -> FastAPI:
    """An isolated app so these tests don't depend on the real app's routes
    or auth — just the envelope/error-handling behavior itself."""
    app = FastAPI()
    register_response_envelope(app)

    class Item(BaseModel):
        name: str

    @app.get("/ok")
    def ok():
        return {"foo": "bar"}

    @app.post("/ok", status_code=201)
    def created(item: Item):
        return {"name": item.name}

    @app.get("/not-found")
    def not_found():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Thing not found")

    @app.get("/boom")
    def boom():
        raise RuntimeError("sensitive internal detail that must not leak")

    return app


def _client() -> TestClient:
    return TestClient(_tiny_app(), raise_server_exceptions=False)


def test_success_response_wrapped():
    r = _client().get("/ok")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"] == {"foo": "bar"}


def test_success_response_preserves_custom_status_code():
    r = _client().post("/ok", json={"name": "widget"})
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"] == {"name": "widget"}


def test_http_exception_wrapped_as_error():
    r = _client().get("/not-found")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error"]["message"] == "Thing not found"
    assert body["error"]["status_code"] == 404


def test_validation_error_wrapped():
    r = _client().post("/ok", json={"wrong_field": 123})
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"]["status_code"] == 422
    assert "details" in body["error"]
    assert isinstance(body["error"]["details"], list)


def test_unhandled_exception_returns_safe_generic_message():
    r = _client().get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["success"] is False
    assert body["error"]["message"] == "Internal server error"
    assert "sensitive" not in r.text


def test_real_app_health_endpoint_wrapped():
    import app.main as main_module

    r = TestClient(main_module.app).get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
