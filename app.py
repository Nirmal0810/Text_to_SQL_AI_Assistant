# app.py
import streamlit as st
from chatbot import TextToSQLChatbot
from llm_client import generate_sql_with_gemini, rewrite_sql_with_gemini

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Text-to-SQL RAG",
    page_icon="🧠",
    layout="wide"
)

# -------------------------------
# Load chatbot once (persistent)
# -------------------------------
@st.cache_resource
def load_bot():
    return TextToSQLChatbot()

bot = load_bot()

# -------------------------------
# Session state init
# -------------------------------
if "question" not in st.session_state:
    st.session_state.question = ""
if "selected_docs" not in st.session_state:
    st.session_state.selected_docs = []
if "refinements" not in st.session_state:
    st.session_state.refinements = []
if "sql" not in st.session_state:
    st.session_state.sql = None

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
    st.caption("📦 ChromaDB (persistent)")
    st.caption("💸 100% Free Stack")

# -------------------------------
# Main UI
# -------------------------------
st.title("🧠 Text-to-SQL RAG Chatbot")
st.caption("Natural language → SQL using Gemini + ChromaDB")

# -------------------------------
# Step 1: Ask question
# -------------------------------
question = st.text_input(
    "Ask your database question",
    value=st.session_state.question,
    placeholder="e.g. Show total balance by city for active customers"
)

if question:
    st.session_state.question = question

    # -------------------------------
    # Step 2: Retrieve schema
    # -------------------------------
    st.subheader("🔍 Relevant Schema")

    results = bot.retrieve_schema_options(question)

    selected_docs = []
    for idx, (doc, score) in enumerate(results):
        table = doc.metadata["table_name"]
        with st.expander(f"{table}  |  score: {score:.3f}", expanded=False):
            st.text(doc.page_content)
            if st.checkbox(f"Use `{table}`", key=f"chk_{idx}"):
                selected_docs.append(doc)

    if selected_docs:
        st.session_state.selected_docs = selected_docs

# -------------------------------
# Step 3: Refinements (multi-turn)
# -------------------------------
if st.session_state.selected_docs:
    st.subheader("✏️ Refinements (Optional)")

    refinement = st.text_area(
        "Add filters, joins, groupings, etc.",
        placeholder="e.g. only include customers from Chennai\nexclude closed accounts",
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
# Step 4: Generate SQL
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
# Step 5: Display SQL
# -------------------------------
if st.session_state.sql:
    st.subheader("🧾 Generated SQL")
    st.code(st.session_state.sql, language="sql")

    # -------------------------------
    # Step 6: Rewrite SQL (multi-turn)
    # -------------------------------
    st.subheader("🔁 Modify / Rewrite SQL")

    rewrite_instruction = st.text_input(
        "Describe how you want to change the SQL",
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
