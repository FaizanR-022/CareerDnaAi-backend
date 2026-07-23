# Data Analyst domain NPCs and scene configs

# Data Analyst domain NPCs and scene configs

DA_NPCS = {
    "sara_developer": {
        "npc_id": "sara_developer",
        "name": "Sara",
        "role": "Data Developer",
        "personality": "Technical, focused on clean pipelines and queries.",
        "goal": "Ensure the data pipeline and queries are functioning correctly.",
        "vocabulary_pool": [
            "pipeline config", "data integrity", "ETL", "schema validation",
            "null imputation", "SQL", "joins", "timestamp mapping",
            "volume ingestion", "data consistency", "query optimization"
        ],
        "vocabulary_avoid_repeating": True,
        "hard_constraints": [
            "does not know this is a simulation",
            "does not know the student is being assessed",
        ],
        "trust_start": 50,
    },
    "acme_corp_client": {
        "npc_id": "acme_corp_client",
        "name": "Acme Corp",
        "role": "Client",
        "personality": "Business-oriented, concerned about market anomalies.",
        "goal": "Understand if there is institutional dumping or RSI divergence.",
        "vocabulary_pool": [
            "market anomaly", "institutional divergence", "volume spikes",
            "business impact", "RSI divergence", "hypothesis validation",
            "market trends", "data correlation", "actionable insights"
        ],
        "vocabulary_avoid_repeating": True,
        "hard_constraints": [
            "does not know this is a simulation",
            "does not know the student is being assessed",
        ],
        "trust_start": 50,
    }
}

DA_SCENES = {
    1: {
        "type": "pipeline_config",
        "context": (
            "Acme Corp has noticed anomalies in the transaction log and suspects institutional dumping. "
            "Sara needs you to configure the data pipeline to handle missing values and duplicates."
        ),
        "active_npcs": ["sara_developer", "acme_corp_client"],
    },
    2: {
        "type": "sql_editor",
        "context": (
            "With the pipeline configured, Sara asks you to write a PostgreSQL query "
            "to extract the relevant data from the transaction_log table, focusing on timestamp and volume."
        ),
        "active_npcs": ["sara_developer"],
    },
    3: {
        "type": "python_editor",
        "context": (
            "Now that you have the data, Sara wants you to write a pandas script to visualize it. "
            "Plot the volume against the timestamp to check for RSI divergence."
        ),
        "active_npcs": ["sara_developer", "acme_corp_client"],
    },
    4: {
        "type": "insights_console",
        "context": (
            "Review the visualized data and provide your final analysis to Acme Corp. "
            "Select the most likely hypothesis (e.g., RSI divergence) and provide a detailed text analysis."
        ),
        "active_npcs": ["acme_corp_client"],
        "is_final": True,
    }
}
