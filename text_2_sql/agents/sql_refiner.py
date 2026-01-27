from llm_client import call_llm

SYSTEM_PROMPT = """
You are a SQL editor.

Rules:
- Modify ONLY the provided SQL.
- Do NOT change tables unless explicitly requested.
- Output ONLY SQL.
"""

def refine_sql(existing_sql: str, refinement: str):
    user_prompt = f"""
Current SQL:
{existing_sql}

User Refinement Request:
{refinement}
"""
    return call_llm(SYSTEM_PROMPT, user_prompt)
