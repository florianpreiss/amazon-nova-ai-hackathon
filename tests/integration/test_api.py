"""
Integration tests for the KODA FastAPI application.

These tests run the full HTTP stack against a live FastAPI instance but
mock the underlying Bedrock client so no AWS credentials are required.
They verify that:
  - the /api/health endpoint returns the expected shape
  - the /api/chat endpoint returns a valid ChatResponse for both German
    and English messages
  - the /api/session DELETE endpoint removes a session
  - the chat endpoint creates a new session when none is provided

Mark: ``pytest.mark.integration``
Run with: pytest -m integration
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MOCK_CONVERSE_RESPONSE = {
    "output": {"message": {"content": [{"text": "Das ist eine Testantwort."}]}}
}

_MOCK_ROUTE_RESPONSE = {"output": {"message": {"content": [{"text": "AGENT: COMPASS"}]}}}

_MOCK_CRISIS_RESPONSE = {"output": {"message": {"content": [{"text": "CRISIS: NO"}]}}}


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with Bedrock calls mocked out."""
    with patch("boto3.client") as mock_boto:
        bedrock_mock = MagicMock()

        def _side_effect(**kwargs):
            """Return different canned responses based on max_tokens."""
            max_tokens = kwargs.get("inferenceConfig", {}).get("maxTokens", 4096)
            if max_tokens == 50:
                # Router call uses max_tokens=50
                return _MOCK_ROUTE_RESPONSE
            if max_tokens == 100:
                # Crisis radar uses max_tokens=100
                return _MOCK_CRISIS_RESPONSE
            return _MOCK_CONVERSE_RESPONSE

        bedrock_mock.converse.side_effect = _side_effect
        mock_boto.return_value = bedrock_mock

        # Import app *after* patching so NovaClient uses the mock
        from src.api.app import app

        yield TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_returns_ok(self, client: "TestClient") -> None:
        """GET /api/health must return status=ok and the agent list."""
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "agents" in body
        expected_agents = {"COMPASS", "FINANCING", "STUDY_CHOICE", "ACADEMIC_BASICS", "ROLE_MODELS"}
        assert expected_agents == set(body["agents"])


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestChatEndpoint:
    def test_chat_creates_session(self, client: "TestClient") -> None:
        """A chat request without session_id must return a valid session_id."""
        response = client.post("/api/chat", json={"message": "Hello KODA"})
        assert response.status_code == 200
        body = response.json()
        assert body["session_id"]
        assert isinstance(body["response"], str)
        assert len(body["response"]) > 0

    def test_chat_continues_session(self, client: "TestClient") -> None:
        """A follow-up message with an existing session_id must reuse the session."""
        first = client.post("/api/chat", json={"message": "Hallo"})
        session_id = first.json()["session_id"]

        second = client.post(
            "/api/chat",
            json={"message": "Was ist BAföG?", "session_id": session_id},
        )
        assert second.status_code == 200
        assert second.json()["session_id"] == session_id

    def test_chat_response_schema(self, client: "TestClient") -> None:
        """Response must include all required ChatResponse fields."""
        response = client.post("/api/chat", json={"message": "What is ECTS?"})
        body = response.json()
        assert "session_id" in body
        assert "response" in body
        assert "agent_used" in body
        assert "crisis_detected" in body
        assert "provenance" in body

    def test_chat_german_message(self, client: "TestClient") -> None:
        """A German message must be accepted and return a response."""
        response = client.post(
            "/api/chat",
            json={"message": "Ich verstehe das Studium nicht. Kannst du mir helfen?"},
        )
        assert response.status_code == 200
        assert response.json()["response"]

    def test_chat_english_message(self, client: "TestClient") -> None:
        """An English message must be accepted and return a response."""
        response = client.post(
            "/api/chat",
            json={"message": "I feel like I don't belong at university."},
        )
        assert response.status_code == 200
        assert response.json()["response"]

    def test_chat_agent_used_is_valid(self, client: "TestClient") -> None:
        """agent_used in the response must be one of the registered agent keys."""
        valid_agents = {"COMPASS", "FINANCING", "STUDY_CHOICE", "ACADEMIC_BASICS", "ROLE_MODELS"}
        response = client.post("/api/chat", json={"message": "What is a Semesterbeitrag?"})
        assert response.json()["agent_used"] in valid_agents


# ---------------------------------------------------------------------------
# Onboarding endpoints
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOnboardingEndpoints:
    def test_start_onboarding_creates_session(self, client: "TestClient") -> None:
        """The onboarding start endpoint should create a session and first reply."""
        response = client.post("/api/onboarding/start", json={"language": "de"})

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"]
        assert body["response"]
        assert body["onboarding_state"] == "in_progress"
        assert body["completed"] is False

    def test_continue_onboarding_reuses_session(self, client: "TestClient") -> None:
        """A continued onboarding turn should reuse the same session."""
        first = client.post("/api/onboarding/start", json={"language": "de"})
        session_id = first.json()["session_id"]

        response = client.post(
            "/api/onboarding/continue",
            json={
                "session_id": session_id,
                "language": "de",
                "message": "Ich bin 17 und noch in der Schule.",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == session_id
        assert body["onboarding_state"] == "in_progress"

    def test_skip_onboarding_marks_session_skipped(self, client: "TestClient") -> None:
        """Skipping onboarding should mark the session accordingly."""
        response = client.post("/api/onboarding/skip", json={"language": "en"})

        assert response.status_code == 200
        body = response.json()
        assert body["session_id"]
        assert body["onboarding_state"] == "skipped"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSessionEndpoint:
    def test_delete_session(self, client: "TestClient") -> None:
        """DELETE /api/session/{id} must return status=deleted."""
        first = client.post("/api/chat", json={"message": "Hello"})
        session_id = first.json()["session_id"]

        delete_response = client.delete(f"/api/session/{session_id}")
        assert delete_response.status_code == 200
        assert delete_response.json() == {"status": "deleted"}

    def test_delete_nonexistent_session(self, client: "TestClient") -> None:
        """DELETE on an unknown session_id must still return 200 (idempotent)."""
        response = client.delete("/api/session/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 200

    def test_export_and_import_session_bundle(self, client: "TestClient") -> None:
        """A user can export a session bundle and load it into a fresh session."""
        first = client.post(
            "/api/chat",
            json={"message": "Ich brauche Hilfe bei BAföG.", "language": "de"},
        )
        session_id = first.json()["session_id"]

        export_response = client.get(f"/api/session/{session_id}/export")

        assert export_response.status_code == 200
        bundle = export_response.json()
        assert bundle["bundle_type"] == "koda_session_memory"
        assert bundle["session"]["preferences"]["response_language"] == "de"
        assert len(bundle["session"]["messages"]) == 2

        import_response = client.post("/api/session/import", json=bundle)

        assert import_response.status_code == 200
        imported = import_response.json()
        assert imported["session_id"] != session_id
        assert imported["language"] == "de"
        assert imported["message_count"] == 2

        continued = client.post(
            "/api/chat",
            json={
                "message": "Und wie geht es jetzt weiter?",
                "session_id": imported["session_id"],
                "language": "de",
            },
        )

        assert continued.status_code == 200
        assert continued.json()["session_id"] == imported["session_id"]

    def test_export_missing_session_returns_404(self, client: "TestClient") -> None:
        """Exporting an unknown session should fail clearly."""
        response = client.get("/api/session/00000000-0000-0000-0000-000000000000/export")

        assert response.status_code == 404

    def test_import_rejects_tampered_session_bundle(self, client: "TestClient") -> None:
        """Checksum validation should still happen on the API import path."""
        first = client.post("/api/chat", json={"message": "Hello", "language": "en"})
        session_id = first.json()["session_id"]
        bundle = client.get(f"/api/session/{session_id}/export").json()
        bundle["session"]["active_goals"] = ["This payload was tampered with."]

        response = client.post("/api/session/import", json=bundle)

        assert response.status_code == 400
        assert "checksum" in response.json()["detail"].lower()
