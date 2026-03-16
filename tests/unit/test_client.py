"""Unit tests for Bedrock response parsing helpers."""

import pytest
from src.core.client import NovaClient, strip_hidden_markers

pytestmark = pytest.mark.unit


def _make_response(text: str) -> dict:
    """Build a minimal Converse-style response containing *text*."""
    return {"output": {"message": {"content": [{"text": text}]}}}


class TestStripHiddenMarkers:
    def test_no_markers(self):
        assert strip_hidden_markers("Hello world") == "Hello world"

    def test_single_prefix(self):
        assert strip_hidden_markers("[HIDDEN]Hello") == "Hello"

    def test_multiple_consecutive(self):
        assert strip_hidden_markers("[HIDDEN][HIDDEN][HIDDEN]Hello") == "Hello"

    def test_marker_in_middle(self):
        assert strip_hidden_markers("Hello [HIDDEN] world") == "Hello  world"

    def test_only_markers(self):
        assert strip_hidden_markers("[HIDDEN][HIDDEN]") == ""

    def test_empty_string(self):
        assert strip_hidden_markers("") == ""


class TestExtractTextHiddenMarkers:
    def test_strips_single_prefix(self):
        assert NovaClient.extract_text(_make_response("[HIDDEN]Hi")) == "Hi"

    def test_strips_multiple_markers(self):
        assert NovaClient.extract_text(_make_response("[HIDDEN][HIDDEN]Hi")) == "Hi"

    def test_strips_marker_in_middle(self):
        result = NovaClient.extract_text(_make_response("Start [HIDDEN] end"))
        assert "[HIDDEN]" not in result

    def test_clean_text_unchanged(self):
        assert NovaClient.extract_text(_make_response("Just text")) == "Just text"


class TestIterStreamTextHiddenMarkers:
    def test_strips_hidden_from_chunks(self):
        fake_stream = [
            {"contentBlockDelta": {"delta": {"text": "[HIDDEN]"}}},
            {"contentBlockDelta": {"delta": {"text": "Hello"}}},
        ]
        chunks = list(NovaClient.iter_stream_text({"stream": fake_stream}))
        assert chunks == ["Hello"]

    def test_strips_hidden_within_chunk(self):
        fake_stream = [
            {"contentBlockDelta": {"delta": {"text": "[HIDDEN]Hello [HIDDEN]world"}}},
        ]
        chunks = list(NovaClient.iter_stream_text({"stream": fake_stream}))
        assert chunks == ["Hello world"]


class TestWebCitationExtraction:
    def test_extracts_citations_from_citations_content(self):
        response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "citationsContent": {
                                "citations": [
                                    {
                                        "title": "DAAD",
                                        "url": "https://www.daad.de/en/studying-in-germany/",
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

        citations = NovaClient.extract_web_citations(response)

        assert len(citations) == 1
        assert citations[0].title == "DAAD"
        assert citations[0].origin == "web_grounding"

    def test_extracts_citations_from_tool_result_json(self):
        response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolResult": {
                                "content": [
                                    {
                                        "json": {
                                            "results": [
                                                {
                                                    "sourceTitle": "hochschulstart",
                                                    "sourceUrl": "https://www.hochschulstart.de/",
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

        citations = NovaClient.extract_web_citations(response)

        assert len(citations) == 1
        assert citations[0].domain == "hochschulstart.de"

    def test_dedupes_duplicate_urls(self):
        response = {
            "output": {
                "message": {
                    "content": [
                        {
                            "citationsContent": {
                                "citations": [
                                    {"title": "DAAD", "url": "https://www.daad.de/en/"},
                                    {"label": "DAAD English", "link": "https://www.daad.de/en/"},
                                ]
                            }
                        }
                    ]
                }
            }
        }

        citations = NovaClient.extract_web_citations(response)

        assert len(citations) == 1
