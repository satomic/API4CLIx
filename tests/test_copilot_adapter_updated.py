"""Tests for the updated Copilot CLI adapter."""

import pytest
from unittest.mock import AsyncMock, patch

from src.adapters.copilot import CopilotAdapter


@pytest.fixture
def copilot_adapter():
    """Create a Copilot adapter instance."""
    return CopilotAdapter()


class TestCopilotAdapter:
    """Tests for CopilotAdapter class."""

    @pytest.mark.asyncio
    async def test_is_available_success(self, copilot_adapter):
        """Test successful availability check."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "0.0.348\nCommit: 946b5dc",
                "stderr": "",
                "return_code": 0
            }

            result = await copilot_adapter.is_available()
            assert result is True
            assert copilot_adapter._available is True

    @pytest.mark.asyncio
    async def test_is_available_copilot_not_installed(self, copilot_adapter):
        """Test availability check when Copilot CLI is not installed."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {"success": False, "stdout": "", "stderr": "command not found", "return_code": 1}

            result = await copilot_adapter.is_available()
            assert result is False
            assert copilot_adapter._available is False

    @pytest.mark.asyncio
    async def test_chat_success(self, copilot_adapter):
        """Test successful chat interaction."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Hello! I'm GitHub Copilot CLI, your terminal assistant. I can help you with various software engineering tasks.",
                "stderr": "",
                "return_code": 0
            }

            result = await copilot_adapter.chat("Hello, what can you help me with?")

            assert "response" in result
            assert result["response"] is not None
            assert "metadata" in result
            mock_run.assert_called_once()
            # Check that the command used copilot with -p flag
            args = mock_run.call_args[0][0]
            assert args[0] == "copilot"
            assert "-p" in args

    @pytest.mark.asyncio
    async def test_chat_failure(self, copilot_adapter):
        """Test chat interaction failure."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": False,
                "stdout": "",
                "stderr": "Authentication required",
                "return_code": 1
            }

            result = await copilot_adapter.chat("How do I create a Python function?")

            assert "error" in result
            assert result["response"] is None
            assert "Authentication required" in result["error"]

    @pytest.mark.asyncio
    async def test_explain_code_success(self, copilot_adapter):
        """Test successful code explanation."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "This function prints a greeting message to the console using Python's built-in print function.",
                "stderr": "",
                "return_code": 0
            }

            result = await copilot_adapter.explain_code("print('Hello, World!')", language="python")

            assert "explanation" in result
            assert result["explanation"] is not None
            assert result["language"] == "python"
            mock_run.assert_called_once()
            # Check that the command used copilot with -p flag
            args = mock_run.call_args[0][0]
            assert args[0] == "copilot"
            assert "-p" in args

    @pytest.mark.asyncio
    async def test_modify_code_success(self, copilot_adapter):
        """Test successful code modification."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "Here's the modified code:\n\n```python\nprint('Hello, Python!')\n```",
                "stderr": "",
                "return_code": 0
            }

            result = await copilot_adapter.modify_code(
                "print('Hello, World!')",
                "Change to say Python instead of World",
                language="python"
            )

            assert "modified_code" in result
            assert result["modified_code"] is not None
            assert result["language"] == "python"
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_commit_message_success(self, copilot_adapter):
        """Test successful commit message generation."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            # Mock git diff command
            mock_run.side_effect = [
                {
                    "success": True,
                    "stdout": "diff --git a/test.py b/test.py\n+print('new feature')",
                    "stderr": "",
                    "return_code": 0
                },
                # Mock copilot suggest command
                {
                    "success": True,
                    "stdout": "feat: add new print statement",
                    "stderr": "",
                    "return_code": 0
                }
            ]

            result = await copilot_adapter.generate_commit_message()

            assert "generated_message" in result
            assert result["generated_message"] is not None
            assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_commit_message_no_changes(self, copilot_adapter):
        """Test commit message generation with no staged changes."""
        with patch.object(copilot_adapter, '_run_command') as mock_run:
            mock_run.return_value = {
                "success": True,
                "stdout": "",  # No diff output
                "stderr": "",
                "return_code": 0
            }

            result = await copilot_adapter.generate_commit_message()

            assert "error" in result
            assert "No staged changes found" in result["error"]
            assert result["generated_message"] is None

    def test_parse_copilot_output(self, copilot_adapter):
        """Test parsing of Copilot CLI output."""
        raw_output = """GitHub Copilot CLI
An AI-powered coding assistant
═══════════════════════════════

Here's how you can create a Python function:

def my_function():
    print("Hello, World!")

This function defines a simple greeting."""

        parsed = copilot_adapter._parse_copilot_output(raw_output)
        assert "Here's how you can create a Python function:" in parsed
        assert "def my_function():" in parsed
        # Should not contain header lines
        assert "GitHub Copilot CLI" not in parsed

    def test_extract_code_from_output(self, copilot_adapter):
        """Test code extraction from Copilot output."""
        output_with_code = """Here's the code you requested:

```python
def hello():
    print("Hello, World!")
```

This function prints a greeting."""

        extracted = copilot_adapter._extract_code_from_output(output_with_code)
        assert "def hello():" in extracted
        assert "print(\"Hello, World!\")" in extracted

    def test_extract_code_from_output_no_blocks(self, copilot_adapter):
        """Test code extraction when no code blocks are present."""
        output_without_code = "This is just a text response without code blocks."

        extracted = copilot_adapter._extract_code_from_output(output_without_code)
        assert extracted == output_without_code