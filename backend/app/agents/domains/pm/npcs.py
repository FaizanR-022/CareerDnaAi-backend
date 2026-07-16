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
        },
        # PRD starts incomplete — no scope or metrics yet (student must fill these in)
        "prd_data": {
            "title": "Referral Feature PRD — Draft",
            "objective": "Introduce a referral mechanism to accelerate user growth via word-of-mouth.",
            "audience": "",
            "requirements": "",
            "outOfScope": "",
            "successMetrics": "",
        },
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
        # PRD still incomplete — student is mid-decision, scope not yet locked
        "prd_data": {
            "title": "Referral Feature PRD — Draft",
            "objective": "Introduce a referral mechanism to accelerate user growth via word-of-mouth.",
            "audience": "Existing mobile-first users aged 18-35 who are likely to recommend the product.",
            "requirements": "",
            "outOfScope": "",
            "successMetrics": "",
        },
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
        # PRD partially filled — student must complete requirements, outOfScope, and successMetrics
        "prd_data": {
            "title": "Referral Feature PRD — v0.1",
            "objective": "Deliver an MVP referral flow that lets users share a unique invite link and tracks successful sign-ups.",
            "audience": "Existing mobile-first users aged 18-35 who are likely to recommend the product.",
            "requirements": "1. Unique referral link generation per user.\n2. Referral tracking dashboard (invites sent, accepted).\n3. Confirmation email to referrer on successful sign-up.",
            "outOfScope": "",
            "successMetrics": "",
        },
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
        # PRD fully drafted — student defends this document to Zara
        "prd_data": {
            "title": "Referral Feature PRD — v1.0",
            "objective": "Deliver an MVP referral flow that lets users share a unique invite link and tracks successful sign-ups, targeting a 15% uplift in new user acquisition within 30 days.",
            "audience": "Existing mobile-first users aged 18-35 who are likely to recommend the product.",
            "requirements": (
                "1. Unique referral link generation per user.\n"
                "2. Referral tracking dashboard (invites sent, accepted).\n"
                "3. Confirmation email to referrer on successful sign-up.\n"
                "4. Basic leaderboard showing top referrers (v1 — read-only)."
            ),
            "outOfScope": (
                "Native mobile app deep links, multi-currency reward payouts, "
                "social-sharing leaderboard animations, and AI-personalised referral copy."
            ),
            "successMetrics": (
                "1. Referral conversion rate ≥ 20% (invite accepted / invite sent).\n"
                "2. 15% net new user growth within 30 days of launch.\n"
                "3. Referral share rate ≥ 10% of active user base within first 2 weeks."
            ),
        },
    },
}
