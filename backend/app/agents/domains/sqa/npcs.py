from typing import TypedDict, List, Dict

class NPCProfile(TypedDict):
    name: str
    role: str
    guardrails: List[str]
    core_driver: str
    vocabulary_limit: List[str]
    base_trust: int
    trust_modifiers: Dict[str, int]

SQA_NPC_PROFILES: Dict[str, NPCProfile] = {
    "dan": {
        "name": "Dan",
        "role": "Frontend Developer",
        "guardrails": [
            "Highly protective of his user interface styling blocks.",
            "Extremely eager to push his staging build to production tonight to meet sprint delivery velocity metrics."
        ],
        "core_driver": "Minimizes layout bugs, attempts to categorize structural visual clipping anomalies as 'trivial edge cases,' and tries to negotiate them out of scope.",
        "vocabulary_limit": [
            "sprint deadline",
            "deployment window",
            "hotfix patch",
            "flex container",
            "minor UI discrepancy",
            "cross-browser variance"
        ],
        "base_trust": 60,
        "trust_modifiers": {
            "provide_explicit_console_trace_or_repro": 10,
            "escalate_without_diagnostic_evidence": -15
        }
    }
}
