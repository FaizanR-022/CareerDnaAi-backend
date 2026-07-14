"""
Test Suite — Pydantic schema validators
Field constraints and custom validators on request schemas. No DB.

Run: pytest tests/test_schemas.py
"""
import pytest
from pydantic import ValidationError

from app.schemas.agent_contracts import EvaluationResult, NpcStateUpdate, QuestionScore
from app.schemas.auth import SignupRequest
from app.schemas.user import OnboardingRequest, UpdateUserRequest


# ─── schemas/auth.py ─────────────────────────────────────────────────────

def test_signup_request_normalizes_email_case_and_whitespace():
    req = SignupRequest(
        full_name="Jane Doe", email="  Jane@Example.COM  ", password="a-long-password",
    )
    assert req.email == "jane@example.com"


def test_signup_request_rejects_short_password():
    with pytest.raises(ValidationError):
        SignupRequest(full_name="Jane Doe", email="jane@example.com", password="short")


def test_signup_request_rejects_oversized_bcrypt_password():
    with pytest.raises(ValidationError):
        SignupRequest(full_name="Jane Doe", email="jane@example.com", password="a" * 73)


def test_signup_request_rejects_empty_core_interest():
    with pytest.raises(ValidationError):
        SignupRequest(
            full_name="Jane Doe", email="jane@example.com", password="a-long-password",
            core_interests=["backend", "   "],
        )


def test_signup_request_rejects_too_many_core_interests():
    with pytest.raises(ValidationError):
        SignupRequest(
            full_name="Jane Doe", email="jane@example.com", password="a-long-password",
            core_interests=[f"interest-{i}" for i in range(11)],
        )


def test_signup_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        SignupRequest(full_name="Jane Doe", email="not-an-email", password="a-long-password")


def test_signup_request_rejects_graduation_year_out_of_range():
    with pytest.raises(ValidationError):
        SignupRequest(
            full_name="Jane Doe", email="jane@example.com", password="a-long-password",
            graduation_year=1900,
        )


# ─── schemas/user.py ──────────────────────────────────────────────────────

def test_onboarding_request_requires_chosen_field():
    with pytest.raises(ValidationError):
        OnboardingRequest()


def test_onboarding_request_rejects_invalid_domain():
    with pytest.raises(ValidationError):
        OnboardingRequest(chosen_field="not_a_real_domain")


def test_onboarding_request_accepts_valid_minimal_payload():
    req = OnboardingRequest(chosen_field="product_manager")
    assert req.chosen_field == "product_manager"
    assert req.self_assessment == []


def test_onboarding_request_rejects_self_assessment_score_out_of_range():
    with pytest.raises(ValidationError):
        OnboardingRequest(
            chosen_field="product_manager",
            self_assessment=[{"question": "How comfortable are you with ambiguity?", "score": 6}],
        )


def test_onboarding_request_rejects_too_many_self_assessment_answers():
    with pytest.raises(ValidationError):
        OnboardingRequest(
            chosen_field="product_manager",
            self_assessment=[{"question": f"q{i}", "score": 3} for i in range(21)],
        )


def test_update_user_request_all_fields_optional():
    req = UpdateUserRequest()
    assert req.full_name is None
    assert req.core_interests is None


def test_update_user_request_rejects_empty_full_name():
    with pytest.raises(ValidationError):
        UpdateUserRequest(full_name="")


def test_update_user_request_rejects_empty_core_interest_when_provided():
    with pytest.raises(ValidationError):
        UpdateUserRequest(core_interests=["ml", ""])


def test_update_user_request_allows_core_interests_none():
    req = UpdateUserRequest(core_interests=None)
    assert req.core_interests is None


# ─── schemas/agent_contracts.py — boundary spot-checks ────────────────────

def test_question_score_rejects_out_of_range():
    with pytest.raises(ValidationError):
        QuestionScore(question="q", score=0)
    with pytest.raises(ValidationError):
        QuestionScore(question="q", score=6)
    QuestionScore(question="q", score=1)
    QuestionScore(question="q", score=5)


def test_npc_state_update_rejects_out_of_range_trust_score():
    with pytest.raises(ValidationError):
        NpcStateUpdate(npc_id="n1", trust_score=101, sentiment="positive")
    with pytest.raises(ValidationError):
        NpcStateUpdate(npc_id="n1", trust_score=-1, sentiment="positive")


def test_npc_state_update_rejects_invalid_sentiment():
    with pytest.raises(ValidationError):
        NpcStateUpdate(npc_id="n1", trust_score=50, sentiment="ecstatic")


def test_evaluation_result_rejects_out_of_range_overall_score():
    with pytest.raises(ValidationError):
        EvaluationResult(overall_score=101, feedback_summary="x")
    with pytest.raises(ValidationError):
        EvaluationResult(overall_score=-1, feedback_summary="x")


def test_evaluation_result_requires_feedback_summary():
    with pytest.raises(ValidationError):
        EvaluationResult(overall_score=50)
