# KODA Architecture

## System Flow

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
│      Cross-cutting layers        │◄──┘
│  • Anti-Shame Filter             │
│  • Intersectionality Engine      │
│  • Multilingual (auto-detect)    │
└────────────┬─────────────────────┘
             ▼
┌──────────────────────────────────┐
│         User Response            │
│   (in user's own language)       │
└──────────────────────────────────┘
```

## Agent Inventory

| Agent | Module | Reasoning | Tools | Purpose |
|-------|--------|-----------|-------|---------|
| Router | `agents/router.py` | LOW | — | Message classification |
| Crisis Radar | `agents/crisis.py` | LOW | — | Parallel safety scan |
| Compass | `agents/compass.py` | LOW | — | First contact, orientation |
| Student Aid | `agents/financing/student_aid.py` | HIGH | Code Interpreter | BAföG calculations |
| Scholarships | `agents/financing/scholarships.py` | HIGH | Web Grounding | Scholarship search |
| Cost of Living | `agents/financing/cost_of_living.py` | HIGH | Code Interpreter | City cost comparisons |
| Degree Explorer | `agents/study_choice/degree_explorer.py` | HIGH | Web Grounding | Program discovery |
| University Finder | `agents/study_choice/university_finder.py` | HIGH | Web Grounding | Institution comparison |
| Application Guide | `agents/study_choice/application_guide.py` | HIGH | Web Grounding | Application walkthrough |
| Hidden Curriculum | `agents/academic_basics/hidden_curriculum.py` | HIGH | — | **Signature feature** |
| Study vs. Apprenticeship | `agents/academic_basics/study_vs_apprenticeship.py` | HIGH | — | Decision support |
| Role Model Matching | `agents/role_models/matching.py` | HIGH | — | Inspiration matching |
| Anti-Impostor | `agents/role_models/anti_impostor.py` | HIGH | — | Structural reframing |

**Total: 13 agents** (Router + Crisis Radar + Compass + 10 domain specialists)

## Multilingual Design

All prompts are written in English for maintainability. Every agent inherits a `LANGUAGE_INSTRUCTION` from `BaseAgent` that tells the model to auto-detect the user's language and respond in kind. This means:
- German user → German response
- English user → English response
- Any language → matched response

## Privacy by Design

- No login, no accounts, no persistent user data
- Sessions auto-expire after 30 min inactivity
- All processing via Amazon Bedrock (AWS data terms)
- No third-party analytics or tracking
- GDPR-compliant
