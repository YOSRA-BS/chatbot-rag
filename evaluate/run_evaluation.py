# =============================================================================
# evaluate/run_evaluation.py
#
# Pipeline d'évaluation automatique du RAG
# - Détection et traduction des questions en français
# - Détection des questions hors sujet
# - Calcul des scores RAGAS (Faithfulness + Answer Relevancy)
# - Enregistrement complet des résultats dans MLflow
#
# Usage:
#     python evaluate/run_evaluation.py
#
# Prérequis:
#     1. ollama serve                  (LLM local actif)
#     2. python ingest.py              (index FAISS créé)
#     3. pip install ragas mlflow datasets
# =============================================================================
 
import json
import sys
import os
import time
 
# ── Permet à Python de trouver les modules du projet (chain, config, etc.) ──
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
import mlflow
import mlflow.sklearn
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.run_config import RunConfig # pour configurer les temps d'exécution de RAGAS
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import OllamaLLM
from langchain_community.embeddings import HuggingFaceEmbeddings

from chain import build_chain
from config import OLLAMA_MODEL, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
 
 
# =============================================================================
# CONFIGURATION
# =============================================================================
 
DATASET_PATH    = "evaluate/dataset.json"   # chemin vers votre dataset
EXPERIMENT_NAME = "RAG-Evaluation"          # nom affiché dans MLflow
SEUIL_QUALITE   = 0.5                       # score minimum acceptable (0 à 1)
LANGUE_DETECTEE = "auto"                    # "auto", "fr", ou "en"
 
 
# =============================================================================
# UTILITAIRES
# =============================================================================
 
def detecter_langue(question: str) -> str:
    """
    Détection simple de la langue basée sur des mots-clés français courants.
    Retourne 'fr' ou 'en'.
    """
    mots_francais = [
        "c'est", "quoi", "qu'est", "comment", "pourquoi", "quel",
        "quelle", "quels", "quelles", "est-ce", "expliquez", "décrivez",
        "donnez", "listez", "définissez", "différence", "avantages",
        "inconvénients", "utilisez", "fonctionne", "qu'", "les", "des",
        "une", "un", "le", "la"
    ]
    question_lower = question.lower()
    nb_mots_fr = sum(1 for mot in mots_francais if mot in question_lower)
    return "fr" if nb_mots_fr >= 2 else "en"
 
 
def traduire_vers_anglais(question: str, llm) -> str:
    """
    Traduit une question française vers l'anglais via Ollama.
    Utilisé uniquement si la langue détectée est 'fr'.
    """
    prompt = f"""Translate the following question from French to English.
Return ONLY the translated question, no explanation, no prefix.
 
French question: {question}
 
English translation:"""
 
    try:
        traduction = llm.invoke(prompt).strip()
        # Nettoyage : supprime les guillemets ou préfixes éventuels
        traduction = traduction.strip('"').strip("'")
        return traduction
    except Exception as e:
        print(f"  ⚠️  Traduction échouée ({e}) — utilisation de la question originale")
        return question
 
 
def verifier_hors_sujet(question: str, chain) -> bool:
    """
    Vérifie si une question est hors sujet en testant
    si le retriever trouve des documents pertinents.
    Retourne True si hors sujet, False si dans le sujet.
    """
    try:
        docs = chain.retriever.get_relevant_documents(question)
        if not docs:
            return True
        # Si le meilleur document est très court, probablement pas pertinent
        meilleur_doc = docs[0].page_content.strip()
        if len(meilleur_doc) < 50:
            return True
        return False
    except Exception:
        return False
 
 
def afficher_barre_progression(current: int, total: int, label: str = "") -> None:
    """Affiche une barre de progression simple dans le terminal."""
    pct      = int((current / total) * 30)
    barre    = "█" * pct + "░" * (30 - pct)
    pourcentage = int((current / total) * 100)
    print(f"\r  [{barre}] {pourcentage}% — {label}", end="", flush=True)
 
 
# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================
 
def main():
     # ── FORCER le chemin MLflow ──────────────────────────────
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MLFLOW_DB   = os.path.join(PROJECT_DIR, "mlflow.db")
    mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB}")
    print(f"\n📍  MLflow DB : {MLFLOW_DB}")
    # ─────────────────────────────────────────────────────────

    print("\n" + "═" * 60) 
    print("\n" + "═" * 60)
    print("   🚀  PIPELINE D'ÉVALUATION RAG + MLFLOW")
    print("═" * 60)
 
    # ── 1. Chargement du dataset ────────────────────────────────────────────
    print("\n📂  Chargement du dataset...")
    if not os.path.exists(DATASET_PATH):
        print(f"❌  Dataset introuvable : {DATASET_PATH}")
        print("    Créez d'abord evaluate/dataset.json")
        sys.exit(1)
 
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset_raw = json.load(f)
 
    print(f"    ✅  {len(dataset_raw)} questions chargées")
 
    # ── 2. Chargement des modèles locaux ────────────────────────────────────
    print("\n🤖  Chargement des modèles locaux...")
    print(f"    LLM        : {OLLAMA_MODEL} (via Ollama)")
    print(f"    Embeddings : {EMBEDDING_MODEL} (HuggingFace)")
 
    try:
        llm_local = OllamaLLM(model=OLLAMA_MODEL, temperature=0.1)
        # Test rapide de connexion Ollama
        llm_local.invoke("Hi")
        print("    ✅  Ollama connecté")
    except Exception as e:
        print(f"\n❌  Ollama non disponible : {e}")
        print("    Lancez : ollama serve")
        sys.exit(1)
 
    embeddings_local = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
    )
    print("    ✅  Embeddings chargés")
 
    # ── 3. Construction de la chaîne RAG ────────────────────────────────────
    print("\n🔗  Construction de la chaîne RAG...")
    try:
        chain = build_chain()
        print("    ✅  Chaîne RAG prête")
    except FileNotFoundError:
        print("❌  Index FAISS introuvable.")
        print("    Lancez d'abord : python ingest.py")
        sys.exit(1)
 
    # ── 4. Boucle d'évaluation ──────────────────────────────────────────────
    print(f"\n📝  Évaluation de {len(dataset_raw)} questions...\n")
    print("─" * 60)
 
    questions_finales  = []
    reponses_rag       = []
    contextes          = []
    ground_truths      = []
    questions_originales = []
    langues_detectees  = []
    hors_sujets        = []
    temps_reponses     = []
 
    questions_ignorees = 0
 
    for idx, item in enumerate(dataset_raw, 1):
 
        question_originale = item["question"]
        ground_truth       = item["ground_truth"]
 
        print(f"\n  [{idx}/{len(dataset_raw)}] {question_originale[:60]}...")
 
        # ── Détection de langue ──────────────────────────────────────────────
        langue = detecter_langue(question_originale)
        langues_detectees.append(langue)
        print(f"         Langue     : {'🇫🇷 Français' if langue == 'fr' else '🇬🇧 Anglais'}")
 
        # ── Traduction si français ───────────────────────────────────────────
        if langue == "fr":
            print("         Traduction : en cours...", end=" ")
            question_pour_rag = traduire_vers_anglais(question_originale, llm_local)
            print(f"✅")
            print(f"         → '{question_pour_rag[:60]}...'")
        else:
            question_pour_rag = question_originale
 
        # ── Vérification hors sujet ──────────────────────────────────────────
        hors_sujet = verifier_hors_sujet(question_pour_rag, chain)
        hors_sujets.append(hors_sujet)
 
        if hors_sujet:
            print("         Statut     : ⚠️  HORS SUJET — question ignorée")
            questions_ignorees += 1
            continue
 
        # ── Appel au RAG ─────────────────────────────────────────────────────
        print("         Statut     : ✅ Dans le sujet — appel RAG...")
        debut = time.time()
 
        try:
            result  = chain.invoke({"question": question_pour_rag})
            reponse = result.get("answer", "")
            sources = result.get("source_documents", [])
            # Reset memory for next question (evaluation should be independent)
            chain.memory.clear()
        except Exception as e:
            print(f"         ❌ Erreur RAG : {e}")
            continue
 
        duree = time.time() - debut
        temps_reponses.append(duree)
 
        # Extraction du contexte depuis les sources
        contexte = [doc.page_content for doc in sources] if sources else [""]
 
        print(f"         Réponse    : {reponse[:80]}...")
        print(f"         Durée      : {duree:.1f}s | Sources : {len(sources)}")
 
        # ── Sauvegarde pour RAGAS ────────────────────────────────────────────
        questions_finales.append(question_pour_rag)
        reponses_rag.append(reponse)
        contextes.append(contexte)
        ground_truths.append(ground_truth)
        questions_originales.append(question_originale)
 
    print("\n" + "─" * 60)
    print(f"\n  ✅  Questions évaluées   : {len(questions_finales)}")
    print(f"  ⚠️  Questions ignorées   : {questions_ignorees} (hors sujet)")
 
    if not questions_finales:
        print("\n❌  Aucune question n'a pu être évaluée.")
        sys.exit(1)
 
    # ── 5. Calcul des scores RAGAS ───────────────────────────────────────────
    print("\n📊  Calcul des scores RAGAS...")
    print("    (Faithfulness + Answer Relevancy)")
    print("    ⏳  Cela peut prendre quelques minutes...\n")
 
    ragas_dataset = Dataset.from_dict({
        "question"    : questions_finales,
        "answer"      : reponses_rag,
        "contexts"    : contextes,
        "ground_truth": ground_truths,
    })
 
    # Modèle plus léger pour RAGAS (évaluation seulement)
    from ragas.run_config import RunConfig
    run_config = RunConfig(max_workers=1, timeout=1200)  # 20 minutes timeout, séquentiel

    ragas_llm = LangchainLLMWrapper(
        OllamaLLM(model="qwen2:0.5b", temperature=0)  # Modèle léger et rapide au lieu de llama3.2 pour l'évaluation RAGAS car RAGAS lance 40 tâches en parallèle (20 pour chaque métrique). Ollama ne gère pas bien le parallélisme sur un PC local → surcharge et timeouts
    )
    ragas_emb = LangchainEmbeddingsWrapper(embeddings_local)
 
    try:
        resultats = evaluate(
            dataset   = ragas_dataset,
            metrics   = [faithfulness, answer_relevancy],
            llm       = ragas_llm,
            embeddings= ragas_emb,
            run_config= run_config,
        )
    except Exception as e:
        print(f"❌  Erreur RAGAS : {e}")
        sys.exit(1)

    # Convertir en DataFrame pandas pour calculer les moyennes
    df_resultats = resultats.to_pandas()
    score_faithfulness     = df_resultats["faithfulness"].mean()
    score_answer_relevancy = df_resultats["answer_relevancy"].mean()
    score_global           = (score_faithfulness + score_answer_relevancy) / 2
    temps_moyen            = sum(temps_reponses) / len(temps_reponses) if temps_reponses else 0
 
    print(f"\n  ✅  Faithfulness      : {score_faithfulness:.2%}")
    print(f"  ✅  Answer Relevancy  : {score_answer_relevancy:.2%}")
    print(f"  🏆  Score global      : {score_global:.2%}")
    print(f"  ⏱️   Temps moyen/réponse : {temps_moyen:.1f}s")
 
    # ── 6. Enregistrement dans MLflow ────────────────────────────────────────
    print("\n📈  Enregistrement dans MLflow...")
 
    mlflow.set_experiment(EXPERIMENT_NAME)
 
    with mlflow.start_run(run_name=f"eval_{OLLAMA_MODEL}"):
 
        # ── Paramètres du système ────────────────────────────────────────────
        mlflow.log_param("llm_model",            OLLAMA_MODEL)
        mlflow.log_param("embedding_model",      EMBEDDING_MODEL)
        mlflow.log_param("chunk_size",           CHUNK_SIZE)
        mlflow.log_param("chunk_overlap",        CHUNK_OVERLAP)
        mlflow.log_param("top_k",                TOP_K)
        mlflow.log_param("nb_questions_total",   len(dataset_raw))
        mlflow.log_param("nb_questions_evaluees",len(questions_finales))
        mlflow.log_param("nb_questions_ignorees",questions_ignorees)
        mlflow.log_param("seuil_qualite",        SEUIL_QUALITE)
 
        # ── Métriques RAGAS ──────────────────────────────────────────────────
        mlflow.log_metric("faithfulness",        score_faithfulness)
        mlflow.log_metric("answer_relevancy",    score_answer_relevancy)
        mlflow.log_metric("score_global",        score_global)
        mlflow.log_metric("temps_moyen_reponse", round(temps_moyen, 2))
 
        # ── Tableau détaillé des résultats ───────────────────────────────────
        df_resultats = pd.DataFrame({
            "question_originale" : questions_originales,
            "question_anglais"   : questions_finales,
            "reponse_rag"        : reponses_rag,
            "ground_truth"       : ground_truths,
        })
 
        # Sauvegarde du tableau en CSV et log dans MLflow
        csv_path = "evaluate/resultats_evaluation.csv"
        os.makedirs("evaluate", exist_ok=True)
        df_resultats.to_csv(csv_path, index=False, encoding="utf-8")
        mlflow.log_artifact(csv_path)
 
        # ── Tag de qualité ───────────────────────────────────────────────────
        qualite = "✅ ACCEPTABLE" if score_global >= SEUIL_QUALITE else "❌ INSUFFISANT"
        mlflow.set_tag("qualite",    qualite)
        mlflow.set_tag("llm",        OLLAMA_MODEL)
        mlflow.set_tag("evaluation", "RAGAS")
 
        print("    ✅  Résultats enregistrés dans MLflow")
        print(f"    📁  CSV sauvegardé : {csv_path}")
 
    # ── 7. Rapport final ─────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("   📋  RAPPORT FINAL D'ÉVALUATION")
    print("═" * 60)
    print(f"\n  Modèle LLM          : {OLLAMA_MODEL}")
    print(f"  Embedding           : {EMBEDDING_MODEL}")
    print(f"  Chunk size          : {CHUNK_SIZE}")
    print(f"  Top-K               : {TOP_K}")
    print(f"\n  Questions testées   : {len(dataset_raw)}")
    print(f"  Questions évaluées  : {len(questions_finales)}")
    print(f"  Questions ignorées  : {questions_ignorees} (hors sujet)")
    print(f"\n  Faithfulness        : {score_faithfulness:.2%}")
    print(f"  Answer Relevancy    : {score_answer_relevancy:.2%}")
    print(f"  Score global        : {score_global:.2%}")
    print(f"  Temps moyen/réponse : {temps_moyen:.1f}s")
    print(f"\n  Seuil minimum       : {SEUIL_QUALITE:.0%}")
    print(f"  Qualité             : {qualite}")
 
    print("\n" + "─" * 60)
    print("  📊  Visualiser les résultats dans MLflow :")
    print("      mlflow ui   →   http://localhost:5000")
    print("─" * 60 + "\n")
 
    # ── 8. Vérification du seuil (bloque le CI/CD si insuffisant) ───────────
    if score_global < SEUIL_QUALITE:
        print(f"❌  Score insuffisant ({score_global:.2%} < {SEUIL_QUALITE:.0%})")
        print("    Le pipeline CI/CD sera bloqué.")
        sys.exit(1)
    else:
        print(f"✅  Score acceptable — pipeline CI/CD peut continuer.\n")
        sys.exit(0)
 
 
# =============================================================================
if __name__ == "__main__":
    main()