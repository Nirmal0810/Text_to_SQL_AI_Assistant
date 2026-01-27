import json
from llm_client import call_llm

SYSTEM_PROMPT = """
You are a Schema Context Builder.

Rules:
- Use ONLY the provided metadata.
- Do NOT invent tables or columns.
- Do NOT generate SQL.
- Output ONLY valid JSON in the form:
  { "schema_context": {...} }
"""

def build_context(user_query: str, selected_tables: list, metadata_repo: dict):
    scoped_metadata = {t: metadata_repo[t] for t in selected_tables}

    user_prompt = f"""
User Query:
{user_query}

Selected Tables:
{json.dumps(selected_tables)}

Table Metadata:
{json.dumps(scoped_metadata)}
"""
    response = call_llm(SYSTEM_PROMPT, user_prompt)
    return json.loads(response)["schema_context"]
