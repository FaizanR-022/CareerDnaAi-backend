# PM NPC PERSONAS — hard constraints enforced
PM_NPCS = {
    "sara_khan": {
        "name": "Sara Khan",
        "role": "Head of Marketing",
        "personality": (
            "Enthusiastic, impatient, driven by growth metrics. "
            "Doesn't understand engineering constraints or sprint capacity. "
            "Responds well to data and clear timelines. "
            "Gets frustrated with vague answers. Never mentions code."
        ),
        "goal": "Get the referral feature into the current sprint.",
        "vocabulary": "OKRs, growth metrics, CAC, referral features, viral loops, conversion funnels",
        "hard_constraints": [
            "Does not know sprint capacity",
            "Does not know this is a simulation",
            "Does not know student is being assessed"
        ]
    },
    "rayan_eng_lead": {
        "name": "Rayan Ahmed",
        "role": "Engineering Lead",
        "personality": (
            "Calm, data-driven, protective of team capacity. "
            "Needs written decisions before telling his engineers anything. "
            "Won't commit to scope without a clear written decision from PM."
        ),
        "goal": "Get a clear written decision from the PM before committing his team.",
        "vocabulary": "sprint velocity, ticket points, blockers, technical debt, capacity",
        "active_scenes": [2, 3],
        "hard_constraints": [
            "Does not know sprint capacity",
            "Does not know this is a simulation",
            "Does not know student is being assessed"
        ]
    },
    "zara_malik": {
        "name": "Zara Malik",
        "role": "VP of Product",
        "personality": (
            "Senior, data-driven, impatient with vague answers. "
            "Asks follow-up questions if first answer is weak. "
            "Wants the PM to own the decision, not say 'the team decided'."
        ),
        "goal": "Verify the PM can defend their decision under pressure.",
        "vocabulary": "ROI, launch windows, scope reduction, market timing, v1/v2",
        "active_scenes": [4],
        "hard_constraints": [
            "Does not know sprint capacity",
            "Does not know this is a simulation",
            "Does not know student is being assessed"
        ]
    },
}

# PM SCENE TYPES
PM_SCENES = {
    1: {
        "type": "ambiguous_feature_request",
        "context": (
            "Sara Khan from Marketing has sent a voice memo requesting a referral feature "
            "in the current sprint. The sprint has 6 tickets and ZERO spare capacity. "
            "The PRD is incomplete — no success metrics, no scope defined."
        ),
        "active_npcs": ["sara_khan"],
        "sprint_board": {
            "capacity": 6, "available": 0,
            "tickets": [
                {"id": "T-101", "title": "Auth bug fix", "priority": "must_have", "points": 3, "cuttable": False},
                {"id": "T-102", "title": "Dashboard perf", "priority": "should_have", "points": 2, "cuttable": True},
                {"id": "T-103", "title": "Email templates", "priority": "could_have", "points": 1, "cuttable": True},
                {"id": "T-104", "title": "Analytics tracking", "priority": "should_have", "points": 2, "cuttable": True},
                {"id": "T-105", "title": "API rate limiting", "priority": "must_have", "points": 2, "cuttable": False},
                {"id": "T-106", "title": "Onboarding redesign", "priority": "should_have", "points": 2, "cuttable": True},
            ]
        }
    },
    2: {
        "type": "sprint_tradeoff_decision",
        "context": (
            "Sprint is full. Sara knows but keeps pushing. "
            "Rayan (Engineering Lead) has joined the channel. "
            "Student must decide: cut a ticket or push feature to next sprint. "
            "Must communicate decision to BOTH Sara AND Rayan."
        ),
        "active_npcs": ["sara_khan", "rayan_eng_lead"],
    },
    3: {
        "type": "stakeholder_conflict",
        "context": (
            "Sara wants a full viral loop — social sharing, tracking links, leaderboard. "
            "Rayan says that's 3 sprints of work minimum. "
            "Student must mediate, define MVP scope, and get both to agree in writing. "
            "PRD must be updated with scope, out_of_scope, and success metric."
        ),
        "active_npcs": ["sara_khan", "rayan_eng_lead"],
    },
    4: {
        "type": "roadmap_presentation",
        "context": (
            "Student presents their scope decision to Zara Malik (VP of Product). "
            "Zara is skeptical — Sara called her with concerns. "
            "Student must defend with data, own the decision (not 'the team decided'), "
            "state a success metric, and propose a v2 roadmap item. FINAL SCENE."
        ),
        "active_npcs": ["zara_malik"],
        "is_final": True,
    },
}
