# Test Suite Documentation — RAG Chatbot LLMOps Pipeline

## Vue d'ensemble

Cette suite de tests complète assure la robustesse, la qualité et l'intégrité du pipeline RAG (Retrieval-Augmented Generation) pour le chatbot LLMOps. Elle suit les meilleures pratiques de test avec une séparation claire entre tests unitaires et d'intégration.

## Structure des tests

```
tests/
├── unitaires/                    # Tests unitaires des composants individuels
│   ├── conftest.py              # Fixtures partagées pour les tests unitaires
│   ├── test_config.py           # Tests de configuration
│   ├── test_loader.py           # Tests de chargement de documents
│   ├── test_embeddings.py       # Tests d'embeddings et vectorstore
│   ├── test_chain.py            # Tests de construction de chaîne RAG
│   ├── test_ingest.py           # Tests de pipeline d'ingestion
│   └── test_data_ingest.py      # Tests de composants d'ingestion (inspirés GitHub)
├── integration/                 # Tests d'intégration
│   ├── test_full_pipeline.py    # Tests du pipeline complet
│   └── test_evaluation.py       # Tests du système d'évaluation
└── pytest.ini                   # Configuration pytest
```

## Types de tests

### Tests unitaires (`tests/unitaires/`)

Tests isolés pour chaque composant individuel :

- **Configuration** : Validation des paramètres et constantes
- **Chargement** : Support des formats PDF, DOCX, TXT
- **Embeddings** : Splitting, création d'embeddings, FAISS
- **Chaîne RAG** : Construction et configuration du pipeline
- **Ingestion** : Pipeline de préparation des documents
- **Composants** : Classes utilitaires et helpers

### Tests d'intégration (`tests/integration/`)

Tests de l'interaction entre composants :

- **Pipeline complet** : Du document à la réponse
- **Évaluation** : Métriques RAGAS et MLflow
- **Gestion d'erreurs** : Robustesse du système

## Exécution des tests

### Exécution complète
```bash
pytest
```

### Exécution par type
```bash
# Tests unitaires uniquement
pytest tests/unitaires/

# Tests d'intégration uniquement
pytest tests/integration/

# Tests avec couverture
pytest --cov=. --cov-report=html
```

### Exécution sélective
```bash
# Test spécifique
pytest tests/unitaires/test_config.py::TestConfigConstants::test_paths_are_strings

# Tests avec marker
pytest -m "unit"
pytest -m "integration"
```

## Fixtures et mocks

### Fixtures principales (`conftest.py`)

- `tmp_dirs` : Répertoires temporaires pour tests I/O
- `sample_documents` : Documents de test échantillon
- `mock_embedding_model` : Mock du modèle d'embeddings
- `mock_vectorstore` : Mock FAISS vectorstore
- `mock_llm` : Mock du modèle de langage
- `test_config` : Configuration de test

### Stratégie de mocking

- **Modèles externes** : Ollama, HuggingFace embeddings
- **Dépendances I/O** : Système de fichiers, FAISS
- **APIs externes** : MLflow, services cloud
- **Composants lents** : Évite les téléchargements et calculs lourds

## Bonnes pratiques appliquées

### Naming
- `test_*` pour fonctions de test
- `Test*` pour classes de test
- Noms descriptifs expliquant le comportement testé

### Isolation
- Chaque test est indépendant
- Utilisation de fixtures pour setup/teardown
- Mocks pour éviter les effets de bord

### Lisibilité
- Commentaires expliquant l'objectif de chaque test
- Structure claire : Arrange, Act, Assert
- Messages d'erreur informatifs

### Maintenabilité
- Tests modulaires et extensibles
- Fixtures réutilisables
- Configuration centralisée

## Métriques de qualité

### Couverture cible
- **Lignes** : ≥ 80%
- **Branches** : ≥ 75%
- **Fonctions** : ≥ 90%

### Performance
- Tests unitaires : < 100ms chacun
- Tests d'intégration : < 5s chacun
- Suite complète : < 2min

## Intégration CI/CD

### GitHub Actions (recommandé)
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov
    pytest --cov=. --cov-report=xml
```

### Pré-commit hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
```

## Extension de la suite

### Ajout de tests unitaires
1. Créer `test_nouveau_module.py` dans `tests/unitaires/`
2. Ajouter fixtures si nécessaire dans `conftest.py`
3. Suivre le pattern : classe `Test*`, méthodes `test_*`

### Ajout de tests d'intégration
1. Créer `test_nouvelle_integration.py` dans `tests/integration/`
2. Tester les interactions réelles entre composants
3. Utiliser des mocks pour les dépendances externes

### Nouveaux markers
Ajouter dans `pytest.ini` :
```ini
markers =
    nouveau_marker: Description du marker
```

## Dépannage

### Tests lents
- Vérifier les mocks : éviter les appels réels
- Utiliser `@pytest.mark.slow` pour les exclure
- Optimiser les fixtures

### Échecs intermittents
- Vérifier l'isolation entre tests
- Éviter les dépendances temporelles
- Utiliser des seeds pour la randomisation

### Problèmes de dépendances
- Installer tous les packages de `requirements.txt`
- Vérifier les versions compatibles
- Utiliser des environnements virtuels

## Contribution

### Standards de code
- PEP 8 pour le code de test
- Docstrings pour classes et fonctions complexes
- Commentaires pour logique non-évidente

### Review process
- Tous les tests doivent passer
- Couverture maintenue ou améliorée
- Pas de régression introduite

Cette suite de tests constitue une base solide pour l'extension et la maintenance du pipeline RAG, assurant qualité et fiabilité dans un environnement de production.