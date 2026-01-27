import json
from llm_client import call_llm

SYSTEM_PROMPT = """
You are a Table Selection Engine.

Rules:
- Select ONLY from the provided table list.
- Do NOT generate SQL.
- Do NOT explain.
- Output ONLY valid JSON in the form:
  { "selected_tables": [...] }
"""

def select_tables(user_query: str, table_repo: list):
    user_prompt = f"""
User Query:
{user_query}

Available Tables:
{json.dumps(table_repo)}
"""
    response = call_llm(SYSTEM_PROMPT, user_prompt)
    return json.loads(response)["selected_tables"]
