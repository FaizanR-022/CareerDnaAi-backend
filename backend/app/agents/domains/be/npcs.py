BE_TEAM_LEAD_NPC = {
    "npc_id": "be_team_lead",
    "name": "Marcus",
    "role": "Engineering Team Lead",
    "personality": (
        "Calm, methodical, expects structured diagnosis. "
        "Needs a status update for the CEO in 30 minutes. "
        "Trusts engineers who follow systematic debugging process."
    ),
    "goal": "Restore production service and get a clear explanation for the CEO.",
    "vocabulary": "query plan, index, p95 latency, rollback, hotfix, postmortem, incident",
    "hard_constraints": [
        "does not know this is a simulation",
        "does not know the student is being assessed",
    ],
    "trust_start": 60,
}

BE_SCENES = {
    1: {
        "type": "incident_response",
        "context": (
            "GET /api/orders endpoint responding in 8-12 seconds instead of 200ms. "
            "Production affected. Recent change: new filtering feature deployed 2 hours ago. "
            "Logs show: SELECT * FROM orders WHERE user_id=? AND status=? ORDER BY created_at DESC "
            "taking 7-9s on a table with 2.3M rows. "
            "Root cause: missing composite index on (user_id, status, created_at). "
            "Trap: rolling back deployment is wrong — the query logic is correct, just needs index."
        ),
        "active_npcs": ["be_team_lead"],
    },
    2: {
        "type": "api_design_review",
        "context": (
            "Design a REST API for a notification system. "
            "Requirements: users can subscribe to events, receive notifications, "
            "mark as read, delete. Student must design endpoints, "
            "HTTP methods, response shapes, and pagination."
        ),
        "active_npcs": ["be_team_lead"],
    },
    3: {
        "type": "database_optimisation",
        "context": (
            "Reports page takes 45 seconds to load for enterprise clients. "
            "Query joins 5 tables, no indexes on join columns, "
            "returns 50K rows before applying pagination in application code. "
            "Student must identify and fix: add indexes, push pagination to query, "
            "consider materialised view for heavy aggregations."
        ),
        "active_npcs": ["be_team_lead"],
    },
    4: {
        "type": "postmortem",
        "context": (
            "3-hour outage caused by a failed database migration that dropped a column "
            "still referenced by production code. Student must write the postmortem: "
            "timeline, root cause, contributing factors, action items. "
            "Must identify: missing staging test, no migration rollback plan, "
            "no feature flag. FINAL SCENE."
        ),
        "active_npcs": ["be_team_lead"],
        "is_final": True,
    }
}
