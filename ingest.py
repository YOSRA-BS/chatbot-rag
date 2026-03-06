# =============================================================================
# ingest.py — Prepare your documents for the RAG chatbot
#
# Run this script ONCE before launching the chatbot, and again whenever
# you add new documents to the documents/ folder.
#
# Usage:
#     python ingest.py
# =============================================================================

from loader     import load_documents
from embeddings import split_documents, build_vectorstore


def ingest() -> None:
    print("=" * 60)
    print("  RAG Chatbot — Document Ingestion")
    print("=" * 60)

    # Step 1 ── Load all documents from the documents/ folder
    print("\n[Step 1/3] Loading documents ...")
    documents = load_documents()

    if not documents:
        print("\nNothing to ingest. Add files to the 'documents/' folder and retry.")
        return

    # Step 2 ── Split documents into smaller chunks
    print("\n[Step 2/3] Splitting into chunks ...")
    chunks = split_documents(documents)

    # Step 3 ── Create embeddings and save the FAISS index
    print("\n[Step 3/3] Creating embeddings and saving vector store ...")
    build_vectorstore(chunks)

    print("=" * 60)
    print(f"  Done!  {len(chunks)} chunks stored and ready.")
    print("  You can now launch the chatbot:  streamlit run chatbot.py")
    print("=" * 60)


if __name__ == "__main__":
    ingest()
