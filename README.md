# KODA — AI Companion for First-Generation Academics

> *Japanese: "here, at this point" · Dakota Sioux: "friend, ally"*

[![Amazon Nova](https://img.shields.io/badge/Built%20with-Amazon%20Nova%202%20Lite-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/ai/nova/)
[![Category](https://img.shields.io/badge/Category-Agentic%20AI-7C3AED?style=flat-square)]()
[![Hackathon](https://img.shields.io/badge/Amazon%20Nova-AI%20Hackathon-232F3E?style=flat-square)](https://amazon-nova.devpost.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=flat-square&logo=github-actions&logoColor=white)](.github/workflows/ci.yml)

**Category:** Agentic AI &nbsp;|&nbsp; **Model:** Amazon Nova 2 Lite &nbsp;|&nbsp; **Nova Features:** Extended Thinking · Code Interpreter · Web Grounding · Streaming

---

<details>
<summary><strong>Table of Contents</strong></summary>

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Why Amazon Nova?](#why-amazon-nova)
- [Architecture](#architecture)
- [Agent System](#agent-system)
- [Key Features](#key-features)
- [Community Impact](#community-impact)
- [Demo](#demo)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Security](#security)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)

</details>

---

## The Problem

In Germany, only **25 out of 100** children from non-academic families start university — compared to **78 out of 100** from academic families ([DZHW, 2026](https://www.dzhw.eu/)).

Those who do enroll face an invisible barrier: the **hidden curriculum** — the unwritten rules, institutional jargon, financial systems, and social codes that continuing-generation students absorb naturally from family. Nobody teaches this. It is simply assumed you already know.

First-generation students are **3× more likely to drop out** in their first year and report significantly higher rates of impostor syndrome, financial stress, and isolation. Existing support structures — counseling offices, mentoring programs — are underfunded, appointment-only, and carry a stigma that prevents the students who need them most from seeking help.

**The gap is not ability. It is access to information.**

## The Solution

KODA is a **multi-agent AI system** powered by **Amazon Nova 2 Lite** that decodes the hidden curriculum — 24/7, anonymously, free of charge — in the user's own language.

A user writes a question in German or English. KODA routes it to the right specialist agent, scans every message in parallel for crisis signals, and responds with concrete, shame-free guidance — as if a knowledgeable friend were in the room.

> **Problem → Solution → Why Nova:**
> Traditional support is scarce, appointment-gated, and stigmatized. KODA uses Amazon Nova's Extended Thinking for deep, context-aware reasoning across 13 specialized agents, Code Interpreter for personalized financial calculations, and Web Grounding for real-time scholarship and program searches — all orchestrated through a custom multi-agent framework that runs parallel crisis detection on every single message.

### How It Works

1. **User sends a message** — in German or English, about BAföG, degree programs, impostor feelings, or anything related to university life
2. **Router Agent** classifies the message in <1 second using Extended Thinking (LOW)
3. **Crisis Radar** scans for safety signals **in parallel** on every message
4. **Specialist Agent** responds with deep reasoning (Extended Thinking HIGH), optional Code Interpreter for calculations, or Web Grounding for live data
5. **Anti-Shame Filter** rewrites any condescending language before the response reaches the user
6. **Provenance Tracker** documents where every answer came from (trusted registry, web, document, or model knowledge)

---

## Why Amazon Nova?

Amazon Nova 2 Lite is the core foundation model powering every agent in KODA. Here is exactly how each Nova feature drives the solution:

| Nova Feature | Where Used | Why It Matters |
|:---|:---|:---|
| **Extended Thinking (LOW)** | Router Agent, Crisis Radar | Fast message classification in <1 sec. The router evaluates 5 agent categories with reasoning, not keywords — so ambiguous questions like *"I'm not sure if university is right for me"* route correctly (study choice) rather than incorrectly (crisis). |
| **Extended Thinking (HIGH)** | All 10 domain agents | Deep, multi-step reasoning for complex topics. The Hidden Curriculum agent explains university jargon with 5-point contextual breakdowns. The Anti-Impostor agent applies academic psychology (Jo Phelan's "impostorization" framework, 2024) to structurally reframe self-doubt. |
| **Code Interpreter** | Student Aid Agent, Cost-of-Living Agent | Personalized financial calculations. Students enter their family income, and Code Interpreter computes BAföG eligibility (up to €934/month) with breakdown tables. Cost-of-Living compares monthly expenses across German cities with itemized budgets. |
| **Web Grounding** | Scholarship Agent, Degree Explorer, University Finder, Application Guide | Real-time information retrieval. Scholarship deadlines, Numerus Clausus cut-offs, and application procedures change every semester. Web Grounding ensures answers are current, not stale. |
| **Streaming** | Streamlit frontend (`st.write_stream()`) | Token-by-token display for responsive UX. Students see answers forming in real time rather than waiting for complete responses — critical for trust in a support context. |
| **Cross-Region Inference** | Default model configuration | Automatic capacity failover via the `us.amazon.nova-2-lite-v1:0` cross-region profile. Code Interpreter availability is routed through the global CRIS endpoint. |

**Model ID:** `us.amazon.nova-2-lite-v1:0` (cross-region inference profile)
**Embeddings (configured):** `amazon.nova-2-multimodal-embeddings-v1:0` (reserved for future RAG)

---

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                    User Message                       │
└─────────┬─────────────────────────────┬───────────────┘
          │                             │
          ▼                             ▼
┌───────────────────┐     ┌─────────────────────────┐
│   Router Agent    │     │     Crisis Radar         │
│ (Ext. Thinking    │     │ (parallel on EVERY msg)  │
│      LOW)         │     │ (Ext. Thinking LOW)      │
└────────┬──────────┘     └────────────┬────────────┘
         │                             │
         ▼                             │
┌──────────────────────────────────┐   │
│       Agent Selection            │   │
│                                  │   │
│  ┌────────────┐ ┌─────────────┐  │   │
│  │  COMPASS   │ │  FINANCING  │  │   │
│  │  (LOW)     │ │ (HIGH+Tool) │  │   │
│  └────────────┘ └─────────────┘  │   │
│  ┌─────────────┐ ┌────────────┐  │   │
│  │STUDY_CHOICE │ │  ACADEMIC  │  │   │
│  │ (HIGH+Web)  │ │  BASICS    │  │   │
│  └─────────────┘ │ (HIGH)     │  │   │
│  ┌─────────────┐ └────────────┘  │   │
│  │ ROLE_MODELS │                 │   │
│  │ (HIGH)      │                 │   │
│  └─────────────┘                 │   │
└────────────┬─────────────────────┘   │
             │                         │
             ▼                         │
┌──────────────────────────────────┐   │
│      Cross-Cutting Layers        │◄──┘
│  • Anti-Shame Filter             │
│  • Intersectionality Engine      │
│  • Provenance Tracker            │
│  • Multilingual (auto-detect)    │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│         User Response            │
│   (in user's own language)       │
└──────────────────────────────────┘
```

Full system design, agent inventory, and privacy model: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Agent System

KODA orchestrates **13 specialized agents**, each with a tailored system prompt, reasoning level, and optional tool access:

### Router & Safety

| Agent | Module | Reasoning | Purpose |
|:---|:---|:---:|:---|
| **Router** | `src/agents/router.py` | LOW | Fast message classification into 5 agent categories. Temperature 0.0, max 50 tokens — deterministic and fast. |
| **Crisis Radar** | `src/agents/crisis.py` | LOW | Parallel safety scan on every message. Detects financial emergencies, mental health signals, dropout risk, and acute danger. Provides German crisis hotlines (Telefonseelsorge, 0800 111 0 111). |
| **Compass** | `src/agents/compass.py` | LOW | Emotional grounding and gentle triage to specialist agents. First point of contact. |

### Domain Specialists

| Agent | Module | Reasoning | Tools | Purpose |
|:---|:---|:---:|:---:|:---|
| **Student Aid (BAföG)** | `src/agents/financing/student_aid.py` | HIGH | Code Interpreter | BAföG eligibility and amount calculations. Embedded knowledge: max €934/month, 50% grant + 50% interest-free loan, income allowances. |
| **Scholarships** | `src/agents/financing/scholarships.py` | HIGH | Web Grounding | Scholarship discovery. Curated database of Deutschlandstipendium, Hans-Böckler-Stiftung, Rosa-Luxemburg-Stiftung, and more. Live deadline searches. |
| **Cost of Living** | `src/agents/financing/cost_of_living.py` | HIGH | Code Interpreter | City-by-city cost comparison with itemized budgets. 2026 benchmarks for Munich (€650–900), Berlin (€500–700), Leipzig (€300–450). |
| **Degree Explorer** | `src/agents/study_choice/degree_explorer.py` | HIGH | Web Grounding | Interest-to-program matching. Explains university vs. Fachhochschule vs. dual study. Shows entry requirements. |
| **University Finder** | `src/agents/study_choice/university_finder.py` | HIGH | Web Grounding | Institution comparison with first-gen-friendly criteria: mentoring programs, class sizes, cost of living, support services. |
| **Application Guide** | `src/agents/study_choice/application_guide.py` | HIGH | Web Grounding | Step-by-step walkthrough of Hochschulstart.de, deadlines (July 15 / January 15), required documents, and enrollment. |
| **Hidden Curriculum** | `src/agents/academic_basics/hidden_curriculum.py` | HIGH | — | **Signature feature.** Decodes 30+ university terms (ECTS, Immatrikulation, Freiversuch, Fachschaft, etc.) with a 5-point method: simple explanation → context → concrete example → what to do → why first-gen students don't know. |
| **Study vs. Apprenticeship** | `src/agents/academic_basics/study_vs_apprenticeship.py` | HIGH | — | Honest, bias-free comparison. Validates family pressure ("your father's advice makes sense from his experience") while showing all options. |
| **Role Model Matching** | `src/agents/role_models/matching.py` | HIGH | — | Matches users with relevant first-gen role models from a curated database of 20 (Cem Özdemir, Ursula Burns, Malala Yousafzai, and more). Tells stories in an empowering frame — WITH their perspective, not DESPITE their background. |
| **Anti-Impostor** | `src/agents/role_models/anti_impostor.py` | HIGH | — | Structural reframing based on Jo Phelan's (2024) "impostorization" concept. Does NOT say "just believe in yourself." Instead: validates the feeling → explains the structural cause → offers concrete coping strategies. |

### Onboarding

| Agent | Module | Reasoning | Purpose |
|:---|:---|:---:|:---|
| **Onboarding** | `src/agents/onboarding.py` | LOW | 3–5 turn guided intake conversation. Builds a user profile (situation, main concern, interests) and generates personalized quick-action prompts for the sidebar. |

---

## Key Features

### Anti-Shame Filter

Every response passes through a filter that detects and rewrites condescending language patterns — 20+ rules in both German and English:

| Detected Pattern | Replacement |
|:---|:---|
| "you should know" | "I'll explain it clearly" |
| "this is basic" | "I'll keep this simple" |
| "everyone knows" | "many people are never told this" |
| "das solltest du wissen" | "Ich erkläre es gerne" |

**Core principle embedded in every agent's system prompt:**
> "When a user does not know something, ALWAYS say: 'Nobody explains this automatically. You are not supposed to already know.' NEVER say: 'This is basic' or 'You should know this.'"

### Parallel Crisis Detection

The Crisis Radar runs **on every single message**, in parallel with the router — not as an afterthought, but as a first-class safety system:

- **Financial emergency:** Cannot pay rent/food, dropout risk due to finances
- **Mental health:** Hopelessness, self-harm signals, extreme isolation
- **Dropout risk:** Wants to quit, sees no purpose in continuing
- **Acute danger:** Homelessness, violence, immediate physical danger

Detection uses Nova's reasoning (not just keyword matching), with smart benign-pattern filtering to avoid false positives on study-choice questions like *"I'm wondering whether I even want to study."*

When crisis signals are detected, KODA displays a crisis resource banner with German emergency numbers:
- **112** (Emergency) / **110** (Police)
- **Telefonseelsorge:** 0800 111 0 111 (free, 24/7, Germany)
- **University counseling:** free psychological services at local Studierendenwerk
- **ArbeiterKind.de:** peer mentoring network for first-gen students

### Multilingual Support

- Automatic language detection from user messages (German/English)
- All agents respond in the user's language — no configuration needed
- UI fully translated (160+ strings) with one-click language toggle
- Agent prompts written in English for maintainability; language instruction inherited by all agents

### Session Memory & Portability

- In-memory sessions with automatic topic extraction (BAföG, scholarships, ECTS, Ausbildung, etc.)
- Identity context captured conversationally (first-gen status, working student, financial stress, caregiver)
- LLM-generated sidebar summaries (profile facts + conversation overview)
- **Session export/import:** download your session as JSON, resume later on any device
- Sessions auto-expire after 30 minutes — privacy by design, no persistent user data

### Document Support

Upload documents for context-aware conversations:
- **Supported formats:** PDF, DOCX, TXT, MD, CSV, XLSX
- **Limits:** 5 documents per request, 4.5 MB per text document, 25 MB combined
- **Privacy:** Documents are processed ephemerally — metadata stored, content discarded after response

### Provenance Tracking

Every answer includes attribution metadata documenting its source:
- **Source registry:** Curated German government and educational sources
- **Web grounding:** Real-time web results with URLs
- **Document upload:** Information from user-uploaded files
- **Model knowledge:** Nova's training data (clearly labeled)

---

## Community Impact

### Who This Serves

**2.9 million students** are currently enrolled in German universities. An estimated **790,000** are first-generation academics — students whose parents did not attend university. They navigate a system designed for people whose families already know the rules.

### What Changes

| Current State | With KODA |
|:---|:---|
| Support available Mon–Fri 9–16, by appointment | Available 24/7, instantly, from any device |
| Students must self-identify as "needing help" | Anonymous — no login, no stigma, no judgment |
| Counselors handle 500+ students each | Unlimited capacity via Amazon Nova |
| Information scattered across 50+ websites | One conversation, one trusted companion |
| German-only bureaucratic language | Plain language in the user's own language |
| Impostor syndrome treated as individual problem | Structural reframing based on academic research |

### Potential Scale

- **Germany:** 423 universities, each with first-gen students who lack guidance
- **Global applicability:** The hidden curriculum problem exists in every country with university systems
- **Partner path:** ArbeiterKind.de (Germany's largest first-gen mentoring network, 6,000+ mentors) could integrate KODA as a digital first-contact companion

---

## Demo

<!-- 🎥 Demo Video: Replace with your YouTube/Vimeo link -->
**▶ [Watch the Demo Video (≈3 min)](https://youtu.be/REPLACE_WITH_VIDEO_ID)** — #AmazonNova

The demo showcases:
1. Onboarding conversation that builds a personalized profile
2. BAföG calculation via Code Interpreter with itemized breakdown
3. Real-time scholarship search via Web Grounding
4. Hidden Curriculum decoder explaining "ECTS" with anti-shame framing
5. Crisis detection triggering resource banner
6. Language switching between German and English
7. Session export and reimport

---

## Quick Start

### Prerequisites

| Requirement | Notes |
|:---|:---|
| Python 3.11+ | Earlier versions are not supported |
| AWS account | With Amazon Bedrock enabled in `us-east-1` |
| Bedrock model access | Enable **Amazon Nova 2 Lite** in the [Bedrock console](https://console.aws.amazon.com/bedrock/home#/modelaccess) |
| AWS credentials | IAM user keys **or** a named profile (see [.env.example](.env.example)) |

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

Every variable is documented in [.env.example](.env.example) with type, default, and security rationale.

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

The Streamlit frontend calls agents directly. The FastAPI backend is available for programmatic access or future integrations.

```bash
uvicorn src.api.app:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

### Docker

```bash
docker compose up --build
# Opens at http://localhost:8501
```

The container runs as a non-root user with a read-only filesystem, all capabilities dropped, and no privilege escalation — [OWASP Container Security Verification Standard](https://owasp.org/www-project-web-security-testing-guide/) compliant.

---

## Project Structure

```
amazon-nova-ai-hackathon/
├── frontend/
│   ├── app.py                    # Streamlit chat interface (deployed UI)
│   └── static/                   # Logo, background images
├── src/
│   ├── agents/                   # 13 specialized agents
│   │   ├── base.py               # Base class (anti-shame filter, language detection, streaming)
│   │   ├── router.py             # Fast message triage (Extended Thinking LOW)
│   │   ├── crisis.py             # Parallel safety scan (Extended Thinking LOW)
│   │   ├── compass.py            # First contact, emotional grounding
│   │   ├── onboarding.py         # Guided intake conversation
│   │   ├── financing/            # Student Aid · Scholarships · Cost of Living
│   │   ├── study_choice/         # Degree Explorer · University Finder · Application Guide
│   │   ├── academic_basics/      # Hidden Curriculum · Study vs. Apprenticeship
│   │   └── role_models/          # Role Model Matching · Anti-Impostor
│   ├── orchestration/
│   │   └── chat_service.py       # Central orchestrator (routing, crisis, response shaping)
│   ├── core/
│   │   ├── client.py             # Amazon Bedrock Converse API wrapper (retry, streaming, tools)
│   │   ├── conversation.py       # In-memory session state (24-message history, topic extraction)
│   │   ├── safety.py             # Anti-shame filter + intersectionality engine
│   │   ├── provenance.py         # Source attribution and citation tracking
│   │   ├── documents.py          # Ephemeral document handling (PDF, DOCX, CSV, XLSX)
│   │   ├── session_bundle.py     # Portable session export/import (JSON, SHA-256 checksum)
│   │   └── session_summary.py    # LLM-generated sidebar summaries
│   ├── api/
│   │   └── app.py                # FastAPI REST API (8 endpoints, Pydantic-validated)
│   ├── i18n/
│   │   └── strings.py            # 160+ bilingual UI strings (German + English)
│   ├── knowledge/
│   │   ├── role_models.json      # 20 curated first-gen role models
│   │   ├── scholarships.json     # Scholarship database
│   │   ├── terminology.json      # University system terminology
│   │   ├── source_registry.py    # Trusted German source curation
│   │   └── trusted_sources/      # Country-specific source lists
│   └── tools/
│       ├── bafoeg_calculator.py   # BAföG computation (via Code Interpreter)
│       ├── cost_calculator.py     # Cost-of-living comparison
│       └── degree_database.py     # Degree program lookup
├── config/
│   └── settings.py               # Single source of truth (model IDs, timeouts, CORS)
├── tests/
│   ├── unit/                     # 16 test modules (no AWS required)
│   ├── integration/              # API endpoint tests (mocked Bedrock)
│   └── scenarios/                # 6 JSON scenario files + parametrized runner
├── terraform/                    # Full AWS infrastructure as code
│   ├── ecs.tf                    # ECS Fargate (512 CPU, 1 GB RAM, circuit breaker)
│   ├── alb.tf                    # Application Load Balancer (sticky sessions for WebSocket)
│   ├── cloudfront.tf             # CDN distribution
│   ├── waf.tf                    # AWS WAF (rate limit, bot control, SQLi/XSS)
│   ├── iam_ecs.tf                # Scoped IAM roles (Bedrock limited to Nova 2 Lite only)
│   └── ...                       # VPC, security groups, ECR, DynamoDB, secrets, monitoring
├── .github/workflows/
│   ├── ci.yml                    # Lint, security scan, Docker build + Trivy, unit tests
│   ├── deploy.yml                # OIDC-based deploy to ECS (no static credentials)
│   ├── test.yml                  # Full test suite with coverage
│   └── dependency-audit.yml      # Automated vulnerability scanning
├── .env.example                  # Documented environment template
├── Dockerfile                    # Multi-stage, non-root, OCI-labeled
├── docker-compose.yml            # Local dev (read-only FS, no capabilities)
├── pyproject.toml                # Package metadata, Ruff, mypy, pytest config
├── requirements.txt              # Pinned production dependencies
├── SECURITY.md                   # Vulnerability reporting policy
└── docs/
    └── ARCHITECTURE.md           # Full system design document
```

---

## Running Tests

Three test tiers — all runnable without AWS credentials:

| Tier | Location | What It Covers |
|:---|:---|:---|
| **Unit** (16 modules) | `tests/unit/` | Router classification, crisis detection, anti-shame filter, session memory, provenance, CORS validation, i18n, documents, onboarding |
| **Integration** | `tests/integration/` | FastAPI endpoints with mocked Bedrock (health, chat, documents, onboarding, sessions) |
| **Scenario** | `tests/scenarios/` | End-to-end routing against 6 JSON test cases (German + English inputs → correct agent) |

```bash
# Unit tests only (fast, no credentials needed)
pytest tests/unit/ -v -m unit

# Integration tests
pytest tests/integration/ -v -m integration

# Scenario tests
pytest tests/scenarios/ -v

# Full suite
pytest -v

# With coverage report
pytest --cov=src --cov-report=term-missing
```

---

## Deployment

KODA deploys to **AWS ECS Fargate** behind **CloudFront** with **WAF** protection. All infrastructure is managed via Terraform.

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Deployment Architecture

| Component | Service | Configuration |
|:---|:---|:---|
| Compute | ECS Fargate | 512 CPU, 1 GB RAM, deployment circuit breaker with auto-rollback |
| Load Balancer | ALB | Sticky sessions (LB cookie, 86400s) for Streamlit WebSocket |
| CDN | CloudFront | Edge caching, TLS termination |
| Security | AWS WAF | Rate limiting, bot control, IP reputation, SQLi/XSS rules |
| Container Registry | Amazon ECR | Images tagged by commit SHA for reproducibility |
| Secrets | AWS Secrets Manager | Bedrock credentials injected at runtime (never in image) |
| Monitoring | CloudWatch | Container Insights, structured logging via `structlog` |
| CI/CD | GitHub Actions | OIDC authentication (no long-lived keys), auto-deploy on push to `main` |

See [terraform/README.md](terraform/README.md) for IAM requirements, Secrets Manager setup, and the OIDC deploy pipeline.

---

## Security

KODA is designed with security and privacy as first-class requirements, not afterthoughts.

| Concern | Control | Standard |
|:---|:---|:---|
| **Data privacy** | Sessions in-memory only, auto-expire after 30 min, never persisted to disk or database | GDPR Art. 25 (Privacy by Design) |
| **Authentication** | None by design — no login, no accounts, no tracking | Minimizes attack surface |
| **Transport** | HTTPS enforced via CloudFront TLS termination | OWASP A02:2021 |
| **API access** | CORS restricted to explicit origin allowlist; wildcard `*` rejected at startup | OWASP A05:2021 |
| **Infrastructure** | AWS WAF with rate limiting, bot control, IP reputation, SQLi/XSS protection | OWASP A03:2021 |
| **Secrets** | No credentials in code or images; IAM roles in production, Secrets Manager for ECS | OWASP A07:2021 |
| **Container** | Non-root user, read-only filesystem, all capabilities dropped, no privilege escalation | OWASP Container Security (CSVS) |
| **Dependencies** | Ruff (Bandit rules), Trivy container scan, Dependabot, `pip-audit` in CI | OWASP A06:2021 |
| **Code quality** | CodeQL on PRs, secret scanning on all pushes, pre-commit hooks | NIST SP 800-218 (SSDF) |

To report a vulnerability, see [SECURITY.md](SECURITY.md).

---

## Tech Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| **AI Model** | Amazon Nova 2 Lite (`us.amazon.nova-2-lite-v1:0`) | Foundation model with Extended Thinking, Code Interpreter, Web Grounding |
| **Agent Framework** | Custom multi-agent orchestration (Python) | 13-agent routing, parallel crisis detection, anti-shame filtering |
| **Frontend** | Streamlit | Chat interface with streaming, document upload, session management |
| **Backend API** | FastAPI + Uvicorn | 8 REST endpoints with Pydantic validation for programmatic access |
| **Infrastructure** | AWS ECS Fargate · CloudFront · WAF · ALB | Serverless containers, CDN, DDoS protection |
| **IaC** | Terraform | Full infrastructure as code (20+ resource definitions) |
| **CI/CD** | GitHub Actions (4 workflows) | Lint, security scan, Docker build + Trivy, OIDC deploy |
| **Language** | Python 3.11+ | Type-annotated, Ruff-checked, mypy-verified |

---

## Contributing

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Write code following the existing style (PEP 8, type annotations).
3. Add or update tests for any changed behaviour.
4. Run the quality gates locally:
   ```bash
   ruff check .                       # lint (includes Bandit security rules)
   ruff format .                      # format
   mypy src/                          # type checking
   pytest -m "unit or integration" -v  # tests
   ```
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(agents): add scholarship matcher for DAAD programs
   fix(frontend): correct language toggle initial state
   ```
6. Open a Pull Request against `main`.

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**73% of German students from non-academic families either never start, or navigate university alone — figuring out by trial and error what others learned at the dinner table.**

**KODA exists to close that gap.**

*Built for the [Amazon Nova AI Hackathon](https://amazon-nova.devpost.com/)* · **#AmazonNova**

</div>
