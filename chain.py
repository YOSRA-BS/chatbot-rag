# =============================================================================
# chain.py — Build the conversational RAG chain
#
# This is the core of the chatbot.
# It connects: retriever → prompt → LLM → answer + sources
# =============================================================================

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory

from config import OLLAMA_MODEL, OLLAMA_TEMPERATURE, TOP_K, SYSTEM_PROMPT
from embeddings import load_vectorstore, get_retriever


def build_chain() -> ConversationalRetrievalChain: #signifie que la fonction build_chain retourne une instance de ConversationalRetrievalChain, qui est la chaîne de traitement du langage naturel utilisée par le chatbot pour répondre aux questions des utilisateurs en se basant sur les documents pertinents récupérés
    """
    Build and return a ready-to-use ConversationalRetrievalChain.

    The chain does the following on every invoke():
        1. Reformulate the question using chat history (so follow-ups work)
        2. Retrieve TOP_K relevant chunks from FAISS
        3. Inject chunks + history into the prompt
        4. Send the full prompt to LLaMA via Ollama
        5. Return the answer + the source documents used

    Returns:
        A ConversationalRetrievalChain instance.
    """

    # ── 1. Load the vector store and create the retriever ─────────────────
    vectorstore = load_vectorstore()
    retriever   = get_retriever(vectorstore, k=TOP_K) #transforme FAISS en un retriever capable de chercher les TOP_K chunks les plus pertinents pour une question

    # ── 2. Define the LLM ─────────────────────────────────────────────────
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=OLLAMA_TEMPERATURE, #contrôle la créativité (faible = réponses plus factuelles)
        # Ask Ollama to keep the model loaded between calls (faster responses)
        keep_alive="5m", #garde le modèle en mémoire pour éviter de le recharger à chaque requête → réponses plus rapides
    )

    # ── 3. Prompt template ────────────────────────────────────────────────
    # This prompt is what the LLM actually receives.
    # {context}      → the retrieved document chunks
    # {chat_history} → previous Q&A turns
    # {question}     → the current (possibly reformulated) question
    #
    # The strict instruction in config.SYSTEM_PROMPT prevents the LLM from
    # making up answers when the context does not contain the information.
    prompt = PromptTemplate(
        input_variables=["context", "chat_history", "question"],
        template=SYSTEM_PROMPT,
    )

    # ── 4. Conversation memory ────────────────────────────────────────────
    # Stores the full exchange so the LLM can handle follow-up questions.
    # output_key="answer" tells Memory to save only the final answer,
    # not the intermediate source_documents key.
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    # ── 5. Assemble the chain ─────────────────────────────────────────────
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,   # so we can show sources in the UI
        verbose=False,
    ) # C’est la fusion finale : retrieval + augmentation + génération

    print(f"[chain] RAG chain ready  "
          f"(model={OLLAMA_MODEL}, top_k={TOP_K}, temp={OLLAMA_TEMPERATURE})\n")
    return chain
