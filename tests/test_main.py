"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.api4clix.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_assistant_manager():
    """Create a mock assistant manager."""
    manager = AsyncMock()
    manager.get_available_assistants.return_value = ["copilot"]
    manager.get_assistant_status.return_value = {
        "copilot": {
            "name": "GitHub Copilot CLI",
            "available": True,
            "command": "gh"
        }
    }
    return manager


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_without_initialization(self, client):
        """Test health check when service is not initialized."""
        response = client.get("/health")
        assert response.status_code == 503  # Service unavailable

    def test_health_check_with_initialization(self, client, mock_assistant_manager):
        """Test health check when service is initialized."""
        with patch("src.api4clix.main.assistant_manager", mock_assistant_manager), \
             patch("src.api4clix.main.start_time", 100.0), \
             patch("time.time", return_value=200.0):

            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] is not None
            assert "copilot" in data["available_assistants"]
            assert data["uptime"] == 100.0


class TestChatEndpoint:
    """Tests for the chat endpoint."""

    def test_chat_success(self, client, mock_assistant_manager):
        """Test successful chat request."""
        mock_assistant_manager.chat.return_value = {
            "response": "Hello! How can I help you?",
            "metadata": {"command": "gh copilot suggest"}
        }

        with patch("src.api4clix.main.assistant_manager", mock_assistant_manager):
            response = client.post("/chat", json={
                "message": "Hello",
                "assistant_type": "copilot"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["response"] == "Hello! How can I help you?"
            assert data["assistant_type"] == "copilot"

    def test_chat_invalid_assistant(self, client, mock_assistant_manager):
        """Test chat request with invalid assistant type."""
        mock_assistant_manager.chat.side_effect = ValueError("Assistant 'invalid' is not available")

        with patch("src.api4clix.main.assistant_manager", mock_assistant_manager):
            response = client.post("/chat", json={
                "message": "Hello",
                "assistant_type": "invalid"
            })

            assert response.status_code == 400

    def test_chat_missing_message(self, client):
        """Test chat request with missing message."""
        response = client.post("/chat", json={
            "assistant_type": "copilot"
        })

        assert response.status_code == 422  # Validation error


class TestCodeEndpoints:
    """Tests for code-related endpoints."""

    @patch("src.api4clix.main.assistant_manager")
    def test_explain_code_success(self, mock_manager, client, mock_assistant_manager):
        """Test successful code explanation request."""
        mock_manager = mock_assistant_manager
        mock_manager.explain_code.return_value = {
            "explanation": "This function prints hello world",
            "language": "python"
        }

        response = client.post("/code/explain", json={
            "code": "print('Hello, World!')",
            "operation": "explain",
            "language": "python",
            "assistant_type": "copilot"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["explanation"] == "This function prints hello world"
        assert data["language"] == "python"

    @patch("src.api4clix.main.assistant_manager")
    def test_modify_code_success(self, mock_manager, client, mock_assistant_manager):
        """Test successful code modification request."""
        mock_manager = mock_assistant_manager
        mock_manager.modify_code.return_value = {
            "modified_code": "print('Hello, Python!')",
            "explanation": "Changed the greeting message",
            "language": "python"
        }

        response = client.post("/code/modify", json={
            "code": "print('Hello, World!')",
            "operation": "modify",
            "message": "Change to say Python instead of World",
            "language": "python",
            "assistant_type": "copilot"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["modified_code"] == "print('Hello, Python!')"
        assert data["explanation"] == "Changed the greeting message"

    def test_modify_code_missing_instructions(self, client):
        """Test code modification without instructions."""
        response = client.post("/code/modify", json={
            "code": "print('Hello, World!')",
            "operation": "modify",
            "assistant_type": "copilot"
        })

        assert response.status_code == 400


class TestCommitEndpoint:
    """Tests for the commit endpoint."""

    @patch("src.api4clix.main.assistant_manager")
    def test_generate_commit_success(self, mock_manager, client, mock_assistant_manager):
        """Test successful commit generation."""
        mock_manager = mock_assistant_manager
        mock_manager.generate_commit.return_value = {
            "generated_message": "feat: add new feature",
            "commit_hash": None,
            "files_committed": []
        }

        response = client.post("/git/commit", json={
            "assistant_type": "copilot"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["generated_message"] == "feat: add new feature"


class TestAssistantsEndpoint:
    """Tests for the assistants listing endpoint."""

    @patch("src.api4clix.main.assistant_manager")
    def test_list_assistants(self, mock_manager, client, mock_assistant_manager):
        """Test listing available assistants."""
        mock_manager = mock_assistant_manager

        response = client.get("/assistants")

        assert response.status_code == 200
        data = response.json()
        assert "assistants" in data
        assert "copilot" in data["assistants"]