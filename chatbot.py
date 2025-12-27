# chatbot.py
from typing import Optional, List, Tuple

from langchain_core.documents import Document
from langchain_chroma import Chroma

from llm_client import build_gemini_client, generate_sql_with_gemini, rewrite_sql_with_gemini
from vectorstore_manager import build_or_load_vectorstore


class TextToSQLChatbot:
    def __init__(self):
        # Build LLM + vectorstore
        self.client = build_gemini_client()
        self.vectorstore: Chroma = build_or_load_vectorstore()

        # Conversation state
        self.current_question: Optional[str] = None
        self.refinements: List[str] = []
        self.selected_docs: List[Document] = []
        self.last_sql: Optional[str] = None

    # ---- RAG / Retrieval ----
    def retrieve_schema_options(
        self, question: str, top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Similarity search on schema metadata and return (doc, score) pairs."""
        results = self.vectorstore.similarity_search_with_score(question, k=top_k)
        return results

    def present_schema_options(
        self, results: List[Tuple[Document, float]]
    ) -> List[Document]:
        """Print RAG options to user and let them choose relevant chunks."""

        if not results:
            print("No relevant schema chunks found. Try rephrasing your question.")
            return []

        print("\nI found the following relevant schema components:")
        for idx, (doc, score) in enumerate(results, start=1):
            table = doc.metadata.get("table_name", "UNKNOWN_TABLE")
            short_preview = doc.page_content.splitlines()[0:3]
            preview_text = " / ".join(short_preview)
            print(f"{idx}. Table: {table} | Score: {score:.4f}")
            print(f"   Preview: {preview_text[:200]}...")
            print()

        while True:
            choice = input(
                "Select the option numbers (e.g. 1,2) you want to use for SQL context,\n"
                "or type 'all' to use all, or 'none' to cancel: "
            ).strip().lower()

            if choice == "none":
                return []

            if choice == "all":
                return [doc for (doc, _) in results]

            try:
                indices = [int(x) for x in choice.split(",") if x.strip()]
                selected_docs = []
                for i in indices:
                    if 1 <= i <= len(results):
                        selected_docs.append(results[i - 1][0])
                if selected_docs:
                    return selected_docs
                else:
                    print("No valid indices selected. Try again.")
            except ValueError:
                print("Invalid input. Please enter comma-separated numbers, 'all', or 'none'.")

    # ---- Conversation Logic ----
    def reset_for_new_question(self):
        self.current_question = None
        self.refinements = []
        self.selected_docs = []

    def start(self):
        print("🧠 Text-to-SQL RAG Chatbot (Gemini 2.5 Flash + Chroma)")
        print("Commands: /new = new question, /generate = generate SQL, /exit = quit\n")

        while True:
            user_input = input("You: ").strip()

            # Global commands
            if user_input.lower() in ("/exit", "exit", "quit"):
                print("Exiting. Goodbye!")
                break

            if user_input.lower() in ("/new", "new"):
                self.reset_for_new_question()
                self.last_sql = None
                print("Starting a new question. Ask me your natural-language query.")
                continue

            # If we already have a SQL query, treat input as "rewrite the SQL"
            if self.last_sql is not None:
                # Modification mode: use Gemini to rewrite the last SQL
                try:
                    new_sql = rewrite_sql_with_gemini(
                        client=self.client,
                        original_sql=self.last_sql,
                        user_instruction=user_input,
                    )
                    self.last_sql = new_sql
                    # IMPORTANT: print ONLY the SQL query (no extra verbiage)
                    print(new_sql)
                except Exception as e:
                    print(f"[Error while rewriting SQL: {e}]")
                continue

            # If question already exists & schema is selected
            if self.current_question and self.selected_docs:
                if user_input.lower() in ("/generate", "generate", "sql"):
                    # Generate SQL now
                    try:
                        schema_context = self.build_schema_context_text(self.selected_docs)
                        sql = generate_sql_with_gemini(
                            client=self.client,
                            schema_context=schema_context,
                            original_question=self.current_question,
                            refinements=self.refinements,
                        )
                        self.last_sql = sql
                        # IMPORTANT: print ONLY the SQL query (no extra verbiage)
                        print(sql)
                    except Exception as e:
                        print(f"[Error while generating SQL: {e}]")
                    continue
                else:
                    # Treat as refinement
                    self.refinements.append(user_input)
                    print(
                        "Got it. Added this refinement to context. "
                        "When you're ready, type /generate to get the SQL."
                    )
                    continue

            # Otherwise, this is the start of a new question
            if not self.current_question:
                self.current_question = user_input
                self.refinements = []
                self.selected_docs = []

                # Run RAG retrieval
                try:
                    results = self.retrieve_schema_options(self.current_question)
                    self.selected_docs = self.present_schema_options(results)

                    if not self.selected_docs:
                        print("No schema selected. You can /new to ask another question.")
                        # reset so user can try again
                        self.reset_for_new_question()
                        continue

                    print(
                        "\nGreat. I've kept only your selected schema chunks in context.\n"
                        "Now you can:\n"
                        "- Add more details (filters, joins, groupings, etc.), or\n"
                        "- Type /generate when you're ready for the SQL query."
                    )
                except Exception as e:
                    print(f"[Error during retrieval: {e}]")
                    self.reset_for_new_question()
                    continue

    # ---- Helper to format schema context ----
    @staticmethod
    def build_schema_context_text(docs: List[Document]) -> str:
        lines = []
        for idx, doc in enumerate(docs, start=1):
            table = doc.metadata.get("table_name", "UNKNOWN_TABLE")
            lines.append(f"--- Schema Chunk {idx} (Table: {table}) ---")
            lines.append(doc.page_content)
        return "\n".join(lines)
