import json
from app.schemas.agent_contracts import DAScene1Content

payload = {"scene_number": 1, "domain": "data_analyst", "difficulty": "hard", "title": "Configure the Data Pipeline", "narrative": "Sara needs you to configure the data pipeline to handle missing values and duplicates.", "characters": [{"id": "sara", "initial_trust": 50, "name": "Sara", "role": "Data Developer"}], "messages": [], "prompt_for_response": "What type of imputation strategy would you like to use for missing RSI values?", "response_format": "interactive", "interactive_config": {"editor_type": "pipeline_config"}, "context_data": {"active_npcs": [{"name": "Sara", "goal": "Ensure the data pipeline and queries are functioning correctly.", "vocabulary": ["pipeline", "imputation", "SQL", "joins", "timestamp", "volume"], "trust": 50}], "interactive_tasks": {"data_explorer": {"problem_statement": "The transaction log has missing values and duplicates. Fix it using imputation and duplicate handling.", "flagged_constraints": ["missing RSI values", "duplicates in the transaction log"], "pipeline_config": {"null_handling": {"correct": "impute_mean", "options": ["impute_mean", "impute_zero"]}, "duplicate_handling": {"correct": "keep_first", "options": ["keep_first", "keep_last", "drop_all"]}}, "schema": {"RSI": "INTEGER", "Ticker": "VARCHAR", "Timestamp": "VARCHAR", "Type": "VARCHAR", "Volume": "INTEGER"}, "table_data": [{"RSI": None, "Ticker": "AAPL", "Timestamp": "2022-01-01", "Type": "stock", "Volume": 100, "issues": "Error: Null RSI"}, {"RSI": 10, "Ticker": "AAPL", "Timestamp": "2022-01-02", "Type": "stock", "Volume": 120, "issues": "OK"}, {"RSI": None, "Ticker": "AAPL", "Timestamp": "2022-01-03", "Type": "stock", "Volume": 140, "issues": "Error: Null RSI"}]}}}}

try:
    obj = DAScene1Content(**payload)
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
