# metadata_manager.py
import json
import os
from typing import List, Dict, Any

from langchain_core.documents import Document


def load_metadata(path: str) -> List[Dict[str, Any]]:
    """
    Load schema metadata from JSON and normalize to a list of table dicts.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metadata file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Case 1: { "tables": [ ... ] }
    if isinstance(data, dict) and "tables" in data:
        tables = data["tables"]
        if not isinstance(tables, list):
            raise ValueError("Expected 'tables' to be a list in metadata JSON.")
        return tables

    # Case 2: already a list: [ {...}, {...} ]
    if isinstance(data, list):
        return data

    # Anything else is invalid for our usage
    raise ValueError(
        "Unsupported metadata JSON structure. Expected either:\n"
        "- { \"tables\": [ ... ] } or\n"
        "- [ ... ] (list of table objects)."
    )


def metadata_to_documents(metadata: List[Dict[str, Any]]) -> List[Document]:
    """
    Convert table-level metadata into LangChain Documents.

    Each table becomes one Document with:
    - page_content: textual description of table + columns
    - metadata: table_name, id, etc.

    Adapted for your JSON format where the table key is 'name'.
    """
    docs: List[Document] = []

    for table in metadata:
        # Your JSON uses "name" for table name
        table_name = table.get("name", "UNKNOWN_TABLE")
        desc = table.get("description", "")
        columns = table.get("columns", [])

        col_lines = []
        for col in columns:
            col_lines.append(
                f"{col.get('name')} ({col.get('type')}): {col.get('description', '')}"
            )

        content = (
            f"Table: {table_name}\n"
            f"Description: {desc}\n"
            "Columns:\n"
            + "\n".join(f"- {line}" for line in col_lines)
        )

        docs.append(
            Document(
                page_content=content,
                metadata={
                    # No explicit "id" in your JSON, so we just reuse table_name
                    "id": table_name,
                    "table_name": table_name,
                },
            )
        )

    return docs
