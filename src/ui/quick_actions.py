"""Helpers for adaptive quick-action suggestions in the Streamlit app."""

from __future__ import annotations

from src.core.conversation import PersonalizedPrompt, SessionMemorySnapshot

_FINANCING_TOPICS = {"BAfoeG", "scholarships", "semester fees", "financing"}
_STUDY_CHOICE_TOPICS = {
    "study choice",
    "general guidance",
    "Ausbildung",
    "dual study",
}
_ACADEMIC_TOPICS = {"ECTS", "applications", "deadlines", "module handbook", "academic basics"}
_SUPPORT_TOPICS = {"self-doubt", "role models"}
_MAX_PROMPTS = 6


def build_quick_action_prompts(
    snapshot: SessionMemorySnapshot | None,
    *,
    ui_language: str,
    limit: int = _MAX_PROMPTS,
) -> tuple[PersonalizedPrompt, ...]:
    """Build adaptive quick-action prompts from the current session memory."""

    if snapshot is None:
        return ()

    prompts: list[PersonalizedPrompt] = []
    latest_goal = _latest_goal(snapshot)
    latest_topic = snapshot.topics[-1] if snapshot.topics else None
    current_agent = snapshot.current_agent or ""
    profile_text = _build_profile_text(snapshot)
    should_prioritize_onboarding = snapshot.message_count <= 2 and bool(
        snapshot.personalized_prompts
    )

    if should_prioritize_onboarding:
        prompts.extend(snapshot.personalized_prompts)

    prompts.extend(_profile_prompts(profile_text=profile_text, ui_language=ui_language))

    if latest_goal:
        prompts.append(
            _prompt(
                label_de="Passender Start",
                message_de=(
                    f"Wenn du meine Situation mitdenkst: Was wäre jetzt ein guter erster "
                    f"Schritt in Bezug auf '{latest_goal}'?"
                ),
                label_en="Best starting point",
                message_en=(
                    f"Keeping my situation in mind, what would be a good first step "
                    f"regarding '{latest_goal}'?"
                ),
                ui_language=ui_language,
            )
        )

    prompts.extend(
        _topic_prompts(
            latest_topic=latest_topic,
            current_agent=current_agent,
            ui_language=ui_language,
        )
    )

    if not should_prioritize_onboarding:
        for prompt in snapshot.personalized_prompts:
            prompts.append(prompt)

    if latest_goal:
        prompts.append(
            _prompt(
                label_de="Nächste Fragen",
                message_de=(
                    f"Welche Fragen sollte ich als Nächstes zu '{latest_goal}' stellen, "
                    "damit ich besser entscheiden kann?"
                ),
                label_en="Helpful questions",
                message_en=(
                    f"What questions should I ask next about '{latest_goal}' "
                    "so I can make a better decision?"
                ),
                ui_language=ui_language,
            )
        )

    deduped: list[PersonalizedPrompt] = []
    seen: set[str] = set()
    for prompt in prompts:
        key = f"{prompt.label.casefold()}::{prompt.message.casefold()}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(prompt)

    return tuple(deduped[:limit])


def _latest_goal(snapshot: SessionMemorySnapshot) -> str | None:
    if not snapshot.active_goals:
        return None
    latest = str(snapshot.active_goals[-1]).strip()
    return latest or None


def _build_profile_text(snapshot: SessionMemorySnapshot) -> str:
    text_parts: list[str] = []
    if snapshot.profile_summary:
        text_parts.append(str(snapshot.profile_summary))
    text_parts.extend(str(item) for item in snapshot.profile_facts)
    text_parts.extend(str(item) for item in snapshot.active_goals[-2:])
    return " ".join(text_parts).casefold()


def _profile_prompts(*, profile_text: str, ui_language: str) -> tuple[PersonalizedPrompt, ...]:
    prompts: list[PersonalizedPrompt] = []

    if any(
        token in profile_text
        for token in ("architektur", "bauingenieurwesen", "architecture", "civil engineering")
    ):
        prompts.append(
            _prompt(
                label_de="Architektur vs Bau",
                message_de=(
                    "Was sind die wichtigsten Unterschiede zwischen Architektur und "
                    "Bauingenieurwesen im Studium, im Uni-Alltag und später im Beruf?"
                ),
                label_en="Architecture vs civil",
                message_en=(
                    "What are the main differences between architecture and civil engineering "
                    "in the degree, university life, and later jobs?"
                ),
                ui_language=ui_language,
            )
        )

    if any(token in profile_text for token in ("bafög", "bafoeg", "finanz", "stipend")):
        prompts.append(
            _prompt(
                label_de="Finanzierung verstehen",
                message_de=(
                    "Kannst du mir die wichtigsten Finanzierungswege für meine Situation "
                    "kurz vergleichen, besonders BAföG, Stipendien und Nebenjob?"
                ),
                label_en="Understand funding",
                message_en=(
                    "Can you briefly compare the most relevant funding paths for my situation, "
                    "especially student aid, scholarships, and part-time work?"
                ),
                ui_language=ui_language,
            )
        )

    if any(
        token in profile_text
        for token in ("uni erwartet", "what to expect", "erwartet wird", "university expects")
    ):
        prompts.append(
            _prompt(
                label_de="Uni-Alltag verstehen",
                message_de=(
                    "Was erwartet mich an der Uni wirklich im Alltag, zum Beispiel bei "
                    "Vorlesungen, Selbstorganisation, Prüfungen und Abgaben?"
                ),
                label_en="Understand university life",
                message_en=(
                    "What should I realistically expect from university life, for example "
                    "lectures, self-organization, exams, and assignments?"
                ),
                ui_language=ui_language,
            )
        )

    if any(
        token in profile_text
        for token in ("unsicher", "uncertain", "ob ich studieren", "whether i should study")
    ):
        prompts.append(
            _prompt(
                label_de="Passt Studium zu mir?",
                message_de=(
                    "Kannst du mir helfen herauszufinden, ob ein Studium wirklich zu mir passt "
                    "oder ob ein anderer Weg besser wäre?"
                ),
                label_en="Is university right?",
                message_en=(
                    "Can you help me figure out whether university really fits me "
                    "or whether another path might suit me better?"
                ),
                ui_language=ui_language,
            )
        )

    if any(token in profile_text for token in ("abitur", "abi", "school", "schule")):
        prompts.append(
            _prompt(
                label_de="Nach dem Abi",
                message_de=(
                    "Was kann ich schon vor dem Abi oder direkt danach tun, damit mein Start "
                    "ins Studium später leichter wird?"
                ),
                label_en="After school",
                message_en=(
                    "What can I already do before finishing school, or right after, "
                    "to make the transition into university easier?"
                ),
                ui_language=ui_language,
            )
        )

    return tuple(prompts)


def _topic_prompts(
    *,
    latest_topic: str | None,
    current_agent: str,
    ui_language: str,
) -> tuple[PersonalizedPrompt, ...]:
    if latest_topic in _FINANCING_TOPICS or current_agent == "FINANCING":
        return (
            _prompt(
                label_de="Realistische Wege",
                message_de="Welche Finanzierungsmöglichkeiten sind für meine Situation gerade wirklich realistisch?",
                label_en="Realistic paths",
                message_en="Which funding options are actually realistic for my situation right now?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Stipendien für mich",
                message_de="Welche Stipendien oder Zuschüsse könnten gerade besonders gut zu meinem Hintergrund passen?",
                label_en="My scholarships",
                message_en="Which scholarships or grants could fit my background especially well right now?",
                ui_language=ui_language,
            ),
        )

    if latest_topic in _STUDY_CHOICE_TOPICS or current_agent in {"STUDY_CHOICE", "COMPASS"}:
        return (
            _prompt(
                label_de="Wege vergleichen",
                message_de=(
                    "Kannst du die Wege Studium, Ausbildung und duales Studium so vergleichen, "
                    "dass ich besser einschätzen kann, was gerade zu mir passt?"
                ),
                label_en="Compare paths",
                message_en=(
                    "Can you compare university, an apprenticeship, and a dual study path "
                    "in a way that helps me judge what fits me best right now?"
                ),
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Was passt zu mir?",
                message_de=(
                    "Welche Fragen sollte ich mir stellen, um besser herauszufinden, "
                    "welche Studienfelder oder Berufsrichtungen wirklich zu mir passen?"
                ),
                label_en="What fits me?",
                message_en=(
                    "What questions should I ask myself to better understand which study fields "
                    "or career directions actually fit me?"
                ),
                ui_language=ui_language,
            ),
        )

    if latest_topic in _ACADEMIC_TOPICS or current_agent == "ACADEMIC_BASICS":
        focus = latest_topic or ("Uni-Grundlagen" if ui_language == "de" else "academic basics")
        return (
            _prompt(
                label_de="Einfach erklärt",
                message_de=f"Kannst du mir {focus} in einfachen Worten erklären und direkt sagen, was davon für mich gerade wichtig ist?",
                label_en="Explain simply",
                message_en=f"Can you explain {focus} in simple words and tell me what part of it matters for me right now?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Worauf achten?",
                message_de=f"Worauf sollte ich bei {focus} besonders achten, damit ich keine wichtigen Dinge verpasse?",
                label_en="What to watch",
                message_en=f"What should I watch out for in {focus} so I do not miss the important parts?",
                ui_language=ui_language,
            ),
        )

    if latest_topic in _SUPPORT_TOPICS or current_agent == "ROLE_MODELS":
        return (
            _prompt(
                label_de="Mutmacher",
                message_de="Kannst du mir Vorbilder oder Geschichten von Menschen zeigen, die einen ähnlichen Hintergrund hatten wie ich?",
                label_en="Role models",
                message_en="Can you show me role models or stories from people who had a background similar to mine?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Zweifel sortieren",
                message_de="Wie kann ich meine Zweifel besser einordnen, ohne vorschnell aufzugeben oder mich klein zu machen?",
                label_en="Sort out doubts",
                message_en="How can I sort through my doubts without giving up too quickly or talking myself down?",
                ui_language=ui_language,
            ),
        )

    return ()


def _prompt(
    *,
    label_de: str,
    message_de: str,
    label_en: str,
    message_en: str,
    ui_language: str,
) -> PersonalizedPrompt:
    if ui_language == "de":
        return PersonalizedPrompt(label=label_de, message=message_de)
    return PersonalizedPrompt(label=label_en, message=message_en)
