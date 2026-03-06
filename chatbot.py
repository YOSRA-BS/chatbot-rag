# =============================================================================
# chatbot.py — Streamlit interface for the RAG chatbot
#
# Usage:
#     streamlit run chatbot.py
#
# Prerequisites:
#     1. Ollama running in the background  (ollama serve)
#     2. Model pulled                      (ollama pull llama3.2)
#     3. Documents ingested                (python ingest.py)
# =============================================================================

import os
import streamlit as st

from config import OLLAMA_MODEL, EMBEDDING_MODEL, TOP_K, VECTORSTORE_PATH
from chain  import build_chain


# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="📚",
    layout="centered",
)

st.title("📚 RAG Chatbot")
st.caption(
    f"Asking questions about your documents — "
    f"model: `{OLLAMA_MODEL}` · embeddings: `{EMBEDDING_MODEL}` · top-k: `{TOP_K}`" #affiche les paramètres de configuration actuels du chatbot dans la légende de la page Streamlit, ce qui est utile pour que les utilisateurs sachent quelle version du modèle et des embeddings ils utilisent, ainsi que le nombre de chunks récupérés (top-k) pour chaque question
)


# ── Guard: make sure ingest.py has been run ───────────────────────────────────
if not os.path.exists(os.path.join(VECTORSTORE_PATH, "index.faiss")):
    st.error(
        "**No vector store found.**\n\n"
        "Before chatting, you need to:\n"
        "1. Put your documents (PDF / DOCX / TXT) in the `documents/` folder\n"
        "2. Open a terminal and run:  `python ingest.py`\n"
        "3. Come back here and refresh the page."
    )
    st.stop()


# ── Helper: render source documents ──────────────────────────────────────────
def render_sources(source_docs: list) -> None:
    """
    Display retrieved document chunks inside a collapsible expander.
    Deduplicates entries with the same file + page combination.
    """
    with st.expander("📄 Sources used to answer this question"):
        seen = set()
        for doc in source_docs:
            file_name = os.path.basename(doc.metadata.get("source", "unknown"))
            page      = doc.metadata.get("page", "—")
            key       = f"{file_name}::{page}"

            if key not in seen:
                st.markdown(f"**`{file_name}`** — page {page}")
                excerpt = doc.page_content[:400].strip()
                if len(doc.page_content) > 400:
                    excerpt += "..."
                st.markdown(f"> {excerpt}")
                st.divider()
                seen.add(key)


# ── Load the chain (cached — built only once per session) ─────────────────────
@st.cache_resource(show_spinner="Loading documents and model ...")
def get_chain():
    """
    Build the RAG chain once and keep it in memory for the whole session.

    Without @st.cache_resource Streamlit re-runs the whole script on every
    interaction, which would reload FAISS from disk and wipe the conversation
    memory on every single message.
    """
    return build_chain()


chain = get_chain()


# ── Session state: the visible chat history ───────────────────────────────────
# LangChain's ConversationBufferMemory (inside the chain) handles the LLM
# conversation context automatically. st.session_state.messages only drives
# the visual rendering of past messages in the Streamlit UI.
if "messages" not in st.session_state:
    st.session_state.messages = []


# ── Render all previous messages ──────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])


# ── Handle new user input ─────────────────────────────────────────────────────
if user_question := st.chat_input("Ask a question about your documents ..."):

    # 1. Show and store the user message immediately
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # 2. Run the full RAG pipeline
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer ..."): #affiche un spinner pendant que le chatbot traite la question, ce qui améliore l'expérience utilisateur en indiquant que le système est en train de travailler sur la réponse
            result = chain.invoke({"question": user_question})#invoke() est la méthode qui exécute la chaîne de traitement du langage naturel (RAG chain) avec la question de l'utilisateur comme entrée. La chaîne effectue les étapes de reformulation, de récupération, d'augmentation et de génération pour produire une réponse basée sur les documents pertinents.
            #Ici, quand l’utilisateur tape une question (user_question), cette question est envoyée à la chaîne RAG via chain.invoke(). 
            #la chaîne encode la question en vecteur grâce au modèle d’embeddings déjà chargé (dans get_retriever → FAISS)
        
        answer = result.get("answer", "")
        sources = result.get("source_documents", [])

        st.markdown(answer)

        if sources:
            render_sources(sources)

    # 3. Persist the answer + sources for future rendering
    st.session_state.messages.append({
        "role":    "assistant",
        "content": answer,
        "sources": sources,
    })


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        chain.memory.clear()   # also wipe LangChain's internal memory
        st.rerun()

    st.divider()
    st.markdown("### 📊 Configuration")
    st.markdown(f"- **LLM:** `{OLLAMA_MODEL}`")
    st.markdown(f"- **Embeddings:** `{EMBEDDING_MODEL}`")
    st.markdown(f"- **Top-K chunks:** `{TOP_K}`")
    st.markdown(f"- **Vector store:** `{VECTORSTORE_PATH}/`")

    st.divider()
    st.markdown("### 📁 Add new documents")
    st.markdown(
        "1. Drop files into `documents/`\n"
        "2. Run: `python ingest.py`\n"
        "3. Refresh this page"
    )

    st.divider()
    st.markdown(f"💬 **Messages:** {len(st.session_state.messages)}")