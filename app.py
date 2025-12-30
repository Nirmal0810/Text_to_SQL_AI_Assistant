import streamlit as st
from chatbot import TextToSQLChatbot
from llm_client import (
    generate_sql_with_gemini,
    rewrite_sql_with_gemini,
    answer_question_with_gemini,
)

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Text-to-SQL & Q&A RAG",
    page_icon="🧠",
    layout="wide"
)

# -------------------------------
# Load chatbot once
# -------------------------------
@st.cache_resource
def load_bot():
    return TextToSQLChatbot()

bot = load_bot()

# -------------------------------
# Session state init
# -------------------------------
for key, default in {
    "question": "",
    "selected_docs": [],
    "refinements": [],
    "sql": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title("⚙️ Controls")

    if st.button("🆕 New Question"):
        st.session_state.question = ""
        st.session_state.selected_docs = []
        st.session_state.refinements = []
        st.session_state.sql = None
        st.rerun()

    st.markdown("---")
    st.caption("🧠 Gemini 2.5 Flash")
    st.caption("📦 ChromaDB (Persistent)")
    st.caption("💸 100% Free Stack")

# -------------------------------
# Mode Selector
# -------------------------------
st.title("🧠 Text-to-SQL & Q&A RAG Assistant")

mode = st.radio(
    "Select Mode",
    ["🧾 Text to SQL", "💬 Q&A (Info Bot)"],
    horizontal=True
)

question = st.text_input(
    "Ask your question",
    placeholder="e.g. Which table stores customer phone numbers?"
)

# =========================================================
# MODE 1: Q&A BOT (NO SQL)
# =========================================================
if mode == "💬 Q&A (Info Bot)" and question:
    st.info("This mode answers questions strictly from embedded schema data. SQL generation is disabled.")

    results = bot.retrieve_schema_options(question, top_k=5)
    docs = [doc for doc, _ in results]

    context = bot.build_schema_context_text(docs)

    answer = answer_question_with_gemini(
        client=bot.client,
        context=context,
        question=question,
    )

    st.subheader("💬 Answer")
    st.markdown(answer)

    with st.expander("📚 Context Used"):
        for doc in docs:
            st.text(doc.page_content)

# =========================================================
# MODE 2: TEXT TO SQL
# =========================================================
if mode == "🧾 Text to SQL" and question:
    st.session_state.question = question

    # -------------------------------
    # Schema Retrieval
    # -------------------------------
    st.subheader("🔍 Relevant Schema")

    results = bot.retrieve_schema_options(question)

    selected_docs = []
    for idx, (doc, score) in enumerate(results):
        table = doc.metadata["table_name"]
        with st.expander(f"{table} | score: {score:.3f}"):
            st.text(doc.page_content)
            if st.checkbox(f"Use `{table}`", key=f"sql_chk_{idx}"):
                selected_docs.append(doc)

    if selected_docs:
        st.session_state.selected_docs = selected_docs

    # -------------------------------
    # Refinements (Multi-turn)
    # -------------------------------
    if st.session_state.selected_docs:
        st.subheader("✏️ Refinements")

        refinement = st.text_area(
            "Add filters, joins, grouping rules, etc.",
            placeholder="e.g. only active accounts\nexclude closed loans",
            height=80
        )

        if st.button("➕ Add Refinement"):
            if refinement.strip():
                st.session_state.refinements.append(refinement.strip())

        if st.session_state.refinements:
            st.markdown("**Current refinements:**")
            for r in st.session_state.refinements:
                st.markdown(f"- {r}")

    # -------------------------------
    # Generate SQL
    # -------------------------------
    if st.session_state.selected_docs:
        if st.button("⚡ Generate SQL"):
            schema_context = bot.build_schema_context_text(
                st.session_state.selected_docs
            )

            sql = generate_sql_with_gemini(
                client=bot.client,
                schema_context=schema_context,
                original_question=st.session_state.question,
                refinements=st.session_state.refinements,
            )

            st.session_state.sql = sql

    # -------------------------------
    # SQL Output + Rewrite
    # -------------------------------
    if st.session_state.sql:
        st.subheader("🧾 Generated SQL")
        st.code(st.session_state.sql, language="sql")

        st.subheader("🔁 Modify / Rewrite SQL")

        rewrite_instruction = st.text_input(
            "Describe how to modify the SQL",
            placeholder="e.g. convert subquery to CTE, add HAVING clause"
        )

        if st.button("♻️ Rewrite SQL"):
            new_sql = rewrite_sql_with_gemini(
                client=bot.client,
                original_sql=st.session_state.sql,
                user_instruction=rewrite_instruction,
            )
            st.session_state.sql = new_sql
            st.rerun()
