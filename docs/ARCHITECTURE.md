# KODA — System Architecture

> Multi-agent AI system for first-generation academic guidance, built on Amazon Nova 2 Lite.

---

## Table of Contents

- [Overview](#overview)
- [Request Lifecycle](#request-lifecycle)
- [Agent System](#agent-system)
- [Amazon Nova Integration](#amazon-nova-integration)
- [Cross-Cutting Layers](#cross-cutting-layers)
- [Session Management](#session-management)
- [Provenance Tracking](#provenance-tracking)
- [Infrastructure](#infrastructure)
- [Network Architecture](#network-architecture)
- [CI/CD Pipeline](#cicd-pipeline)
- [Privacy Model](#privacy-model)

---

## Overview

KODA decomposes the problem of university guidance into specialized agents, each configured with the appropriate reasoning depth and tools for its domain. The system is not a single LLM wrapped in a chat UI — it is an orchestration layer that routes, reasons, monitors safety, filters tone, and tracks provenance across every interaction.

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
│       Specialist Selection       │   │
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

---

## Request Lifecycle

Every user message follows the same orchestrated pipeline, implemented in `ChatService.respond()`:

### Step 1 — Prepare Turn

`_prepare_turn()` retrieves or creates an ephemeral session, syncs any incoming history, and merges conversation metadata (topics, identity signals, goals).

### Step 2 — Parallel Dispatch

Two operations run simultaneously:

| Operation | Agent | Reasoning | Purpose |
|:---|:---|:---:|:---|
| **Route** | Router Agent | LOW | Classify the message into one of 5 agent categories (COMPASS, FINANCING, STUDY_CHOICE, ACADEMIC_BASICS, ROLE_MODELS). Temperature 0.0, max 50 tokens — deterministic. |
| **Safety Scan** | Crisis Radar | LOW | Detect financial emergencies, mental health signals, dropout risk, or acute danger. Runs on every message, not just flagged ones. |

### Step 3 — Select Specialist

The router returns an agent key. `ChatService` looks up the matching specialist from the registered agent map. If routing fails, the system falls back to the COMPASS agent (general orientation).

### Step 4 — Build Enriched System Prompt

`BaseAgent._build_prompt()` assembles the final system prompt from six layers:

1. **Domain prompt** — agent-specific instructions and embedded knowledge
2. **Language instruction** — auto-detect and respond in user's language
3. **UI language addendum** — strong signal for ambiguous messages
4. **Identity addendum** — intersectionality context from captured identity signals
5. **Session memory addendum** — previous topics, goals, and conversation context
6. **Sourcing addendum** — trusted source prioritization rules (if Web Grounding enabled)

### Step 5 — Generate Response

The agent calls Amazon Bedrock via `NovaClient`:

| Agent Tool Mode | Bedrock API Call | Temperature |
|:---|:---|:---:|
| `None` (standard) | `converse()` with Extended Thinking HIGH | 0.7 |
| `code_interpreter` | `converse()` with `nova_code_interpreter` system tool | 0.0 |
| `web_grounding` | `converse()` with `nova_grounding` system tool | 0.3 |

### Step 6 — Apply Anti-Shame Filter

`apply_anti_shame_filter()` scans the response for 20+ condescending language patterns in German and English and replaces them with neutral, supportive alternatives.

### Step 7 — Resolve Provenance

`merge_provenance()` combines request-level source context (trusted registry) with response-extracted citations (Web Grounding URLs) into a single `ResponseProvenance` object documenting where the answer came from.

### Step 8 — Inject Crisis Resources

If the Crisis Radar detected a signal, a resource banner (emergency numbers, crisis hotlines, counseling services) is prepended to the response.

### Step 9 — Store Turn & Return

The user and assistant messages are stored in the session. If a summarizer is configured, it generates updated sidebar facts. The final `ChatTurnResult` is returned with: session_id, response text, agent used, crisis status, crisis resources, and provenance metadata.

### Streaming Variant

`respond_stream()` follows the same pipeline but yields tokens incrementally via `converse_stream()`. Tool-mode agents (Code Interpreter, Web Grounding) do not support streaming and fall back to full-response delivery. The anti-shame filter runs on the fully collected text; if it modifies the response, a `\x00REPLACE\x00` marker signals the UI to swap the displayed text.

---

## Agent System

### Inventory

| # | Agent | Module | Reasoning | Tools | Purpose |
|:-:|:---|:---|:---:|:---:|:---|
| 1 | **Router** | `agents/router.py` | LOW | — | Fast message classification into 5 categories |
| 2 | **Crisis Radar** | `agents/crisis.py` | LOW | — | Parallel safety scan on every message |
| 3 | **Compass** | `agents/compass.py` | LOW | — | First contact, emotional grounding, triage |
| 4 | **Student Aid** | `agents/financing/student_aid.py` | HIGH | Code Interpreter | BAföG eligibility and amount calculations |
| 5 | **Scholarships** | `agents/financing/scholarships.py` | HIGH | Web Grounding | Scholarship discovery with live deadline searches |
| 6 | **Cost of Living** | `agents/financing/cost_of_living.py` | HIGH | Code Interpreter | City-by-city cost comparison with itemized budgets |
| 7 | **Degree Explorer** | `agents/study_choice/degree_explorer.py` | HIGH | Web Grounding | Interest-to-program matching |
| 8 | **University Finder** | `agents/study_choice/university_finder.py` | HIGH | Web Grounding | Institution comparison with first-gen criteria |
| 9 | **Application Guide** | `agents/study_choice/application_guide.py` | HIGH | Web Grounding | Step-by-step application walkthrough |
| 10 | **Hidden Curriculum** | `agents/academic_basics/hidden_curriculum.py` | HIGH | — | University jargon decoder (30+ terms) |
| 11 | **Study vs. Apprenticeship** | `agents/academic_basics/study_vs_apprenticeship.py` | HIGH | — | Honest, bias-free path comparison |
| 12 | **Role Model Matching** | `agents/role_models/matching.py` | HIGH | — | First-gen role model stories (20 profiles) |
| 13 | **Anti-Impostor** | `agents/role_models/anti_impostor.py` | HIGH | — | Structural reframing (Phelan 2024) |

**+ Onboarding Agent** (`agents/onboarding.py`, LOW) — 3–5 turn guided intake that builds a user profile and generates personalized quick-action prompts.

### Agent Base Class

All agents inherit from `BaseAgent` which provides:

- **Unified Bedrock interface** — `respond()`, `respond_with_details()`, `respond_stream()`
- **System prompt enrichment** — 6-layer addendum assembly via `_build_prompt()`
- **Anti-shame filter** — applied on every response before returning
- **Error handling** — catches `NovaClientError`, returns bilingual fallback, never exposes traces
- **Language instruction** — inherited constant that tells Nova to auto-detect and match user language

```
Constructor: BaseAgent(name, system_prompt, reasoning_effort, tool_mode)
                                                    ↓
_build_prompt()  →  domain_prompt + language + ui_lang + identity + memory + sources
                                                    ↓
NovaClient.converse() / .converse_stream() / .with_code_interpreter() / .with_web_grounding()
                                                    ↓
apply_anti_shame_filter(response_text)  →  AgentReply(text, provenance)
```

### Crisis Detection

The Crisis Radar uses Nova's reasoning (not keyword matching) to classify messages into four severity categories:

| Category | Examples |
|:---|:---|
| **FINANCIAL** | Cannot pay rent/food, dropout risk due to finances |
| **MENTAL** | Hopelessness, self-harm signals, extreme isolation |
| **DROPOUT** | Wants to quit, sees no purpose in continuing |
| **ACUTE** | Homelessness, violence, immediate physical danger |

Smart benign-pattern filtering prevents false positives on study-choice questions like *"I'm wondering whether I even want to study."*

Resources provided when crisis is detected:
- **112** (Emergency) / **110** (Police)
- **Telefonseelsorge:** 0800 111 0 111 (free, 24/7)
- **University counseling:** Studierendenwerk
- **ArbeiterKind.de:** peer mentoring network

---

## Amazon Nova Integration

### Model Configuration

| Parameter | Value | Source |
|:---|:---|:---|
| Model ID | `us.amazon.nova-2-lite-v1:0` | Cross-region inference profile |
| Region | `us-east-1` | Default |
| Read Timeout | 3600s (60 min) | Extended Thinking can be slow |
| Max Tokens | 4096 | Default for all agents |
| Temperature | 0.7 (standard), 0.3 (Web Grounding), 0.0 (Code Interpreter, Router) | Per-agent |
| Top-P | 0.9 | Default |

### Bedrock Client (`NovaClient`)

The client wraps the Amazon Bedrock Converse API with:

- **Retry logic** — 3 retries with exponential backoff (1s → 2s → 4s)
- **Extended Thinking** — configured via `additionalModelRequestFields.reasoningConfig` (Bedrock rejects temperature/topP/maxTokens when reasoning is enabled)
- **Tool attachment** — `nova_code_interpreter` and `nova_grounding` system tools
- **Stream handling** — `iter_stream_text()` generator that strips `[HIDDEN]` reasoning markers
- **Citation extraction** — `extract_web_citations()` recursively searches responses for URLs

### Error Hierarchy

```
NovaClientError
├── NovaThrottlingError     — Rate limit exceeded (retried 3×)
├── NovaAccessDeniedError   — IAM permission issue
└── NovaTimeoutError        — 60-min timeout exceeded
```

All errors are caught at the agent level and result in a user-friendly fallback message — never a stack trace.

---

## Cross-Cutting Layers

### Anti-Shame Filter

Every response passes through `apply_anti_shame_filter()` which detects 20+ condescending patterns and replaces them:

| Detected (EN) | Replacement | Detected (DE) | Replacement |
|:---|:---|:---|:---|
| "you should know" | "I'll explain it clearly" | "das solltest du wissen" | "ich erkläre es dir kurz" |
| "this is basic" | "I'll keep this simple" | "das ist grundwissen" | "ich halte es bewusst einfach" |
| "everyone knows" | "many people are never told this" | "jeder weiss" | "viele Menschen bekommen das nie erklärt" |
| "obviously" | "to make it clear" | "selbstverständlich" | "zur Einordnung" |
| "common knowledge" | "often left unexplained" | | |
| "should have learned" | "may not have been explained yet" | | |

### Intersectionality Engine

`build_identity_addendum()` enriches every system prompt with captured identity context:

```
--- Adapt guidance to this user context ---
- Use inclusive, gender-sensitive, anti-racist language.
- Do not stereotype or make assumptions based on gender, race, class,
  migration history, disability, religion, or sexuality.
- Treat identity markers as context, not as limitations.
- first_generation_student: True
- working_student: True
- financial_stress: "tight budget"
---
```

Identity signals are detected automatically from conversation content — never from forms or self-disclosure prompts.

### Multilingual Design

All agent prompts are written in English for maintainability. Every agent inherits a `LANGUAGE_INSTRUCTION` that tells Nova to:

1. Auto-detect the user's language from the latest message
2. Respond in the same language
3. Use plain language (150–250 words unless asked otherwise)
4. Avoid jargon
5. Use gender-sensitive, inclusive wording

The UI layer provides 160+ translated strings (German + English) with a one-click language toggle.

---

## Session Management

### Lifecycle

Sessions are ephemeral, in-memory objects that auto-expire after 30 minutes of inactivity. Thread-safe via `RLock`.

### Limits

| Parameter | Value |
|:---|:---|
| Message history | 24 messages (trimmed to last 24) |
| Active goals | 4 |
| Topics tracked | 6 |
| Active documents | 5 |
| Goal length | 140 characters |
| Personalized prompts | 5 |
| Onboarding messages | 12 |
| Profile summary | 1200 characters |

### Automatic Extraction

**Topics** (9 categories detected from keywords):
BAföG · Scholarships · ECTS · Applications · Deadlines · Semester fees · Ausbildung · Dual study · Module handbook · Self-doubt

**Identity signals** (5 markers detected from conversational context):
first_generation_student · international_student · working_student · caregiver · financial_stress

### Session Export/Import

Users can download their session as a JSON bundle (max 256 KB) with SHA-256 checksum validation and reimport it to continue on any device.

---

## Provenance Tracking

Every answer carries a `ResponseProvenance` object documenting its source:

| Mode | When Selected |
|:---|:---|
| `source_registry` | Trusted curated sources matched (German government, educational sites) |
| `web_grounding` | Web Grounding tool returned citations |
| `source_registry_and_web` | Both curated sources and web results contributed |
| `document` | User-uploaded documents were used |
| `model` | Pure Nova knowledge (no external sources) |

Source deduplication prefers `source_registry` over `web_grounding` when the same URL appears from both origins.

---

## Infrastructure

### Deployment Architecture

```
Internet
  │
  ▼
CloudFront (TLS termination, caching)
  │
  ├── AWS WAF (rate limit, bot control, IP reputation, SQLi/XSS)
  │
  ▼
Application Load Balancer (sticky sessions, 86400s LB cookie)
  │                         [Public Subnets — 2 AZs]
  ▼
ECS Fargate (port 8501)
  │                         [Private Subnets — 2 AZs]
  │
  ├──→ Amazon Bedrock (Converse API)         [via NAT Gateway]
  ├──→ Web Grounding (nova_grounding tool)   [via NAT Gateway]
  └──→ CloudWatch Logs                       [via VPC endpoint]
```

### ECS Task Definition

| Parameter | Value |
|:---|:---|
| CPU | 512 (0.5 vCPU) |
| Memory | 1024 MB |
| Launch type | FARGATE |
| Container port | 8501 (Streamlit) |
| Health check | `curl -f http://localhost:8501/_stcore/health` (30s interval, 3 retries) |
| Deployment | Circuit breaker with auto-rollback |
| Secrets | AWS Secrets Manager (Bedrock credentials injected at runtime) |
| Logging | CloudWatch via `awslogs` driver |

### WAF Rules

| Priority | Rule | Configuration |
|:---:|:---|:---|
| 1 | Rate Limiting | 2000 requests / 5 min per IP |
| 2 | IP Reputation | `AWSManagedRulesAmazonIpReputationList` |
| 3 | Bot Control | `AWSManagedRulesBotControlRuleSet` |
| 4 | Common Attacks | `AWSManagedRulesCommonRuleSet` (SQLi, XSS) with upload path exception |

### Container Security

- **Non-root user** (`koda:koda`) — OWASP CSVS-2.1
- **Read-only filesystem** — OWASP CSVS-2.2
- **All capabilities dropped** — minimal attack surface
- **No privilege escalation** — `no-new-privileges: true`
- **Multi-stage build** — production image contains no build tools

---

## Network Architecture

### VPC Layout

| Subnet Type | CIDR | AZs | Purpose |
|:---|:---|:---:|:---|
| Public | `10.0.0.0/24`, `10.0.1.0/24` | 2 | ALB, NAT Gateway |
| Private | `10.0.10.0/24`, `10.0.11.0/24` | 2 | ECS Fargate tasks |

### Security Group Rules

**ALB Security Group:**
- Ingress: ports 80, 443 from `0.0.0.0/0`
- Egress: all outbound

**ECS Security Group:**
- Ingress: port 8501 from ALB SG only
- Egress: port 443 (Bedrock API, Web Grounding), port 53 UDP (DNS)

---

## CI/CD Pipeline

### Continuous Integration (`.github/workflows/ci.yml`)

Triggered on push to `main`/`develop` and PRs to `main`:

| Job | Steps |
|:---|:---|
| **Lint & Format** | `ruff check`, `ruff format --check`, `mypy src/` |
| **Security Scan** | `bandit -c pyproject.toml -r src/` |
| **Dockerfile Lint** | Hadolint with warning threshold |
| **Docker Build & Scan** | Build image → Trivy vulnerability scan (fail on CRITICAL) |
| **Unit Tests** | `pytest tests/unit/ -v -m unit` (no AWS credentials) |
| **Integration Tests** | `pytest tests/integration/ -v -m integration` (main branch only) |
| **Terraform Validate** | `terraform fmt -check`, `terraform init`, `terraform validate` |

### Continuous Deployment (`.github/workflows/deploy.yml`)

Triggered on push to `main`:

| Step | Details |
|:---|:---|
| **Authentication** | GitHub OIDC → AWS IAM role (no long-lived keys) |
| **Build** | Docker image tagged with commit SHA |
| **Push** | Amazon ECR |
| **Deploy** | Update ECS task definition → update service → circuit breaker monitors health |

---

## Privacy Model

| Principle | Implementation |
|:---|:---|
| **No accounts** | No login, no registration, no user tracking |
| **No persistence** | Sessions in-memory only, never written to disk or database |
| **Auto-expiry** | Sessions expire after 30 min inactivity |
| **No analytics** | No third-party tracking scripts or telemetry |
| **Minimal data** | Documents processed ephemerally; metadata stored, content discarded |
| **Transport security** | HTTPS enforced via CloudFront TLS termination |
| **GDPR Art. 25** | Privacy by design — data minimization as architectural constraint |
| **AWS data terms** | All AI processing via Amazon Bedrock (no data used for model training) |
