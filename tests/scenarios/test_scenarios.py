"""
Scenario-based tests for KODA.

Two test classes:
  1. ``TestRouterScenarios`` — verifies that the RouterAgent classifies each
     scenario's input to the expected agent. Uses a mocked Bedrock client so
     no AWS credentials are required (marked ``unit``).

  2. ``TestFullScenarios`` — sends each scenario through the full agent
     pipeline and checks ``must_contain_any`` / ``must_not_contain`` rules.
     Requires live AWS credentials (marked ``integration``, auto-skipped
     when credentials are absent).

Scenarios are loaded dynamically from JSON files in this directory so that
new test cases can be added without touching Python code — just drop a new
``.json`` file.

JSON schema per scenario file:
  {
    "id":               str   — unique slug,
    "description":      str   — human-readable intent,
    "input":            str   — user message to send,
    "language":         str   — "de" | "en" | ...,
    "expected_agent":   str   — one of COMPASS / FINANCING / STUDY_CHOICE /
                                ACADEMIC_BASICS / ROLE_MODELS,
    "must_contain_any": list  — at least ONE of these substrings (case-insensitive)
                                must appear in the agent response,
    "must_not_contain": list  — NONE of these substrings may appear in the
                                agent response (anti-shame filter smoke test)
  }
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when tests are run directly
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parents[2]))

# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------

SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"


def _load_scenarios() -> list[dict]:
    """Return all scenario dicts from JSON files in the scenarios directory."""
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            scenarios.append(json.load(fh))
    return scenarios


ALL_SCENARIOS = _load_scenarios()
SCENARIO_IDS = [s["id"] for s in ALL_SCENARIOS]

# ---------------------------------------------------------------------------
# Shared mock Bedrock factory
# ---------------------------------------------------------------------------


def _make_mock_bedrock(agent_name: str) -> MagicMock:
    """Return a boto3 mock that always routes to *agent_name*."""
    bedrock_mock = MagicMock()

    def _side_effect(**kwargs):
        max_tokens = kwargs.get("inferenceConfig", {}).get("maxTokens", 4096)
        if max_tokens == 50:
            return {"output": {"message": {"content": [{"text": f"AGENT: {agent_name}"}]}}}
        if max_tokens == 100:
            return {"output": {"message": {"content": [{"text": "CRISIS: NO"}]}}}
        return {"output": {"message": {"content": [{"text": "Test response content."}]}}}

    bedrock_mock.converse.side_effect = _side_effect
    return bedrock_mock


# ---------------------------------------------------------------------------
# 1. Unit — router classification (no AWS required)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=SCENARIO_IDS)
class TestRouterScenarios:
    """Verify that the RouterAgent maps each input to the expected agent."""

    def test_routes_to_expected_agent(self, scenario: dict) -> None:
        expected = scenario["expected_agent"]
        mock_bedrock = _make_mock_bedrock(expected)

        with patch("boto3.client", return_value=mock_bedrock):
            from src.agents.router import RouterAgent

            router = RouterAgent()
            result = router.route(scenario["input"])

        assert result == expected, (
            f"Scenario '{scenario['id']}': expected agent '{expected}', got '{result}'.\n"
            f"Input: {scenario['input']}"
        )


# ---------------------------------------------------------------------------
# 2. Integration — full pipeline with real AWS (skipped without credentials)
# ---------------------------------------------------------------------------

_HAS_AWS = bool(os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"))


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_AWS, reason="AWS credentials required for full scenario tests")
@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=SCENARIO_IDS)
class TestFullScenarios:
    """
    End-to-end scenario runner: calls real Bedrock and checks response
    content rules.

    Requires: valid AWS credentials + Bedrock access to Nova 2 Lite.
    """

    def test_must_contain_any(self, scenario: dict) -> None:
        """Response must include at least one of the must_contain_any keywords."""
        from src.agents.academic_basics.hidden_curriculum import (
            HiddenCurriculumAgent,
        )
        from src.agents.compass import CompassAgent
        from src.agents.financing.student_aid import StudentAidAgent
        from src.agents.role_models.anti_impostor import AntiImpostorAgent
        from src.agents.router import RouterAgent
        from src.agents.study_choice.degree_explorer import DegreeExplorerAgent

        agents = {
            "COMPASS": CompassAgent(),
            "FINANCING": StudentAidAgent(),
            "STUDY_CHOICE": DegreeExplorerAgent(),
            "ACADEMIC_BASICS": HiddenCurriculumAgent(),
            "ROLE_MODELS": AntiImpostorAgent(),
        }

        messages = [{"role": "user", "content": [{"text": scenario["input"]}]}]
        agent_key = RouterAgent().route(scenario["input"])
        agent = agents.get(agent_key, agents["COMPASS"])
        response = agent.respond(messages).lower()

        required = scenario.get("must_contain_any", [])
        if required:
            assert any(kw.lower() in response for kw in required), (
                f"Scenario '{scenario['id']}': response did not contain any of "
                f"{required}.\nResponse snippet: {response[:300]}"
            )

    def test_must_not_contain(self, scenario: dict) -> None:
        """Response must not contain any shame-reinforcing patterns."""
        from src.agents.academic_basics.hidden_curriculum import (
            HiddenCurriculumAgent,
        )
        from src.agents.compass import CompassAgent
        from src.agents.financing.student_aid import StudentAidAgent
        from src.agents.role_models.anti_impostor import AntiImpostorAgent
        from src.agents.router import RouterAgent
        from src.agents.study_choice.degree_explorer import DegreeExplorerAgent

        agents = {
            "COMPASS": CompassAgent(),
            "FINANCING": StudentAidAgent(),
            "STUDY_CHOICE": DegreeExplorerAgent(),
            "ACADEMIC_BASICS": HiddenCurriculumAgent(),
            "ROLE_MODELS": AntiImpostorAgent(),
        }

        messages = [{"role": "user", "content": [{"text": scenario["input"]}]}]
        agent_key = RouterAgent().route(scenario["input"])
        agent = agents.get(agent_key, agents["COMPASS"])
        response = agent.respond(messages).lower()

        forbidden = scenario.get("must_not_contain", [])
        for pattern in forbidden:
            assert pattern.lower() not in response, (
                f"Scenario '{scenario['id']}': response contained forbidden "
                f"shame pattern '{pattern}'.\nResponse snippet: {response[:300]}"
            )
