"""Unit tests for the Router Agent."""

import os
import sys

sys.path.insert(0, ".")

import pytest

from src.agents.router import RouterAgent

# Skip tests if AWS credentials are not available
pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(
        not (os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE")),
        reason="AWS credentials required for router tests",
    ),
]


@pytest.fixture
def router():
    return RouterAgent()


class TestRouterClassification:
    def test_financial_question(self, router):
        assert router.route("What is BAföG and am I eligible?") == "FINANCING"

    def test_financial_german(self, router):
        assert router.route("Was ist BAföG?") == "FINANCING"

    def test_study_choice(self, router):
        assert router.route("Which degree program should I choose?") == "STUDY_CHOICE"

    def test_terminology(self, router):
        assert router.route("What does Immatrikulation mean?") == "ACADEMIC_BASICS"

    def test_impostor(self, router):
        assert router.route("I feel like I don't belong at university") == "ROLE_MODELS"

    def test_general(self, router):
        assert router.route("Hello, I don't know where to start") == "COMPASS"
