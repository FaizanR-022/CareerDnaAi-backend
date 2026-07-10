"""
Test Suite — app boot smoke test
Confirms the app builds cleanly and the unversioned root/health routes work.

Run: pytest tests/test_main.py
"""


def test_app_boots_and_registers_routes():
    import app.main as main_module

    assert len(main_module.app.routes) > 0


def test_root_endpoint(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["data"]["status"] == "Career Simulator API running"


def test_health_endpoint(api_client):
    r = api_client.get("/health")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["status"] == "ok"
    assert body["supabase"] in ("connected", "memory-only mode")


def test_versioned_routes_registered():
    import app.main as main_module

    # app.routes doesn't flatten included-router paths directly in this
    # FastAPI version (wraps them in an internal _IncludedRouter) — the
    # OpenAPI schema is the stable, version-proof way to check what's
    # actually registered.
    paths = main_module.app.openapi()["paths"].keys()
    assert "/api/v1/simulations" in paths
    assert "/api/v1/reports" in paths
    assert "/api/v1/auth/signin" in paths
    assert "/api/v1/users/me" in paths
