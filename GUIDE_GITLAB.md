# 📘 Guide Complet GitLab CI/CD/CT pour LLMOps — Première fois

> 🎯 Ce guide vous accompagne étape par étape pour configurer et utiliser votre pipeline GitLab CI/CD/CT complète pour un projet LLMOps (RAG Chatbot).

---

## 📑 Table des matières

1. [Prérequis](#prérequis)
2. [Configuration initiale GitLab](#configuration-initiale-gitlab)
3. [Structures des fichiers](#structures-des-fichiers)
4. [Pipeline expliquée en détail](#pipeline-expliquée-en-détail)
5. [Déploiement et monitoring](#déploiement-et-monitoring)
6. [Dépannage courant](#dépannage-courant)
7. [Bonnes pratiques](#bonnes-pratiques)

---

## 🔧 Prérequis

### Avant de commencer, assurez-vous d'avoir :

```
✅ Un compte GitLab.com OU une instance GitLab Self-Hosted
✅ Un projet Git créé sur GitLab
✅ GitLab Container Registry (recommandé - intégré à GitLab)
✅ Accès aux CI/CD Runners (partagés par défaut sur GitLab.com)
✅ Les droits "Developer" ou "Maintainer" sur le projet
```

### Vérifiez votre accès GitLab

```bash
# Dans votre terminal local
cd /path/to/mon-chatbot

# Vérifiez que vous êtes connected à GitLab
git remote -v
# Devrait afficher quelque chose comme:
# origin  https://gitlab.com/votre-username/mon-chatbot.git (fetch)
# origin  https://gitlab.com/votre-username/mon-chatbot.git (push)
```

---

## 🎯 Pourquoi GitLab Container Registry ?

**GitLab Container Registry est LA solution recommandée** pour votre pipeline LLMOps :

### ✅ Avantages par rapport à Docker Hub :

- **Intégration native** : Pas besoin de comptes séparés ou de tokens externes
- **Sécurité renforcée** : Images privées par défaut, contrôle d'accès granulaire
- **Performance** : Images stockées près de vos runners GitLab
- **Gratuit** : Inclus dans GitLab.com (limites raisonnables)
- **Automatisation** : Variables `CI_REGISTRY_*` fournies automatiquement
- **Versioning** : Tags automatiques basés sur les commits Git

### 🚫 Inconvénients potentiels de Docker Hub :

- Limites de taux (pulls anonymes)
- Gestion de tokens séparés
- Moins intégré à GitLab CI/CD
- Risques de sécurité pour les images privées

**Verdict** : Utilisez GitLab Container Registry ! C'est déjà configuré dans votre `.gitlab-ci.yml`.

---

## 🚀 Configuration initiale GitLab

### Étape 1 : Créer le projet sur GitLab

#### Option A : Via l'interface web

1. Allez sur [GitLab.com](https://gitlab.com)
2. Cliquez sur **"+ Nouveau projet"** (ou **"New project"**)
3. Choisissez **"Créer un projet vierge"** (Blank project)
4. Remplissez :
   - **Nom du projet** : `mon-chatbot`
   - **Slug du projet** : Auto-complété (ex: `mon-chatbot`)
   - **Visibilité** : Private ou Public (selon vos besoins)
5. Cliquez **"Créer un projet"**

#### Option B : Via CLI

```bash
# Si vous avez un compte GitLab CLI configuré
git remote add origin https://gitlab.com/votre-username/mon-chatbot.git
git branch -M main
git push -u origin main
```

### Étape 2 : Configurer les Runners

Les **Runners** exécutent vos jobs de pipeline. GitLab fournit des runners partagés gratuits.

#### Vérifier les runners disponibles

1. Dans GitLab, allez dans : **Paramètres (Settings) → CI/CD → Runners**
2. Vous devriez voir les **"Shared runners"** disponibles

```
✅ Si vous voyez des runners (docker, shell, etc.), c'est OK !
❌ Si vous ne voyez rien, vous aurez besoin de configurer un runner (voir section "Runner personnalisé")
```

#### Runner personnalisé (optionnel)

Si vous avez besoin d'un runner local ou sur serveur :

```bash
# 1. Installez GitLab Runner
# Sur macOS
brew install gitlab-runner

# Sur Linux (Debian/Ubuntu)
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | bash
sudo apt-get install gitlab-runner

# 2. Enregistrez le runner
sudo gitlab-runner register \
  --url https://gitlab.com/ \
  --token glrt_xxxxx \
  --description "Docker Runner" \
  --executor docker \
  --docker-image docker:20.10.16 \
  --docker-privileged

# 3. Lancez le runner
sudo gitlab-runner run
```

### Étape 3 : Configurer les variables CI/CD

Les **variables** sont des secrets/paramètres accessibles dans votre pipeline.

1. Allez dans : **Paramètres (Settings) → CI/CD → Variables**
2. Cliquez sur **"Ajouter une variable"**

#### Variables recommandées à ajouter:

| Variable | Valeur | Type | Scope |
|----------|--------|------|-------|
| `CI_REGISTRY_USER` | votre-username | Variable | All |
| `CI_REGISTRY_PASSWORD` | token-personnel | Protected | All |
| `MLFLOW_TRACKING_URI` | http://mlflow-server:5000 | Variable | All |
| `PRODUCTION_DEPLOY_URL` | votre-api-prod.com | Protected | Production |

**Note importante** : Pour GitLab Container Registry, les variables `CI_REGISTRY_USER` et `CI_REGISTRY_PASSWORD` sont automatiquement fournies par GitLab. Vous n'avez pas besoin de les définir manuellement - elles utilisent votre token de déploiement automatique.

**Si vous voulez définir manuellement un token** (optionnel) :
1. Allez dans **Profil (Profile) → Paramètres d'accès (Access tokens)**
2. Cliquez **"Ajouter un nouveau token"**
3. Donnez-lui les permissions : `api`, `read_registry`, `write_registry`
4. Copiez le token et mettez-le dans `CI_REGISTRY_PASSWORD`

### Étape 4 : Pusher vos fichiers vers GitLab

```bash
# Depuis la racine de votre projet
cd /path/to/mon-chatbot

# Les fichiers suivants DOIVENT être à la racine :
# - .gitlab-ci.yml (pipeline)
# - Dockerfile (image Docker)
# - requirements.txt (dépendances Python)
# - pytest.ini (config tests)

# Commit et push
git add .gitlab-ci.yml Dockerfile
git commit -m "feat: add GitLab CI/CD pipeline with Docker, tests, evaluation"
git push origin main
```

### Étape 5 : Vérifier que la pipeline génère

1. Allez dans GitLab : votre project → **Construire (Build) → Pipelines**
2. Vous devriez voir une **nouvelle pipeline** en cours d'exécution

```
✅ Pipeline visible = Succès !
⏳ Si elle est en "pending", attendez quelques secondes
❌ Si elle est en erreur, voir section "Dépannage"
```

---

## 📁 Structures des fichiers

Après cette configuration, votre projet devrait ressembler à :

```
mon-chatbot/
├── .gitlab-ci.yml           ← ⭐ FICHIER PRINCIPAL (pipeline)
├── Dockerfile                ← ⭐ Image Docker
├── requirements.txt          ← Dépendances Python
├── pytest.ini                ← Config tests
├── config.py
├── chain.py
├── chatbot.py
├── ingest.py
├── embeddings.py
│
├── documents/                ← Documents RAG
│   ├── 01_How_to_Fine_Tune_LLM_HuggingFace.txt
│   ├── 02_Large_Language_Model_Tutorial.txt
│   └── ...
│
├── tests/
│   ├── unitaires/
│   │   ├── test_chain.py
│   │   ├── test_embeddings.py
│   │   ├── test_loader.py
│   │   └── ...
│   └── integration/
│       ├── test_full_pipeline.py
│       └── test_evaluation.py
│
├── evaluate/
│   ├── run_evaluation.py
│   ├── dataset.json
│   └── resultats_evaluation.csv
│
└── mlruns/                   ← Artefacts MLflow (créé lors pipeline)
    └── ...
```

---

## 🔄 Pipeline expliquée en détail

Voici ce que fait **chaque stage** de votre pipeline :

### **Stage 1️⃣ : BUILD** — Construction Docker

**Fichier déclenché** : `.gitlab-ci.yml` → `build:docker` job

```yaml
build:docker:
  stage: build
  image: docker:20.10.16          # Utilise l'image Docker officielle
  services:
    - docker:20.10.16-dind        # "docker in docker"
  script:
    - docker build -t $IMAGE_NAME:$IMAGE_TAG .   # Build image
    - docker push $IMAGE_NAME:$IMAGE_TAG         # Push vers registry
```

**Qu'est-ce qui se passe** :

1. **Login au registry** GitLab avec vos credentials
2. **Parse le Dockerfile** et construit l'image
3. **Installe les dépendances** (numpy, torch, langchain, etc.)
4. **Tag l'image** avec le commit SHA (ex: `registry.gitlab.com/user/repo:a1b2c3d4`)
5. **Push vers GitLab Container Registry**

**Résultat** : Image Docker disponible dans **Déployer (Deploy) → Registre de conteneurs**

#### Accéder à votre image Docker :

```bash
# Après le build réussi, vous pouvez faire :
docker pull registry.gitlab.com/votre-username/mon-chatbot:latest

# Lancer un conteneur
docker run -it registry.gitlab.com/votre-username/mon-chatbot:latest bash
```

---

### **Stage 2️⃣ : TEST** — Tests Pytest

**Deux jobs en parallèle** :

#### A) `test:unit` — Tests unitaires

```yaml
test:unit:
  stage: test
  image: python:3.11-slim
  script:
    - pip install -r requirements.txt
    - pytest tests/unitaires/ --cov=. --cov-report=xml
```

**Qu'est-ce qui se passe** :

1. Lance une **image Python 3.11 vierge**
2. Installe vos dépendances
3. Exécute **tous les tests** dans `tests/unitaires/`
4. **Mesure la couverture de code** (% du code testé)
5. Génère un rapport XML pour GitLab

**Résultat dans GitLab** :
- Tab **"Tests"** affiche résumé des tests
- Tab **"Code Coverage"** affiche % couvert
- Artefacts téléchargeables : `coverage.xml`, `test-results-unit.xml`

#### B) `test:integration` — Tests d'intégration

```yaml
test:integration:
  stage: test
  script:
    - pytest tests/integration/ -m "not requires_ollama"
```

Similaire aux tests unitaires, mais teste **les composants ensemble**.

---

### **Stage 3️⃣ : EVALUATE** — Évaluation Ragas

**Job** : `evaluate:ragas`

```yaml
evaluate:ragas:
  stage: evaluate
  script:
    - python evaluate/run_evaluation.py
    - python -c "check quality score >= 0.5"
```

**Qu'est-ce qui se passe** :

1. **Charge votre dataset** (`evaluate/dataset.json`)
2. **Exécute les questions** via votre RAG
3. **Calcule les métriques** Ragas :
   - **Faithfulness** : Réponse fidèle aux sources ?
   - **Answer Relevancy** : Réponse pertinente à la question ?
4. **Vérifie le seuil** : score moyen ≥ 0.5 requis
5. **Génère rapport** : `evaluation_results.json`

**Résultat** :
- ❌ Si score < 0.5 → Pipeline continue (allow_failure: true)
- ✅ Si score ≥ 0.5 → Succès

#### Vérifier les résultats d'évaluation :

Dans GitLab, allez dans **Construire (Build) → Jobs** → cliquez sur `evaluate:ragas`

```json
{
  "faithfulness": 0.82,
  "answer_relevancy": 0.79,
  "execution_time": 15.3,
  "status": "completed"
}
```

---

### **Stage 4️⃣ : SECURE** — Scan de sécurité

**Deux jobs** :

#### A) `security:bandit` — Scan code Python

```bash
# Cherche des bugs de sécurité :
- Injections SQL
- Accès fichiers sensibles
- Credentials hardcodées
```

#### B) `security:dependency-check` — Scan dépendances

```bash
# Cherche des CVE (Common Vulnerabilities)
- Packages vulnérables
- Versions obsolètes
```

**Résultat dans GitLab** :
- Tab **"Sécurité"** affiche vulnérabilités trouvées
- Fichiers rapports : `bandit-report.json`, `safety-report.json`

---

### **Stage 5️⃣ : METRICS** — Logging MLflow

**Job** : `metrics:log`

```yaml
metrics:log:
  stage: metrics
  script:
    - python -c "
        mlflow.set_tracking_uri('file:///app/mlruns')
        mlflow.log_param('torch_version', '2.2.2')
        mlflow.log_metric('test_coverage', 85.2)
      "
```

**Qu'est-ce qui se passe** :

1. **Crée un run MLflow** avec ID unique
2. **Log les tags** :
   - `gitlab_pipeline_id`
   - `gitlab_commit_sha`
   - `gitlab_branch`
3. **Log les paramètres** (versions des libs)
4. **Log les métriques** (scores, temps d'exécution)
5. **Sauvegarde artefacts** (rapports de tests)

**Accéder à MLflow** :

```bash
# Localement ou sur serveur
mlflow ui
# Ouvre http://localhost:5000
```

---

### **Stage 6️⃣ : DEPLOY** — Déploiement

**Deux jobs** (mutuellement exclusifs) :

#### A) `deploy:staging` — Vers environnement de test

```yaml
deploy:staging:
  stage: deploy
  only:
    - develop          # Déclencht seulement sur branche 'develop'
  when: manual         # Déclenché MANUELLEMENT
```

**Déclencher manuellement** :
1. Dans GitLab, **Construire (Build) → Pipelines**
2. Cliquez sur la pipeline
3. Cherchez le bouton **▶️ Play** à côté du job `deploy:staging`
4. Cliquez pour lancer le déploiement

#### B) `deploy:production` — Vers production

```yaml
deploy:production:
  stage: deploy
  only:
    - tags            # Déclencht seulement sur tags Git (ex: v1.0.0)
  when: manual
```

**Déclencher** :
1. Créez un **tag Git** :
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
2. GitLab créera une pipeline pour ce tag
3. Cliquez le bouton **▶️** à côté de `deploy:production`

---

## 📊 Déploiement et Monitoring

### Voir l'historique des pipelines

**Chemin dans GitLab** :
```
Projet → Construire (Build) → Pipelines
```

Vous verrez un tableau avec :

```
| Status | Pipeline ID | Branch | Commit | Durée | Actions |
|--------|-------------|--------|--------|-------|---------|
| ✅     | #12345      | main   | a1b2c3 | 8m    | ⋮ Voir |
| ⏳     | #12344      | develop| d4e5f6 | EN... | ⋮ Voir |
| ❌     | #12343      | feat/* | g7h8i9 | 3m    | ⋮ Voir |
```

### Analyser une pipeline ayant échoué

1. Cliquez sur la pipeline échouée
2. Voir le **"Failed"** en rouge
3. Cliquez sur le **job échoué** (ex: `test:unit`)
4. Lisez la **sortie complète** pour voir l'erreur

**Exemple erreur courante** :

```
ERROR: pip install torch failed
Solution: Vérifiez que numpy est installé EN PREMIER

# ❌ MAuvais
pip install -r requirements.txt

# ✅ Bon
pip install "numpy<2"
pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt (reste)
```

### Exporter les résultats

Dans GitLab, chaque job génère des **artefacts** (fichiers générés) :

```
Construire (Build) → Jobs → [Sélectionner job]
    → Onglet "Artefacts" → Télécharger
```

**Fichiers disponibles** :
- `coverage.xml` — Couverture des tests
- `test-results-unit.xml` — Résultats détaillés tests
- `bandit-report.json` — Problèmes de sécurité
- `evaluation_results.json` — Scores Ragas
- `mlruns/` — Historique MLflow complet

---

## 🔧 Dépannage courant

### ❌ Erreur 1 : "No runners available"

**Symptôme** : Pipeline reste en "pending" depuis 10+ minutes

**Cause** : Aucun runner disponible pour exécuter les jobs

**Solution** :

```bash
# Option 1 : Utiliser les runners partagés GitLab (gratuit)
# Allez dans Paramètres → CI/CD → Runners
# Vérifiez que vous voyez au moins 1 runner partagé

# Option 2 : Configurer un runner personnel
gitlab-runner register \
  --url https://gitlab.com/ \
  --token glrt_xxx \
  --executor docker

# Option 3 : Spécifiez les tags attendus
# Modifiez .gitlab-ci.yml :
build:docker:
  tags:
    - docker      # Assure qu'un runner docker répond
```

---

### ❌ Erreur 2 : "docker: command not found"

**Symptôme** : Job `build:docker` échoue avec "docker: command not found"

**Cause** : Services Docker non disponible

**Solution dans .gitlab-ci.yml** :

```yaml
build:docker:
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind    # ⭐ IMPORTANT : ajouter cette ligne
```

---

### ❌ Erreur 3 : "403 Forbidden" lors du push

**Symptôme** : "GitLab Registry: error 403"

**Cause** : Credentials GitLab incorrects

**Solution** :

```bash
# 1. Générer un token personnel
# GitLab → Profil → Access Tokens
# Domaines : api, read_registry, write_registry

# 2. Configurer les variables CI/CD
# GitLab → Paramètres → CI/CD → Variables
# Ajouter :
#   CI_REGISTRY_USER = votre-username
#   CI_REGISTRY_PASSWORD = token-personnel

# 3. S'assurer que le registre est bon
# Dans .gitlab-ci.yml :
variables:
  REGISTRY: "registry.gitlab.com"   # ✅ Correct pour GitLab.com
```

---

### ❌ Erreur 4 : "torch import failed" dans tests

**Symptôme** :

```
ModuleNotFoundError: No module named 'torch'
```

**Cause** : numpy 2.x incompatible avec torch

**Solution dans .gitlab-ci.yml** :

```yaml
before_script:
  - pip install --upgrade pip
  - pip install "numpy<2"    # ⭐ TOUJOURS EN PREMIER
  - pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
  - pip install -r requirements.txt
```

---

### ❌ Erreur 5 : "Ollama not running" dans évaluation

**Symptôme** : Job `evaluate:ragas` échoue avec "Could not connect to Ollama"

**Cause** : Ollama n'est pas disponible en CI/CD (normal)

**Solution** : Le `.gitlab-ci.yml` gère ça avec :

```yaml
allow_failure: true    # Pipeline continue même si ça échoue
```

Et il crée des **résultats mock** pour tester le pipeline :

```python
if Ollama not available:
    create_mock_evaluation_results()
```

---

## ✅ Bonnes pratiques

### 1. Commits et branches

```bash
# Utilisez une branche pour chaque feature
git checkout -b feature/improve-rag

# Commitez souvent avec messages clairs
git commit -m "feat: improve retrieval accuracy"

# Poussez vers GitLab
git push origin feature/improve-rag

# GitLab créera une pipeline à chaque push
```

### 2. Protéger votre branche main

**Paramètres → Repository → Protected branches**

```
Branche "main" :
- ✅ Require approval from code owners
- ✅ Require pipeline to succeed
- ✅ Require status checks to pass
```

**Résultat** : Aucun merge possible si la pipeline échoue

### 3. Monitorer les performances

**Construire → Analytics** permet de voir :

- Temps moyen d'exécution des pipelines
- Taux de réussite/échec
- Jobs qui prennent le plus de temps

### 4. Cacher les variables sensibles

```yaml
# ❌ JAMAIS faire ça
variables:
  DB_PASSWORD: "my-secret-password"

# ✅ Faire ça
# Dans GitLab : Paramètres → CI/CD → Variables
# Ajouter variable "DB_PASSWORD" avec valeur
# Puis dans .gitlab-ci.yml :
script:
  - echo $DB_PASSWORD    # Automatiquement remplacé
```

### 5. Utiliser les caches

```yaml
cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths:
    - .cache/pip           # Cache npm/pip
    - .pytest_cache        # Cache tests
    - node_modules/        # Si utilisation Node.js
```

**Résultat** : Jobs plus rapides (pas de réinstallation dépendances chaque fois)

### 6. Planifier des pipelines récurrentes

**Construire → Planified pipelines**

Créer une pipeline qui s'exécute automatiquement :

```
Chaque jour à 2:00 AM sur la branche 'main'
Chaque semaine le vendredi pour audit sécurité
```

---

## 🎓 Résumé — Votre premier déploiement

### Checklist pour premiers pas :

```
☐ J'ai créé un projet sur GitLab.com
☐ J'ai pushé mon code avec Dockerfile et .gitlab-ci.yml
☐ Je vois une pipeline dans "Construire → Pipelines"
☐ Stage BUILD est complété (image Docker créée)
☐ Stage TEST affiche résultats des tests
☐ Stage EVALUATE montre scores Ragas
☐ Stage SECURE reporte vulnérabilités
☐ Stage METRICS enregistre dans MLflow
☐ J'ai déclenché DEPLOY:STAGING manuellement
☐ Mon container est deployé ✅
```

---

## 📞 Obtenir de l'aide

### Ressources utiles

- [Documentation GitLab CI/CD](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner documentation](https://docs.gitlab.com/runner/)
- [Docker documentation](https://docs.docker.com/)
- [Pytest documentation](https://docs.pytest.org/)
- [Ragas documentation](https://docs.ragas.io/)
- [MLflow documentation](https://mlflow.org/docs/)

### Communauté GitLab

- Forum : https://forum.gitlab.com/
- Issues GitLab : https://gitlab.com/gitlab-org/gitlab/-/issues

---

**🎉 Félicitations ! Vous avez maintenant une pipeline CI/CD/CT complète et profesionnelle ! 🚀**

