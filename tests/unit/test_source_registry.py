"""Unit tests for the curated trusted-source registry."""

import pytest
from src.knowledge.source_registry import (
    SourceSelectionContext,
    get_trusted_sources,
    load_trusted_source_manifests,
    select_trusted_sources,
)

pytestmark = pytest.mark.unit


class TestTrustedSourceRegistry:
    def test_manifest_loads(self):
        manifests = load_trusted_source_manifests()
        assert manifests
        assert manifests[0].registry_id == "de-germany-curated-v1"

    def test_all_sources_have_unique_ids(self):
        source_ids = [source.id for source in get_trusted_sources()]
        assert source_ids
        assert len(source_ids) == len(set(source_ids))

    def test_registry_contains_expected_categories(self):
        categories = {source.category for source in get_trusted_sources()}
        assert categories == {
            "FINANCING",
            "STUDY_CHOICE",
            "ACADEMIC_BASICS",
            "ROLE_MODELS",
        }

    def test_manifest_is_german_and_germany_scoped(self):
        for source in get_trusted_sources():
            assert source.language == "de"
            assert source.country_codes == ("DE",)


class TestSelectionPolicy:
    def test_german_language_uses_registry(self):
        selection = select_trusted_sources(
            SourceSelectionContext(
                user_language="de-DE",
                user_message="Wie beantrage ich BAföG?",
            ),
            category="FINANCING",
        )

        assert selection.use_registry is True
        assert selection.reason == "language_match"
        assert selection.sources
        assert all(source.category == "FINANCING" for source in selection.sources)

    def test_english_query_about_germany_uses_registry(self):
        selection = select_trusted_sources(
            SourceSelectionContext(
                user_language="en",
                user_message="How does BAföG work if I want to study in Germany?",
            ),
            category="FINANCING",
            limit=3,
        )

        assert selection.use_registry is True
        assert selection.reason == "germany_focus"
        assert len(selection.sources) == 3

    def test_general_english_query_skips_registry(self):
        selection = select_trusted_sources(
            SourceSelectionContext(
                user_language="en",
                user_message="How do scholarships usually work for college students?",
            ),
            category="FINANCING",
        )

        assert selection.use_registry is False
        assert selection.reason == "policy_not_matched"
        assert selection.sources == ()

    def test_explicit_country_code_uses_registry(self):
        selection = select_trusted_sources(
            SourceSelectionContext(
                user_language="en",
                user_message="I am comparing universities.",
                country_code="DE",
            ),
            category="STUDY_CHOICE",
        )

        assert selection.use_registry is True
        assert selection.reason == "germany_focus"
        assert selection.sources

    def test_invalid_limit_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            select_trusted_sources(
                SourceSelectionContext(user_language="de", user_message="Was ist BAföG?"),
                limit=0,
            )
