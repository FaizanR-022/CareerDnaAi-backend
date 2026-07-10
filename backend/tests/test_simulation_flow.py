"""
Test Suite — full simulation + report flow, real HTTP layer, real Supabase
Everything I've manually verified live throughout this project, turned into
permanent, automated tests: start -> submit -> next-scene -> ... ->
completed -> generate report, plus every guard the service layer enforces.

Run: pytest tests/test_simulation_flow.py
"""


def _walk_to_completion(api_client, auth_headers, domain="product_manager"):
    """Drives one simulation to completion, returns the session_id."""
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": domain, "difficulty": "medium"},
    )
    assert r.status_code == 201, r.text
    session_id = r.json()["data"]["session_id"]
    scene_number = r.json()["data"]["scene"]["scene_number"]

    while True:
        r = api_client.post(
            f"/api/v1/simulations/{session_id}/scenes/{scene_number}/responses",
            headers=auth_headers,
            json={"response": {"raw_text": "a thoughtful, detailed clarifying response"}},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        if data["is_final_scene"]:
            break
        r = api_client.post(f"/api/v1/simulations/{session_id}/scenes", headers=auth_headers)
        assert r.status_code == 200, r.text
        scene_number = r.json()["data"]["scene"]["scene_number"]

    return session_id


def test_full_simulation_walkthrough(api_client, auth_headers):
    session_id = _walk_to_completion(api_client, auth_headers)

    r = api_client.get(f"/api/v1/simulations/{session_id}", headers=auth_headers)
    assert r.status_code == 200
    state = r.json()["data"]
    assert state["status"] == "completed"
    assert all(s["evaluated"] for s in state["scenes"])

    r = api_client.get(f"/api/v1/simulations/{session_id}/scenes/current", headers=auth_headers)
    assert r.status_code == 200

    r = api_client.get("/api/v1/simulations", headers=auth_headers)
    assert r.status_code == 200
    assert any(s["id"] == session_id for s in r.json()["data"])


def test_submit_response_rejects_wrong_scene_number(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": "product_manager", "difficulty": "medium"},
    )
    session_id = r.json()["data"]["session_id"]

    r = api_client.post(
        f"/api/v1/simulations/{session_id}/scenes/999/responses",
        headers=auth_headers, json={"response": {"raw_text": "x"}},
    )
    assert r.status_code == 409
    assert r.json()["success"] is False


def test_double_submit_rejected(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": "product_manager", "difficulty": "medium"},
    )
    session_id = r.json()["data"]["session_id"]

    body = {"response": {"raw_text": "first response"}}
    r1 = api_client.post(
        f"/api/v1/simulations/{session_id}/scenes/1/responses", headers=auth_headers, json=body
    )
    assert r1.status_code == 200

    r2 = api_client.post(
        f"/api/v1/simulations/{session_id}/scenes/1/responses", headers=auth_headers, json=body
    )
    assert r2.status_code == 409


def test_next_scene_before_evaluation_rejected(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": "product_manager", "difficulty": "medium"},
    )
    session_id = r.json()["data"]["session_id"]

    r = api_client.post(f"/api/v1/simulations/{session_id}/scenes", headers=auth_headers)
    assert r.status_code == 409


def test_next_scene_after_completion_rejected(api_client, auth_headers):
    session_id = _walk_to_completion(api_client, auth_headers)

    r = api_client.post(f"/api/v1/simulations/{session_id}/scenes", headers=auth_headers)
    assert r.status_code == 409


def test_cross_user_access_forbidden(api_client, auth_headers, e2e_user):
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": "product_manager", "difficulty": "medium"},
    )
    session_id = r.json()["data"]["session_id"]

    from app.services import auth_service
    import uuid
    other = auth_service.signup({
        "email": f"pytest-e2e-other-{uuid.uuid4().hex[:12]}@example.com",
        "password": "another-long-password",
        "full_name": "Other User",
        "university": "", "degree": "", "graduation_year": None, "core_interests": [],
    })
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    r = api_client.get(f"/api/v1/simulations/{session_id}", headers=other_headers)
    assert r.status_code == 403

    from app.db.client import get_supabase
    get_supabase().table("users").delete().eq("id", other["user"]["id"]).execute()


def test_unauthenticated_request_rejected(api_client):
    r = api_client.get("/api/v1/simulations")
    assert r.status_code == 401


# ─── report generation ──────────────────────────────────────────────────

def test_generate_report_on_incomplete_session_returns_400(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/simulations", headers=auth_headers,
        json={"domain": "product_manager", "difficulty": "medium"},
    )
    session_id = r.json()["data"]["session_id"]

    r = api_client.post(
        "/api/v1/reports", headers=auth_headers, json={"simulation_session_ids": [session_id]}
    )
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_generate_report_on_nonexistent_session_returns_404(api_client, auth_headers):
    r = api_client.post(
        "/api/v1/reports", headers=auth_headers,
        json={"simulation_session_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert r.status_code == 404


def test_full_report_generation_flow(api_client, auth_headers):
    session_id = _walk_to_completion(api_client, auth_headers)

    r = api_client.post(
        "/api/v1/reports", headers=auth_headers, json={"simulation_session_ids": [session_id]}
    )
    assert r.status_code == 201, r.text
    report = r.json()["data"]
    assert report["simulation_session_ids"] == [session_id]
    assert report["top_recommendation"] in report["ranked_domains"]
    assert len(report["ranked_domains"]) == 5

    report_id = report["id"]

    r = api_client.get("/api/v1/reports", headers=auth_headers)
    assert r.status_code == 200
    assert any(rep["id"] == report_id for rep in r.json()["data"])

    r = api_client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["id"] == report_id


def test_report_evidence_citations_point_at_real_evaluation_ids(api_client, auth_headers):
    session_id = _walk_to_completion(api_client, auth_headers)

    from app.repositories import scene_evaluations, simulation_scenes
    scenes = simulation_scenes.list_scenes(session_id)
    real_eval_ids = {e["id"] for e in scene_evaluations.list_evaluations_for_scenes(
        [s["id"] for s in scenes]
    )}

    r = api_client.post(
        "/api/v1/reports", headers=auth_headers, json={"simulation_session_ids": [session_id]}
    )
    assert r.status_code == 201
    citations = r.json()["data"]["evidence_citations"]
    cited_ids = {cid for ids in citations.values() for cid in ids}
    assert cited_ids <= real_eval_ids
