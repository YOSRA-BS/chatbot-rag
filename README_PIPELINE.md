# 🚀 README — Pipeline GitLab CI/CD/CT pour LLMOps

## 📋 Vue d'ensemble

Cette pipeline automatise l'intégralité du pipeline LLMOps pour votre RAG Chatbot :

```
Code Push
   ↓
┌──────────────────────────────────────┐
│  1. BUILD: Docker Image              │ ⏱️  ~5 min
│  - Construct Dockerfile              │
│  - Install dependencies              │
│  - Push to registry                  │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  2. TEST: Unit + Integration Tests   │ ⏱️  ~10 min
│  - Run pytest                        │
│  - Generate coverage report          │
│  - JUnit XML for CI/CD               │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  3. EVALUATE: Ragas Quality Check    │ ⏱️  ~15 min
│  - Load evaluation dataset           │
│  - Run RAG queries                   │
│  - Calculate Faithfulness & Relevancy│
│  - Check quality threshold           │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  4. SECURE: Security Scanning        │ ⏱️  ~5 min
│  - Bandit: code vulnerabilities      │
│  - Safety: dependency CVEs           │
│  - pip-audit: package audit          │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  5. METRICS: MLflow Logging          │ ⏱️  ~2 min
│  - Log pipeline parameters           │
│  - Store test coverage               │
│  - Archive evaluation results        │
└──────────────────────────────────────┘
   ↓
┌──────────────────────────────────────┐
│  6. DEPLOY: Manual Deployment        │ ⏱️  ~5 min
│  - Staging (develop branch)          │
│  - Production (git tags)             │
│  Both require manual trigger         │
└──────────────────────────────────────┘
```

**Total execution time**: ~42 minutes end-to-end

---

## 📁 Files Created

### Core Files

| File | Purpose | Notes |
|------|---------|-------|
| `.gitlab-ci.yml` | **Pipeline definition** | GitLab reads this automatically |
| `Dockerfile` | Docker image build | Multi-stage build for optimization |
| `.env.example` | Template for CI/CD variables | Copy and customize |
| `GUIDE_GITLAB.md` | **Complete setup guide** | Start here if new to GitLab |

### Helper Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `scripts/test_pipeline_locally.py` | Test pipeline without pushing | `python scripts/test_pipeline_locally.py` |

---

## ⚡ Quick Start (5 min)

### 1. Setup GitLab Project

```bash
# Create GitLab project
# https://gitlab.com/projects/new

# Clone and setup
cd mon-chatbot
git remote add origin https://gitlab.com/YOUR_USERNAME/mon-chatbot.git
```

### 2. Add Variables to GitLab

Go to: **GitLab** → **Paramètres (Settings)** → **CI/CD** → **Variables**

Add these variables:

```
CI_REGISTRY_USER = your-username
CI_REGISTRY_PASSWORD = glrt_xxx (personal access token)
```

### 3. Push to Trigger Pipeline

```bash
git add .gitlab-ci.yml Dockerfile Dockerfile .env.example GUIDE_GITLAB.md
git commit -m "feat: add complete CI/CD pipeline"
git push origin main
```

### 4. Monitor Pipeline

Go to: **GitLab** → **Build** → **Pipelines**

Watch your pipeline run! 🎉

---

## 🔍 Testing Locally First

Before pushing to GitLab, test the pipeline locally:

```bash
cd mon-chatbot

# Test all stages
python scripts/test_pipeline_locally.py

# Test specific stage
python scripts/test_pipeline_locally.py --stage build
python scripts/test_pipeline_locally.py --stage test --verbose

# Skip prerequisite checks
python scripts/test_pipeline_locally.py --skip-prereq
```

---

## 📊 Understanding the Pipeline

### Stage 1: BUILD

```yaml
build:docker:
  image: docker:20.10.16
  script:
    - docker build -t $IMAGE_NAME:$IMAGE_TAG .
    - docker push $IMAGE_NAME:$IMAGE_TAG
```

**What it does**:
- Builds Docker image from Dockerfile
- Tags with commit SHA
- Pushes to GitLab Container Registry

**In GitLab UI**: **Deploy** → **Container Registry**

---

### Stage 2: TEST

Two parallel jobs:

#### A) Unit Tests
```bash
pytest tests/unitaires/ --cov=. --cov-report=xml
```

#### B) Integration Tests
```bash
pytest tests/integration/ -m "not requires_ollama"
```

**Results**: 
- JUnit reports (in Tests tab)
- Coverage reports (in Code Coverage tab)

---

### Stage 3: EVALUATE

```bash
python evaluate/run_evaluation.py
```

**Metrics calculated**:
- Faithfulness (0-1): Is the answer grounded in sources?
- Answer Relevancy (0-1): Is the answer relevant to the question?
- Execution Time: How long did evaluation take?

**Quality Gate**: Score must be ≥ 0.5 (configurable)

---

### Stage 4: SECURE

Runs three security scanners:

1. **Bandit**: Python code vulnerabilities
2. **Safety**: Dependency CVE scanning
3. **pip-audit**: Package audit

**Results**: SAST report in Security tab

---

### Stage 5: METRICS

Logs everything to MLflow:

```python
mlflow.log_param("torch_version", "2.2.2")
mlflow.log_metric("test_coverage", 85.2)
mlflow.log_metric("faithfulness", 0.82)
```

**Access MLflow**:
```bash
mlflow ui
# Open http://localhost:5000
```

---

### Stage 6: DEPLOY

Two jobs (mutually exclusive):

#### Staging Deploy
- Triggered on `develop` branch
- **Manual** (click play button in UI)
- Lower requirements

#### Production Deploy
- Triggered on git tags (v1.0.0, v1.1.0, etc.)
- **Manual** (requires tag push first)
- Higher requirements

**Deploy manually**:
1. GitLab → Build → Pipelines
2. Find your pipeline
3. Click ▶️ button next to job name

---

## 🐛 Troubleshooting

### Common Issues

#### Pipeline stuck in "pending"
```
→ No runners available
→ Add tags to job or setup personal runner
→ See GUIDE_GITLAB.md section "Troubleshooting"
```

#### "docker: command not found"
```
→ Add services section:
    services:
      - docker:20.10.16-dind
```

#### "torch import failed"
```
→ Install numpy FIRST:
  pip install "numpy<2"
  pip install torch==2.2.2 --index-url ...
```

#### Tests pass locally but fail in CI
```
→ Environment mismatch
→ Use Docker locally to match CI environment:
  docker build -t test-image .
  docker run test-image pytest tests/
```

See `GUIDE_GITLAB.md` for more solutions!

---

## 📈 Monitoring

### View Pipeline History

**Path**: GitLab → Build → Pipelines

Columns:
- Status (✅/❌/⏳)
- Pipeline ID
- Branch
- Commit message
- Duration
- Actions (view, retry, etc.)

### View Specific Job

Click on a job to see:
- Full log output
- Exit code
- Artifacts generated
- Environment variables used

### Export Results

Each job generates artifacts downloadable from:
- `test-results-unit.xml` — Unit test details
- `coverage.xml` — Coverage in Cobertura format
- `bandit-report.json` — Security findings
- `evaluation_results.json` — Ragas scores
- `mlruns/` — Full MLflow history

---

## 🔐 Security Best Practices

### ✅ DO

```yaml
# Use GitLab CI/CD Variables for secrets
environment:
  DOCKER_PASSWORD: $CI_REGISTRY_PASSWORD    # From Variables

# Mark sensitive variables as "Protected"
# GitLab → Settings → CI/CD → Variables → Protected ✓
```

### ❌ DON'T

```yaml
# Never hardcode secrets
environment:
  DOCKER_PASSWORD: "my-secret-password"

# Never commit .env with real credentials
# Use .env.example as template
```

---

## 🎓 Advanced Features

### Scheduled Pipelines

GitLab → Build → Scheduled pipelines

```
Daily security scan at 2:00 AM
Weekly evaluation on Friday
Monthly full audit
```

### Merge Request Pipelines

Pipeline runs on every merge request (before merge)

**Requires**:
- All stages must pass
- Code coverage must improve
- No security issues

### Rules (Conditional Execution)

```yaml
build:docker:
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'      # Only on main branch
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+/'   # Only on version tags
```

### Dependencies Between Jobs

```yaml
deploy:production:
  dependencies:
    - build:docker
    - test:unit
    - security:bandit
    # Only these artifacts available
```

---

## 📞 Getting Help

### Documentation

- [Gitlab CI/CD Docs](https://docs.gitlab.com/ee/ci/)
- [Docker Docs](https://docs.docker.com/)
- [Pytest Docs](https://docs.pytest.org/)
- [Ragas Docs](https://docs.ragas.io/)
- [MLflow Docs](https://mlflow.org/docs/)

### In This Repository

- `GUIDE_GITLAB.md` — Complete setup guide (🌟 Start here!)
- `.gitlab-ci.yml` — Pipeline definition (read comments)
- `Dockerfile` — Container definition (read comments)

### Community

- GitLab Issues: https://gitlab.com/gitlab-org/gitlab/-/issues
- GitLab Forum: https://forum.gitlab.com/
- Stack Overflow: Tag `gitlab-ci`

---

## ✅ Checklist Before Production

- [ ] Pipeline runs successfully locally with `test_pipeline_locally.py`
- [ ] All tests pass (unit & integration)
- [ ] Coverage > 70%
- [ ] No security issues (Bandit clean)
- [ ] Ragas evaluation scores > 0.5
- [ ] Docker image builds without errors
- [ ] Manual deploy test successful
- [ ] MLflow tracking URI configured
- [ ] All secrets are in CI/CD Variables (not in code)
- [ ] Protected branch rules enabled on main

---

## 📝 License & Credits

- **Pipeline**: Built for LLMOps best practices
- **Framework**: GitLab CI/CD native
- **Tools**: pytest, Ragas, MLflow, Bandit, Docker
- **Documentation**: Comprehensive and beginner-friendly

---

**🎉 Welcome to production-grade MLOps! 🚀**

Need help? Start with `GUIDE_GITLAB.md` and come back here for reference!
