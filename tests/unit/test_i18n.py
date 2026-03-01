"""
Unit tests for src/i18n/strings.py.

Ensures translation completeness: every key present in one language must be
present in every other supported language, and no value may be an empty string.

This catches the class of bug fixed in PR #25, where 12 `quick_*_msg` keys
were missing from the German locale, causing button clicks to display the raw
key name instead of the intended text.

No AWS credentials or network access required.
"""

import sys

sys.path.insert(0, ".")

import pytest
from src.i18n.strings import (
    AGENT_LABELS,
    DEFAULT_LANGUAGE,
    STRINGS,
    SUPPORTED_LANGUAGES,
    get_agent_label,
    t,
)

pytestmark = pytest.mark.unit

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(params=SUPPORTED_LANGUAGES)
def lang(request: pytest.FixtureRequest) -> str:
    """Parametrize a single language code over all supported languages."""
    return str(request.param)


@pytest.fixture
def reference_lang() -> str:
    """The language used as the reference key-set (English is the canonical baseline)."""
    return "en"


# ── STRINGS completeness ─────────────────────────────────────────────────────


class TestStringsCompleteness:
    """Every UI-string key must exist in all supported languages."""

    def test_all_languages_present_in_strings(self):
        """STRINGS dict must have an entry for every supported language."""
        for lang_code in SUPPORTED_LANGUAGES:
            assert lang_code in STRINGS, (
                f"Language '{lang_code}' listed in SUPPORTED_LANGUAGES "
                f"but missing from STRINGS dict"
            )

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_keys_missing_vs_english(self, lang_code):
        """Every key in the English locale must be present in every other locale."""
        english_keys = set(STRINGS["en"].keys())
        target_keys = set(STRINGS[lang_code].keys())
        missing = english_keys - target_keys
        assert not missing, (
            f"Locale '{lang_code}' is missing {len(missing)} key(s) that exist in 'en': "
            f"{sorted(missing)}"
        )

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_extra_keys_vs_english(self, lang_code):
        """No locale should have keys that don't exist in English (catches typos)."""
        english_keys = set(STRINGS["en"].keys())
        target_keys = set(STRINGS[lang_code].keys())
        extra = target_keys - english_keys
        assert not extra, (
            f"Locale '{lang_code}' has {len(extra)} key(s) not found in 'en' "
            f"(possible typo?): {sorted(extra)}"
        )

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_empty_string_values(self, lang_code):
        """No translation value may be an empty string."""
        empty_keys = [k for k, v in STRINGS[lang_code].items() if not v.strip()]
        assert (
            not empty_keys
        ), f"Locale '{lang_code}' has empty string values for keys: {sorted(empty_keys)}"

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_values_equal_to_key(self, lang_code):
        """
        A value equal to its own key strongly suggests the key was copy-pasted
        but never actually translated.  Allow it only for the single-word
        structural entries (e.g. "title": "KODA") by checking for spaces.
        """
        suspicious = [k for k, v in STRINGS[lang_code].items() if v == k and " " in k]
        assert not suspicious, (
            f"Locale '{lang_code}' has values that are identical to their key "
            f"(untranslated?): {sorted(suspicious)}"
        )


# ── AGENT_LABELS completeness ─────────────────────────────────────────────────


class TestAgentLabelsCompleteness:
    """Every agent key must be labelled in all supported languages."""

    def test_all_languages_present_in_agent_labels(self):
        """AGENT_LABELS dict must have an entry for every supported language."""
        for lang_code in SUPPORTED_LANGUAGES:
            assert lang_code in AGENT_LABELS, f"Language '{lang_code}' is missing from AGENT_LABELS"

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_agent_keys_missing_vs_english(self, lang_code):
        """Every agent key in English must be labelled in all other locales."""
        english_agents = set(AGENT_LABELS["en"].keys())
        target_agents = set(AGENT_LABELS[lang_code].keys())
        missing = english_agents - target_agents
        assert not missing, f"AGENT_LABELS['{lang_code}'] is missing agent(s): {sorted(missing)}"

    @pytest.mark.parametrize("lang_code", SUPPORTED_LANGUAGES)
    def test_no_empty_agent_labels(self, lang_code):
        """No agent label value may be an empty string."""
        empty = [k for k, v in AGENT_LABELS[lang_code].items() if not v.strip()]
        assert not empty, f"AGENT_LABELS['{lang_code}'] has empty labels for: {sorted(empty)}"


# ── Helper functions ──────────────────────────────────────────────────────────


class TestHelperFunctions:
    """Behavioural contract tests for t() and get_agent_label()."""

    def test_t_returns_correct_german_string(self):
        assert t("thinking", "de") == "KODA denkt nach..."

    def test_t_returns_correct_english_string(self):
        assert t("thinking", "en") == "KODA is thinking..."

    def test_t_falls_back_to_english_for_unknown_language(self):
        """Unknown language code must fall back to English, not crash."""
        result = t("thinking", "xx")
        assert result == t("thinking", "en")

    def test_t_returns_key_for_missing_key(self):
        """Missing key must return the key itself, not raise an exception."""
        result = t("this_key_does_not_exist", "en")
        assert result == "this_key_does_not_exist"

    def test_t_missing_key_in_any_lang(self):
        """Missing key in a real language also returns the key name."""
        result = t("this_key_does_not_exist", "de")
        assert result == "this_key_does_not_exist"

    def test_get_agent_label_german(self):
        assert get_agent_label("FINANCING", "de") == "Finanzberater"

    def test_get_agent_label_english(self):
        assert get_agent_label("FINANCING", "en") == "Finance Advisor"

    def test_get_agent_label_falls_back_to_english_for_unknown_language(self):
        result = get_agent_label("FINANCING", "xx")
        assert result == get_agent_label("FINANCING", "en")

    def test_get_agent_label_returns_key_for_unknown_agent(self):
        """Unknown agent code must return the code itself, not raise."""
        result = get_agent_label("UNKNOWN_AGENT", "en")
        assert result == "UNKNOWN_AGENT"


# ── Module-level invariants ───────────────────────────────────────────────────


class TestModuleInvariants:
    """Structural properties that must always hold."""

    def test_default_language_in_supported_languages(self):
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES, (
            f"DEFAULT_LANGUAGE='{DEFAULT_LANGUAGE}' is not in "
            f"SUPPORTED_LANGUAGES={SUPPORTED_LANGUAGES}"
        )

    def test_default_language_has_strings(self):
        assert DEFAULT_LANGUAGE in STRINGS

    def test_default_language_has_agent_labels(self):
        assert DEFAULT_LANGUAGE in AGENT_LABELS

    def test_supported_languages_non_empty(self):
        assert len(SUPPORTED_LANGUAGES) >= 1

    def test_strings_and_supported_languages_in_sync(self):
        """STRINGS keys and SUPPORTED_LANGUAGES must be identical sets."""
        assert set(STRINGS.keys()) == set(SUPPORTED_LANGUAGES), (
            f"STRINGS has locale(s) {set(STRINGS.keys())} "
            f"but SUPPORTED_LANGUAGES is {set(SUPPORTED_LANGUAGES)}"
        )

    def test_agent_labels_and_supported_languages_in_sync(self):
        """AGENT_LABELS keys and SUPPORTED_LANGUAGES must be identical sets."""
        assert set(AGENT_LABELS.keys()) == set(SUPPORTED_LANGUAGES), (
            f"AGENT_LABELS has locale(s) {set(AGENT_LABELS.keys())} "
            f"but SUPPORTED_LANGUAGES is {set(SUPPORTED_LANGUAGES)}"
        )
