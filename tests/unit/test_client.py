"""Unit tests for Bedrock response parsing helpers."""

import pytest
from src.core.client import NovaClient

pytestmark = pytest.mark.unit


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
