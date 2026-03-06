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
    )# HuggingFaceEmbeddings est une classe de LangChain qui permet d’utiliser des modèles d’embeddings de Hugging Face pour convertir du texte en vecteurs numériques, model_kwargs={"device": "cpu"} spécifie que le modèle doit être chargé sur le CPU (ce qui garantit la compatibilité avec n’importe quelle machine, même sans GPU), encode_kwargs={"normalize_embeddings": True} indique que les vecteurs d’embeddings doivent être normalisés, ce qui les rend prêts à être utilisés avec la similarité cosinus dans le vector store FAISS


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
        # These separators are tried in order; falls back to the next if a chunk
        # is still too large.
        separators=["

", "
", ". ", "! ", "? ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    print(f"[embeddings] Split {len(documents)} section(s) "
          f"→ {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


# ── Vector store: build and save ───────────────────────────────────────────
def build_vectorstore(chunks: List[Document]) -> FAISS: #--> signature de la fonction build_vectorstore prend une liste de Document (chunks) et retourne un objet FAISS
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

    print(f"[embeddings] Vector store saved to '{VECTORSTORE_PATH}/' ✓
")
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
def get_retriever(vectorstore: FAISS, k: int): # means that the function get_retriever takes a FAISS vectorstore and an integer k as arguments, and returns a retriever object that can be used to search for relevant chunks of documents based on user queries, with k specifying how many top results to return per query
    """
    Wrap the FAISS vector store in a LangChain retriever.

    Args:
        vectorstore : the loaded FAISS index
        k           : number of chunks to return per query (from config.TOP_K)
    """
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    ) #vectorstore.as_retriever Cela “emballe” ton FAISS index dans une interface standard de LangChain appelée Retriever.

      #Le Retriever est une abstraction qui permet de poser des questions et de récupérer les documents les plus pertinents sans avoir à manipuler directement FAISS
