# vectorstore_manager.py
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import METADATA_PATH, CHROMA_DIR, CHROMA_COLLECTION_NAME
from metadata_manager import load_metadata, metadata_to_documents


def build_or_load_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # If DB already exists, just load it
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        return Chroma(
            embedding_function=embeddings,
            persist_directory=CHROMA_DIR,
            collection_name=CHROMA_COLLECTION_NAME,
        )

    # Else build from scratch
    metadata = load_metadata(METADATA_PATH)
    docs = metadata_to_documents(metadata)

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=CHROMA_COLLECTION_NAME,
    )
    return vectorstore
