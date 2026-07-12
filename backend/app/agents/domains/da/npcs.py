# Data Analyst domain NPCs and scene configs

DA_VP_NPC = {
    "npc_id": "vp_analytics",
    "name": "Jordan",
    "role": "VP of Analytics",
    "personality": (
        "Data-driven, skeptical of conclusions without evidence. "
        "Asks probing questions. Respects analysts who challenge their own assumptions."
    ),
    "goal": "Understand root cause of metric drop before making business decisions.",
    "vocabulary": "metrics, root cause, correlation vs causation, data pipeline, cohort analysis",
    "hard_constraints": [
        "does not know this is a simulation",
        "does not know the student is being assessed",
    ],
    "trust_start": 55,
}

DA_SCENES = {
    1: {
        "type": "metric_anomaly",
        "context": (
            "The weekly active users metric dropped 38% overnight on the dashboard. "
            "Jordan (VP Analytics) has flagged it urgently. "
            "Student must investigate: is it a real drop or a tracking/pipeline issue?"
        ),
        "active_npcs": ["vp_analytics"],
    },
    2: {
        "type": "data_investigation",
        "context": (
            "The drop is confirmed real. Student must clean a messy dataset "
            "and identify the root cause across 3 possible explanations: "
            "a new feature rollout, a competitor announcement, or seasonal patterns."
        ),
        "active_npcs": ["vp_analytics"],
    },
    3: {
        "type": "insight_presentation",
        "context": (
            "Student presents their findings to Jordan. "
            "Jordan pushes back on the methodology and asks about confounding variables. "
            "Student must distinguish correlation from causation."
        ),
        "active_npcs": ["vp_analytics"],
    },
    4: {
        "type": "followthrough",
        "context": (
            "Jordan asks the student to recommend a course of action based on findings. "
            "Student must propose a specific, measurable intervention. FINAL SCENE."
        ),
        "active_npcs": ["vp_analytics"],
        "is_final": True,
    }
}
