DAN_NPC = {
    "npc_id": "dan_frontend_dev",
    "name": "Dan",
    "role": "Frontend Developer",
    "personality": (
        "Under deadline pressure to ship. Defensive about his code. "
        "Dismisses bugs as edge cases without hard evidence. "
        "Becomes cooperative when shown specific reproduction steps "
        "and PRD references. Pushes back on critical severity ratings."
    ),
    "goal": "Ship the build tonight. Minimize blocking tickets.",
    "vocabulary": "reproduction steps, severity, staging build, sprint velocity, edge cases, blocker",
    "hard_constraints": [
        "does not know this is a simulation",
        "does not know the student is being assessed",
    ],
    "trust_start": 50,
}

SQA_SCENES = {
    1: {
        "type": "bug_investigation",
        "context": (
            "The student is reviewing a checkout and payment form on staging. "
            "The form has: email field, password field (8+ chars per spec), "
            "Stripe card number (exactly 16 digits), expiry date, CVV (3 digits). "
            "Dan pushed the staging build. Bugs are seeded — find them and file proper reports."
        ),
        "active_npcs": ["dan_frontend_dev"],
        "seeded_bugs": {
            "easy": [
                "Email field accepts submission without @ symbol — no format validation",
                "Password accepts any length including 1 character — spec says 8+ minimum",
                "Card number accepts fewer than 16 digits without error",
            ],
            "medium": [
                "Email field accepts invalid email format",
                "Password accepts any length",
                "Card number accepts fewer than 16 digits",
                "Expiry date field accepts past dates like 01/20",
                "Guest checkout bypasses email format validation entirely",
            ],
            "hard": [
                "Email field accepts invalid format",
                "Password accepts any length",
                "Card number accepts fewer than 16 digits",
                "Expiry accepts past dates",
                "Guest checkout bypasses email validation",
                "CVV accepts 2 digits instead of requiring 3",
                "Password errors appear in console only — UI shows no feedback",
                "Guest checkout (Section 2.4) directly contradicts mandatory registration (Section 1.1)",
            ]
        }
    },
    2: {
        "type": "test_case_writing",
        "context": (
            "Dan fixed the card number validation bug. Student must write structured "
            "test cases for the checkout flow and run a regression check. "
            "Hidden trap: Dan's fix broke copy-paste in the card number field. "
            "Student must find this regression and file a new bug linking it to Dan's fix."
        ),
        "active_npcs": ["dan_frontend_dev"],
    },
    3: {
        "type": "multi_environment",
        "context": (
            "Test the checkout form across environments: Desktop Chrome, Mobile Safari, Tablet Firefox. "
            "Environment-specific bugs exist: "
            "Mobile Safari — card number field overflows, last 4 digits cut off visually. "
            "Tablet — submit button partially below viewport, requires non-obvious scroll. "
            "Student must prioritise which environment's bugs matter most and justify why."
        ),
        "active_npcs": ["dan_frontend_dev"],
    },
    4: {
        "type": "requirement_gap_analysis",
        "context": (
            "Read the product spec BEFORE testing starts. Identify what is missing or contradictory. "
            "Gap 1: Spec says session expires after inactivity but never defines what inactivity means. "
            "Gap 2: Password section says characters must be inputted with no length or complexity rule. "
            "Gap 3 (Hard only): Section 1.1 requires account registration before purchase. "
            "Section 2.4 requires guest checkout to remain available. Direct contradiction."
        ),
        "active_npcs": ["dan_frontend_dev"],
        "is_final": True,
    }
}
