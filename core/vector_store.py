import utils.env_setup  # Enforces safe drive paths and env before imports
import os
from pathlib import Path
from uuid import uuid4
from langchain_chroma import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(PROJECT_ROOT / "vector_db")
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_embeddings():
    cache_dir = str(PROJECT_ROOT / ".cache" / "sentence-transformers")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        cache_folder=cache_dir,
    )

def build_vector_store(transcript: str) -> Chroma:
    print("Building vector store...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=(f"transcript_{uuid4().hex}" if os.getenv("ISOLATE_TRANSCRIPTS") == "1" else COLLECTION_NAME),
        persist_directory=(None if os.getenv("ISOLATE_TRANSCRIPTS") == "1" else CHROMA_DIR)
    )

    return vector_store


def load_vector_store() -> Chroma:
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )

    return vector_store

def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={"k": k}
    )
