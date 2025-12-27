# llm_client.py
from typing import List

from google import genai

from config import GEMINI_MODEL_NAME, get_gemini_api_key


def build_gemini_client() -> genai.Client:
    """Create a Gemini client using the configured API key."""
    api_key = get_gemini_api_key()
    return genai.Client(api_key=api_key)


def generate_sql_with_gemini(
    client: genai.Client,
    schema_context: str,
    original_question: str,
    refinements: List[str],
) -> str:
    """
    Ask Gemini to synthesize an SQL query using the given schema
    and conversation context. Response MUST be SQL only.
    """
    refinements_text = ""
    if refinements:
        refinements_text = "\nAdditional user refinements:\n" + "\n".join(
            f"- {r}" for r in refinements
        )

    prompt = f"""
You are an expert SQL query generator.

You are given:
1. Database schema context (tables & columns).
2. The user's original natural-language question.
3. Optional additional user refinements to narrow the query.

Your task:
- Write a single SQL query that correctly answers the user's request.
- Use ONLY the tables and columns from the provided schema context.
- Do NOT invent tables or columns.
- Use clear and correct SQL.
- SQL dialect: standard ANSI-style SQL (no vendor-specific syntax).
- IMPORTANT: Output ONLY the SQL query and NOTHING ELSE.
- Do not add explanations, comments, or backticks.

=== SCHEMA CONTEXT START ===
{schema_context}
=== SCHEMA CONTEXT END ===

User's original question:
{original_question}
{refinements_text}

Now output only the final SQL query:
""".strip()

    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt,
    )
    sql = (response.text or "").strip()
    return sql


def rewrite_sql_with_gemini(
    client: genai.Client,
    original_sql: str,
    user_instruction: str,
) -> str:
    """
    Ask Gemini to rewrite an existing SQL query based on a user instruction
    (e.g., convert subquery to CTE) while keeping semantics intact.
    """
    prompt = f"""
You are an expert SQL rewriter.

Task:
- You are given an existing SQL query.
- You are also given the user's instruction describing how to modify the query.
- Rewrite the query to satisfy the instruction.
- Preserve the behavior and result of the original query as much as possible.
- Do NOT change the logical meaning unless required by the instruction.
- Examples: converting subqueries to common table expressions (CTEs), changing JOIN styles, etc.
- IMPORTANT: Output ONLY the rewritten SQL query and NOTHING ELSE.
- Do not add explanations, comments, or backticks.

Original SQL query:
{original_sql}

User instruction:
{user_instruction}

Now output only the rewritten SQL query:
""".strip()

    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt,
    )
    new_sql = (response.text or "").strip()
    return new_sql
    