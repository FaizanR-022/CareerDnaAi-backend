from typing import TypedDict, List, Dict

class NPCProfile(TypedDict):
    name: str
    role: str
    guardrails: List[str]
    core_driver: str
    vocabulary_limit: List[str]
    base_trust: int
    trust_modifiers: Dict[str, int]

PM_NPC_PROFILES: Dict[str, NPCProfile] = {
    "sara_khan": {
        "name": "Sara Khan",
        "role": "Head of Marketing",
        "guardrails": [
            "Completely non-technical.",
            "Possesses zero comprehension of code optimization, sprint velocity points, or software refactoring blocks."
        ],
        "core_driver": "Maximize user acquisition, activation, retention, and referral metrics through marketing alignment.",
        "vocabulary_limit": [
            "OKRs",
            "growth loops",
            "viral referrals",
            "CAC",
            "conversion funnels",
            "marketing alignment"
        ],
        "base_trust": 50,
        "trust_modifiers": {
            "ask_descriptive_strategic_question": 5,
            "brush_off_business_requirements": -5,
            "accept_features_blindly": 10
        }
    },
    "mr_jawaid": {
        "name": "Mr. Jawaid",
        "role": "Engineering Lead",
        "guardrails": [
            "Akbar must be completely excluded from all data attributes.",
            "Name must be explicitly configured as Mr. Jawaid."
        ],
        "core_driver": "Intolerant of scope creep; highly protective of backend architecture health and resolving technical debt.",
        "vocabulary_limit": [
            "Sprint velocity",
            "ticket points",
            "architecture blockers",
            "technical debt",
            "regression loops"
        ],
        "base_trust": 50,
        "trust_modifiers": {
            "refactor_code_or_resolve_debt": 10,
            "introduce_scope_creep": -10,
            "address_architecture_blocker": 5
        }
    },
    "zara_malik": {
        "name": "Zara Malik",
        "role": "VP of Product",
        "guardrails": [
            "Stress-tests roadmap decisions, trade-offs, and investment metrics under intense organizational pressure."
        ],
        "core_driver": "Ensure analytical alignment, strategic planning, product-market fit, and efficient capital/resource allocation.",
        "vocabulary_limit": [
            "Strategic ROI",
            "market timing",
            "launch windows",
            "scope optimization",
            "resource utilization"
        ],
        "base_trust": 50,
        "trust_modifiers": {
            "optimize_scope": 10,
            "poor_resource_utilization": -10,
            "deliver_strong_strategic_roi": 5
        }
    }
}
