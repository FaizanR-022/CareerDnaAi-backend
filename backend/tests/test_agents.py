"""Tests for agent layer — no real LLM calls needed for structure tests."""
import pytest
from app.agents.supervisor import get_domain_agent, run_simulation_step
from app.agents.domains.base_agent import BaseDomainAgent
from app.agents.domains.pm_agent import PMAgent

def test_supervisor_routes_correctly():
    for domain in ["pm", "sqa", "da", "fe", "be"]:
        agent = get_domain_agent(domain)
        assert isinstance(agent, BaseDomainAgent)
        assert agent.domain == domain

def test_supervisor_rejects_unknown_domain():
    with pytest.raises(ValueError):
        get_domain_agent("unknown_domain")

def test_base_agent_difficulty_lowering():
    agent = PMAgent()
    # Failing student — avg score 35
    context = {"scores": {"analytical_reasoning": 35.0, "ambiguity_tolerance": 35.0}}
    assert agent.should_lower_difficulty(context) is True

def test_base_agent_passing_student():
    agent = PMAgent()
    # Passing student — avg score 75
    context = {"scores": {"analytical_reasoning": 75.0, "ambiguity_tolerance": 75.0}}
    assert agent.should_lower_difficulty(context) is False

def test_base_agent_simulation_complete():
    agent = PMAgent()
    context = {"scenes_completed": [1, 2, 3, 4]}
    assert agent.is_simulation_complete(context) is True

def test_base_agent_simulation_not_complete():
    agent = PMAgent()
    context = {"scenes_completed": [1, 2]}
    assert agent.is_simulation_complete(context) is False

def test_pm_fallback_scene():
    agent = PMAgent()
    result = agent._fallback_scene(1, "ambiguous_feature_request", {})
    assert "title" in result
    assert "branch_point" in result
    assert "npc_opening_messages" in result
