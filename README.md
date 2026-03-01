# KODA — AI Companion for First-Generation Academics

> *Japanese: "here, at this point" · Dakota Sioux: "friend, ally"*

[![Amazon Nova](https://img.shields.io/badge/Built%20with-Amazon%20Nova%202-FF9900?style=flat-square)](https://aws.amazon.com/nova/)
[![Hackathon](https://img.shields.io/badge/Amazon%20Nova-AI%20Hackathon-blue?style=flat-square)](https://amazon-nova.devpost.com/)
[![Category](https://img.shields.io/badge/Category-Agentic%20AI-7C3AED?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square)](https://www.python.org/)

---

## The Problem

In Germany, only **27 out of 100** children from non-academic families start university —
compared to **79 out of 100** from academic families
([DZHW, 2021](https://www.dzhw.eu/)).

Those who do enroll face an invisible barrier: the **hidden curriculum** — the unwritten
rules, institutional jargon, financial systems, and social codes that
continuing-generation students absorb naturally from family. Nobody teaches this.
It is simply assumed you already know.

## The Solution

KODA is a **multi-agent AI system** built on Amazon Nova 2 that decodes the hidden
curriculum — 24/7, anonymously, free of charge — in the user's own language.

A user writes a question in German or English. KODA routes it to the right specialist
agent, scans every message in parallel for crisis signals, and responds with
concrete, shame-free guidance — as if a knowledgeable friend were in the room.

| Agent | Domain | Amazon Nova 2 Features |
|-------|--------|------------------------|
| **Financing** | Student aid (BAföG), scholarships, cost-of-living | Code Interpreter · Web Grounding |
| **Study Choice** | Degree programs, universities, applications | Web Grounding · Extended Thinking |
| **Academic Basics** | Hidden curriculum decoder, terminology | Extended Thinking (HIGH) |
| **Role Models** | First-gen role models, anti-impostor support | Extended Thinking (HIGH) |

Cross-cutting capabilities active on every request:
- **Router Agent** — fast triage via Extended Thinking LOW
- **Crisis Radar** — parallel safety scan on every message
- **Anti-Shame Filter** — blocks condescending language patterns in responses
- **Multilingual** — auto-detects German/English and responds in kind

---

## Architecture

```
User Message ──┬──► Router Agent          (Extended Thinking LOW — fast triage)
               │         ├──► Financing Agent    (Code Interpreter + Web Grounding)
               │         ├──► Study Choice Agent  (Web Grounding + Extended Thinking HIGH)
               │         ├──► Academic Basics     (Extended Thinking HIGH)
               │         └──► Role Models Agent   (Extended Thinking HIGH)
               │
               └──► Crisis Radar          (parallel on EVERY message)

All agents inherit: Anti-Shame Filter · Language Auto-Detection · Graceful Fallbacks
```

Full system design, agent inventory, and privacy model: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Tech Stack

| Layer | Technology |
|-------|------------|
| AI model | Amazon Nova 2 Lite (cross-region inference) |
| Agent framework | Custom multi-agent orchestration (Python) |
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| Infrastructure | AWS ECS Fargate · CloudFront · WAF · Terraform |
| CI/CD | GitHub Actions · OIDC (no long-lived secrets) |
| Language | Python 3.11+ |

---

## Quick Start

### Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.11+ | Earlier versions are not supported |
| AWS account | With Amazon Bedrock enabled in `us-east-1` |
| Bedrock model access | Enable **Nova 2 Lite** in the [Bedrock console](https://console.aws.amazon.com/bedrock/home#/modelaccess) |
| AWS credentials | IAM user keys **or** a named profile (see `.env.example`) |

### 1. Clone and install

```bash
git clone https://github.com/florianpreiss/amazon-nova-ai-hackathon.git
cd amazon-nova-ai-hackathon
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and fill in your AWS credentials / region
```

Every variable is documented in [`.env.example`](.env.example) with type, default,
and security rationale.

### 3. Verify Bedrock access

```bash
python scripts/verify_setup.py
```

### 4. Run the Streamlit frontend

```bash
./run_frontend.sh
# Opens at http://localhost:8501
```

### 5. (Optional) Run the FastAPI backend

The Streamlit frontend calls agents directly. The FastAPI backend is available
for programmatic access or future mobile/web clients.

```bash
uvicorn src.api.app:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

---

## Project Structure

```
amazon-nova-ai-hackathon/
├── frontend/
│   ├── app.py              # Streamlit chat interface (the deployed UI)
│   └── static/             # Background images
├── src/
│   ├── agents/             # 13 domain agents + router + crisis radar
│   ├── api/                # FastAPI app (REST API)
│   ├── core/               # Bedrock client, conversation state, safety
│   ├── i18n/               # UI translations (German + English)
│   ├── knowledge/          # Static JSON knowledge bases
│   └── tools/              # BAföG calculator, degree DB, cost calculator
├── config/
│   └── settings.py         # Single source of truth for all settings
├── tests/
│   ├── unit/               # Unit tests (no AWS required)
│   ├── integration/        # Integration tests (mocked Bedrock)
│   └── scenarios/          # Scenario JSON files + parametrized runner
├── terraform/              # Full AWS infrastructure (ECS, CloudFront, WAF)
├── docs/
│   └── ARCHITECTURE.md     # Detailed system design
├── .env.example            # Environment variable template
└── requirements.txt
```

---

## Running Tests

The test suite has three tiers:

| Tier | Location | AWS required | What it covers |
|------|----------|:------------:|----------------|
| **Unit** | `tests/unit/` | No | Router classification, i18n, safety filter |
| **Integration** | `tests/integration/` | No | API endpoints with mocked Bedrock |
| **Scenario** | `tests/scenarios/` | No | End-to-end routing against JSON test cases |

```bash
# Unit tests only (fast, no credentials needed)
pytest -m unit -v

# Integration tests (Bedrock is mocked)
pytest -m integration -v

# Scenario tests (routing + response shape validation)
pytest tests/scenarios/ -v

# Full suite
pytest -v

# With coverage report
pytest --cov=src --cov-report=term-missing
```

---

## Deployment

KODA deploys to AWS ECS Fargate behind CloudFront. Infrastructure is managed via Terraform.

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

See [terraform/README.md](terraform/README.md) for details including IAM requirements,
Secrets Manager setup, and the GitHub Actions OIDC deploy pipeline.

---

## Security

| Concern | Control |
|---------|----------|
| Data privacy | Sessions are in-memory only, auto-expire after 30 min, never persisted |
| Authentication | No login, no accounts, no user tracking |
| Transport | HTTPS enforced via CloudFront |
| API access | CORS restricted to explicit origin allowlist (OWASP A05:2021) |
| Infrastructure | AWS WAF with rate limiting, bot control, and IP reputation lists |
| Secrets | No secrets in code; AWS credentials via IAM roles / Secrets Manager in production |
| Dependencies | `ruff` (Bandit rules) and `pip-audit` in CI pipeline |

To report a vulnerability, see [SECURITY.md](SECURITY.md).

---

## Contributing

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Write code following the existing style (PEP 8, type annotations, docstrings).
3. Add or update tests for any changed behaviour.
4. Run the pre-commit quality gates locally:
   ```bash
   ruff check .          # lint (includes Bandit security rules)
   ruff format .         # format
   mypy src/             # type checking
   pytest -m "unit or integration" -v
   ```
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(agents): add scholarship matcher for DAAD programs
   fix(frontend): correct language toggle initial state
   docs(readme): update deployment prerequisites
   ```
6. Open a Pull Request against `main` with a clear description of the change and its motivation.

---

## License

MIT — see [LICENSE](LICENSE)

---

**73% of German students from non-academic families either never start, or navigate
university alone — figuring out by trial and error what others learned at the dinner table.**

KODA exists to close that gap.

---

*Built for the [Amazon Nova AI Hackathon](https://amazon-nova.devpost.com/) · #AmazonNova*
