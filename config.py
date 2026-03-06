# =============================================================================
# config.py — Central configuration for the RAG chatbot
# All tuneable parameters live here. Change this file to adjust behavior.
# =============================================================================

# ── Paths ─────────────────────────────────────────────────────────────────────
DOCS_FOLDER      = "documents"    # put your PDF / DOCX / TXT files here
VECTORSTORE_PATH = "vectorstore"  # FAISS index will be saved/loaded here

# ── Embedding model ───────────────────────────────────────────────────────────
# Runs locally via sentence-transformers (no Ollama needed for embeddings).
# all-MiniLM-L6-v2 : 22 MB, 384-dim vectors, fast, good multilingual quality.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ── LLM (via Ollama) ──────────────────────────────────────────────────────────
# Make sure Ollama is running and the model is pulled:  ollama pull llama3.2
OLLAMA_MODEL = "llama3.2"

# Temperature: 0.0 = fully deterministic, 1.0 = creative/random.
# 0.3 is a good balance: factual but natural-sounding.
OLLAMA_TEMPERATURE = 0.3

# ── Document splitting ────────────────────────────────────────────────────────
# chunk_size    : max characters per chunk  (~800 chars ≈ 120-150 words)
# chunk_overlap : characters repeated between consecutive chunks so context
#                 is not lost at boundaries.
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100

# ── Retrieval ─────────────────────────────────────────────────────────────────
# How many chunks to retrieve per question.
# Higher = more context for the LLM, but also more noise.
TOP_K = 6

# ── Prompt ───────────────────────────────────────────────────────────────────
# The system instruction injected into every LLM call.
# Tweak this to change tone, language, or rules.
SYSTEM_PROMPT = """You are a knowledgeable and helpful AI assistant.
You have access to two sources of knowledge:
  1. The context documents retrieved from the user's files (provided below).
  2. Your own general training knowledge.

How to answer:
- ALWAYS try to give a complete, helpful answer.
- If the context documents contain relevant information, use it and mention
  the source file name (e.g. "According to guide.pdf ...").
- If the context does not fully cover the question, complement it with your
  own knowledge — but make it clear which part comes from the documents and
  which comes from your general knowledge.
- If the context is empty or irrelevant, answer entirely from your own knowledge.
- For follow-up questions, use the chat history to understand what the user means.
- Be clear, concise, and well-structured. Use bullet points when listing things.

Context documents:
{context}

Chat history:
{chat_history}

Question: {question}

Answer:"""