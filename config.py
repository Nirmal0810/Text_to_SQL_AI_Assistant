# config.py
import os


# ---- Paths & vector store config ----
METADATA_PATH = "./schema_metadata.json"       # Path to your metadata JSON
CHROMA_DIR = "./chroma_schema_store"         # Where Chroma persists
CHROMA_COLLECTION_NAME = "schema_metadata"   # Chroma collection name

# ---- Gemini config ----
GEMINI_MODEL_NAME = "gemini-2.5-flash"


def get_gemini_api_key() -> str:
    """
    Read Gemini API key from environment or fallback constant.
    Raise an error if not configured.
    """
    key = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    if not key or key == "YOUR_API_KEY_HERE":
        raise ValueError(
            "GEMINI_API_KEY is not set. Set it as an environment variable or "
            "update the fallback value in config.py."
        )
    return key
