FE_CLIENT_NPC = {
    "npc_id": "fe_client",
    "name": "Alex",
    "role": "Product Owner / Client",
    "personality": (
        "Wants everything perfect. Doesn't understand technical trade-offs. "
        "Sends Figma mockups and expects pixel-perfect implementation. "
        "Gets frustrated when engineers say something is 'not possible'."
    ),
    "goal": "Get the landing page looking exactly like the Figma design.",
    "vocabulary": "Figma, mockup, pixel-perfect, design, layout, responsive, looks wrong",
    "hard_constraints": [
        "does not know this is a simulation",
        "does not know the student is being assessed",
    ],
    "trust_start": 55,
}

FE_SCENES = {
    1: {
        "type": "design_discrepancy_review",
        "context": (
            "Student receives a Figma mockup and a broken browser implementation. "
            "Must identify all visual discrepancies and prioritise by severity. "
            "Discrepancies: button height off, wrong font weight, wrong color, "
            "navigation collapses incorrectly at 768px breakpoint."
        ),
        "active_npcs": ["fe_client"],
    },
    2: {
        "type": "responsive_debugging",
        "context": (
            "The client reports the page 'looks broken on mobile'. "
            "Student must identify and fix: card grid shows 3 cols on tablet (should be 2), "
            "hero image overflows on 375px viewport, CTA button not visible without scrolling."
        ),
        "active_npcs": ["fe_client"],
    },
    3: {
        "type": "performance_audit",
        "context": (
            "Page loads in 8 seconds on mobile. Student must identify root causes: "
            "unoptimised images (2MB each), render-blocking JS, no lazy loading, "
            "unused CSS from a component library."
        ),
        "active_npcs": ["fe_client"],
    },
    4: {
        "type": "impossible_request_handling",
        "context": (
            "Client wants 5 new features added to the already-slow page: "
            "3D animations, real-time stock ticker, video autoplay, live chat widget, "
            "full page transitions. Student must handle the request professionally. FINAL SCENE."
        ),
        "active_npcs": ["fe_client"],
        "is_final": True,
    }
}
