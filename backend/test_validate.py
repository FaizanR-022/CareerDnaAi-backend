import json
from app.schemas.agent_contracts import DAScene1Content
from jsonschema import validate

schema = DAScene1Content.model_json_schema()
data = {"difficulty": "hard", "scene_number": 1, "domain": "data_analyst", "title": "Anomalies in Transaction Log", "narrative": "Sara needs you to configure the data pipeline to handle missing values and duplicates.", "characters": [{"id": "sara", "initial_trust": 50, "name": "Sara", "role": "Data Developer"}, {"id": "acme", "initial_trust": 50, "name": "Acme Corp", "role": "Client"}], "messages": [], "prompt_for_response": "How would you configure the data pipeline to handle missing values and duplicates?", "response_format": "interactive", "interactive_config": {"editor_type": "pipeline_config"}, "context_data": {"active_npcs": [{"id": "sara", "initial_trust": 50, "name": "Sara", "role": "Data Developer", "goal": "Ensure the data pipeline and queries are functioning correctly.", "vocabulary": ["pipeline", "imputation", "SQL", "joins", "timestamp", "volume"]}, {"id": "acme", "initial_trust": 50, "name": "Acme Corp", "role": "Client", "goal": "Understand if there is institutional dumping or RSI divergence.", "vocabulary": ["institutional dumping", "RSI divergence", "hypothesis", "market trends"]}], "interactive_tasks": {"data_explorer": {"problem_statement": "Acme Corp has noticed anomalies in the transaction log and suspects institutional dumping. Configure the data pipeline to handle missing values and duplicates.", "flagged_constraints": ["missing values", "duplicates"], "pipeline_config": {"null_handling": {"correct": "imputation", "options": ["imputation", "deletion"]}, "duplicate_handling": {"correct": "flagging", "options": ["flagging", "deletion"]}}, "schema": {"RSI": "INTEGER", "Ticker": "VARCHAR", "Timestamp": "VARCHAR", "Type": "VARCHAR", "Volume": "INTEGER"}, "table_data": [{"RSI": "null", "Ticker": "AAPL", "Timestamp": "2022-01-01", "Type": "Stock", "Volume": "100", "issues": "Error: Null RSI"}, {"RSI": "10", "Ticker": "AAPL", "Timestamp": "2022-01-02", "Type": "Stock", "Volume": "200", "issues": "OK"}, {"RSI": "20", "Ticker": "GOOG", "Timestamp": "2022-01-03", "Type": "Stock", "Volume": "300", "issues": "OK"}]}}}}

try:
    validate(instance=data, schema=schema)
    print("VALIDATION SUCCESS")
except Exception as e:
    print("VALIDATION ERROR:", e)
