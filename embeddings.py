# =============================================================================
# embeddings.py — Create, save, and load the FAISS vector store
# =============================================================================

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    EMBEDDING_MODEL,
    VECTORSTORE_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


# ── Embedding model (singleton — loaded once, reused everywhere) ───────────
# Calling HuggingFaceEmbeddings() downloads the model on first run (~22 MB).
# Subsequent runs load it from the local cache — no internet needed.
def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Return the HuggingFace embedding model.
    The model is downloaded automatically on first use and cached locally.
    """
    print(f"[embeddings] Loading embedding model: {EMBEDDING_MODEL}")
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},          # use CPU (works on any machine)
        encode_kwargs={"normalize_embeddings": True},  # cosine similarity ready
    )


# ── Text splitting ─────────────────────────────────────────────────────────
def split_documents(documents: List[Document]) -> List[Document]:
    """
    Split large documents into smaller chunks for better retrieval.

    RecursiveCharacterTextSplitter tries to split on natural boundaries
    in this order:  paragraph  →  sentence  →  word  →  character
    so chunks are semantically coherent whenever possible.

    Args:
        documents: flat list of LangChain Documents from loader.py

    Returns:
        list of smaller Document chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    print(f"[embeddings] Split {len(documents)} section(s) "
          f"→ {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


# ── Vector store: build and save ───────────────────────────────────────────
def build_vectorstore(chunks: List[Document]) -> FAISS:
    """
    Embed every chunk and store all vectors in a FAISS index.
    Saves the index to VECTORSTORE_PATH so it can be loaded later.

    This can take a few minutes for large document sets.
    """
    embeddings = get_embedding_model()

    print(f"[embeddings] Creating embeddings for {len(chunks)} chunks "
          "(this may take a few minutes) ...")

    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    # Persist to disk
    Path(VECTORSTORE_PATH).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(VECTORSTORE_PATH)

    print(f"[embeddings] Vector store saved to '{VECTORSTORE_PATH}/' ✓\n")
    return vectorstore


# ── Vector store: load from disk ──────────────────────────────────────────
def load_vectorstore() -> FAISS:
    """
    Load an existing FAISS index from VECTORSTORE_PATH.

    Raises:
        FileNotFoundError if ingest.py has not been run yet.
    """
    index_file = Path(VECTORSTORE_PATH) / "index.faiss"
    if not index_file.exists():
        raise FileNotFoundError(
            f"No vector store found at '{VECTORSTORE_PATH}/'. "
            "Run  python ingest.py  first."
        )

    embeddings = get_embedding_model()

    # allow_dangerous_deserialization=True is required because FAISS stores
    # metadata with Python's pickle format. Since we created this index
    # ourselves with ingest.py, it is safe to load.
    vectorstore = FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    print(f"[embeddings] Vector store loaded from '{VECTORSTORE_PATH}/' ✓")
    return vectorstore


# ── Retriever factory ─────────────────────────────────────────────────────
def get_retriever(vectorstore: FAISS, k: int):
    """
    Wrap the FAISS vector store in a LangChain retriever.

    Args:
        vectorstore : the loaded FAISS index
        k           : number of chunks to return per query (from config.TOP_K)
    """
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )