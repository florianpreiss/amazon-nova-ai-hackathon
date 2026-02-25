# KODA — AI Companion for First-Generation Academics

> *Japanese: "here, at this point" · Dakota Sioux: "friend, ally"*
> You've arrived somewhere new. And you're not alone.

[![Amazon Nova](https://img.shields.io/badge/Built%20with-Amazon%20Nova%202-FF9900?style=flat-square)](https://aws.amazon.com/nova/)
[![Hackathon](https://img.shields.io/badge/Amazon%20Nova-AI%20Hackathon-blue?style=flat-square)](https://amazon-nova.devpost.com/)
[![Category](https://img.shields.io/badge/Category-Agentic%20AI-7C3AED?style=flat-square)]()

## Problem

In Germany only **27 out of 100** children from non-academic families start university — compared to **79 out of 100** from academic families. Those who enroll face an invisible wall: the **hidden curriculum** — unwritten rules, institutional jargon, financial systems, and social codes that continuing-generation students absorb from family.

## Solution

KODA is a **multi-agent agentic AI system** that decodes the hidden curriculum, 24/7, anonymously, for free — in the user's own language.

| Agent | Domain | Nova Features |
|-------|--------|---------------|
| **Financing** | Student aid, scholarships, cost-of-living, jobs | Code Interpreter · Web Grounding |
| **Study Choice** | Degree programs, universities, applications | Web Grounding · Extended Thinking |
| **Academic Basics** | Hidden curriculum decoder, terminology, study vs. apprenticeship | Extended Thinking (HIGH) |
| **Role Models** | First-gen role models, career visions, anti-impostor support | Extended Thinking (HIGH) |

Plus: **Router Agent** · **Crisis Radar** (parallel safety) · **Anti-Shame Filter** · **Intersectionality Layer** · **Multilingual** (responds in user's language)

## Architecture

```
User Message ──┬──► Router Agent (Extended Thinking LOW — fast triage)
               │         ├──► Financing Agent   (Code Interpreter + Web Grounding)
               │         ├──► Study Choice Agent (Web Grounding + Extended Thinking HIGH)
               │         ├──► Academic Basics    (Extended Thinking HIGH) ← signature feature
               │         └──► Role Models Agent  (Extended Thinking HIGH)
               └──► Crisis Radar (parallel on every message)
```

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/koda.git && cd koda
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add AWS credentials
python scripts/verify_setup.py  # test all Nova features
uvicorn src.api.app:app --reload --port 8000
```

## Project Structure

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

## License

MIT

*27 out of 100. KODA exists for those 27.* · #AmazonNova
