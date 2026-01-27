from llm_client import call_llm

SYSTEM_PROMPT = """
You are an expert SQL generator.

Rules:
- Generate ONLY SQL.
- BigQuery-compatible syntax ONLY.
- Use ONLY the provided schema context.
- No explanation.
- No comments.
"""

def generate_sql(user_query: str, schema_context: dict):
    user_prompt = f"""
User Query:
{user_query}

Schema Context:
{schema_context}
"""
    return call_llm(SYSTEM_PROMPT, user_prompt)
