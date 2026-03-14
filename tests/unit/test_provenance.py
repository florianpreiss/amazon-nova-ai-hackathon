"""Unit tests for source attribution and provenance helpers."""

import pytest
from src.core.provenance import (
    build_provenance_context,
    build_sourcing_addendum,
    build_web_source,
    infer_request_language,
    merge_provenance,
)

pytestmark = pytest.mark.unit


class TestProvenanceContext:
    def test_german_financing_query_uses_curated_registry(self):
        metadata = build_provenance_context(
            agent_key="FINANCING",
            user_message="Wie beantrage ich BAföG?",
            ui_language="en",
            tool_mode=None,
        )

        provenance = metadata["provenance"]
        assert provenance.mode == "source_registry"
        assert provenance.source_registry_used is True
        assert provenance.sources
        assert all(source.origin == "source_registry" for source in provenance.sources)

    def test_english_germany_query_uses_curated_registry(self):
        metadata = build_provenance_context(
            agent_key="STUDY_CHOICE",
            user_message="I want to study in Germany. How does Hochschulstart work?",
            ui_language="en",
            tool_mode="web_grounding",
        )

        provenance = metadata["provenance"]
        assert provenance.mode == "source_registry"
        assert provenance.source_registry_used is True
        assert provenance.web_grounding_used is True

    def test_general_english_query_skips_registry(self):
        metadata = build_provenance_context(
            agent_key="STUDY_CHOICE",
            user_message="How do I compare computer science degrees?",
            ui_language="en",
            tool_mode="web_grounding",
        )

        provenance = metadata["provenance"]
        assert provenance.mode == "web_grounding"
        assert provenance.source_registry_used is False
        assert provenance.sources == ()

    def test_compass_defaults_to_model_fallback(self):
        metadata = build_provenance_context(
            agent_key="COMPASS",
            user_message="I feel lost and do not know where to start.",
            ui_language="en",
            tool_mode=None,
        )

        provenance = metadata["provenance"]
        assert provenance.mode == "model"
        assert provenance.sources == ()


class TestSourcingPrompt:
    def test_addendum_lists_curated_sources(self):
        metadata = build_provenance_context(
            agent_key="FINANCING",
            user_message="Wie beantrage ich BAföG?",
            ui_language="de",
            tool_mode=None,
        )

        trusted_sources = metadata["trusted_sources"][:2]
        prompt = build_sourcing_addendum(trusted_sources)

        assert "FACTUAL SOURCING POLICY" in prompt
        assert trusted_sources[0].title in prompt
        assert trusted_sources[0].url in prompt

    def test_addendum_mentions_web_grounding_policy(self):
        prompt = build_sourcing_addendum(tool_mode="web_grounding")
        assert "Web Grounding" in prompt


class TestProvenanceMerging:
    def test_merge_keeps_registry_and_web_sources(self):
        metadata = build_provenance_context(
            agent_key="FINANCING",
            user_message="Wie beantrage ich BAföG?",
            ui_language="de",
            tool_mode="web_grounding",
        )

        merged = merge_provenance(
            metadata["provenance"],
            tool_mode="web_grounding",
            web_sources=(build_web_source("DAAD", "https://www.daad.de"),),
        )

        assert merged.mode == "source_registry_and_web"
        assert len(merged.sources) >= 2
        assert {source.origin for source in merged.sources} == {"source_registry", "web_grounding"}


class TestLanguageInference:
    def test_infer_request_language_prefers_message_over_ui_fallback(self):
        assert infer_request_language("Wie funktioniert BAföG?", "en") == "de"

    def test_infer_request_language_falls_back_when_ambiguous(self):
        assert infer_request_language("Deadline?", "en") == "en"
