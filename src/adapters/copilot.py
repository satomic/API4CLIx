"""GitHub Copilot CLI adapter for API4CLIx."""

import json
import os
import re
from typing import Dict, Any, Optional, List
import logging

from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class CopilotAdapter(BaseAdapter):
    """Adapter for GitHub Copilot CLI."""

    def __init__(self):
        super().__init__("GitHub Copilot CLI", "copilot")

    async def is_available(self) -> bool:
        """Check if Copilot CLI is available."""
        if self._available is not None:
            return self._available

        try:
            # Check if copilot CLI is available (disable streaming for quick check)
            result = await self._run_command(["copilot", "--version"], timeout=5, stream_output=False)
            self._available = result["success"]

            if not self._available:
                logger.warning("GitHub Copilot CLI not available")

        except Exception as e:
            logger.warning(f"Error checking Copilot CLI availability: {e}")
            self._available = False

        return self._available

    async def chat(self, message: str, context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Send a chat message to GitHub Copilot CLI.

        Args:
            message: The message to send
            context: Optional context (can be used to provide more context)
            **kwargs: Additional parameters (including model and workspace)

        Returns:
            Dict containing the response and metadata
        """
        try:
            # Build the command with non-interactive mode
            cmd = ["copilot"]

            # Add model parameter if provided
            model = kwargs.get('model')
            if model:
                cmd.extend(["--model", model])

            # Add the prompt and other options
            if context:
                full_message = f"Context: {context}\n\nQuestion: {message}"
                cmd.extend(["-p", full_message, "--allow-all-tools"])
            else:
                cmd.extend(["-p", message, "--allow-all-tools"])

            # Get workspace directory
            workspace = self._get_workspace_dir(kwargs.get('workspace'))
            
            result = await self._run_command(cmd, timeout=3600, cwd=workspace)

            if not result["success"]:
                return {
                    "response": None,
                    "error": result["stderr"] or "Failed to get response from Copilot CLI",
                    "metadata": {"command": " ".join(cmd)}
                }

            # Parse the output to extract the response
            response_text = self._parse_copilot_output(result["stdout"])

            return {
                "response": response_text,
                "metadata": {
                    "command": " ".join(cmd),
                    "raw_output": result["stdout"]
                }
            }

        except Exception as e:
            logger.error(f"Error in Copilot chat: {e}")
            return {
                "response": None,
                "error": str(e),
                "metadata": {}
            }

    async def explain_code(self, code: str, language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Ask Copilot CLI to explain code.

        Args:
            code: The code to explain
            language: Programming language (optional)
            **kwargs: Additional parameters (including model and workspace)

        Returns:
            Dict containing explanation and metadata
        """
        try:
            # Create a prompt for code explanation
            language_hint = f" (this is {language} code)" if language else ""
            prompt = f"Please explain this code{language_hint}:\n\n```\n{code}\n```"

            cmd = ["copilot"]

            # Add model parameter if provided
            model = kwargs.get('model')
            if model:
                cmd.extend(["--model", model])

            cmd.extend(["-p", prompt, "--allow-all-tools"])

            # Get workspace directory
            workspace = self._get_workspace_dir(kwargs.get('workspace'))

            result = await self._run_command(cmd, timeout=60, cwd=workspace)

            if not result["success"]:
                return {
                    "explanation": None,
                    "error": result["stderr"] or "Failed to explain code with Copilot CLI",
                    "metadata": {"command": " ".join(cmd)}
                }

            explanation = self._parse_copilot_output(result["stdout"])

            return {
                "explanation": explanation,
                "language": language,
                "metadata": {
                    "command": " ".join(cmd),
                    "raw_output": result["stdout"]
                }
            }

        except Exception as e:
            logger.error(f"Error in Copilot explain: {e}")
            return {
                "explanation": None,
                "error": str(e),
                "metadata": {}
            }

    async def modify_code(
        self,
        code: str,
        instruction: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ask Copilot CLI to modify code based on instructions.

        Args:
            code: The code to modify
            instruction: Instructions for modification
            language: Programming language (optional)
            **kwargs: Additional parameters (including model and workspace)

        Returns:
            Dict containing modified code and metadata
        """
        try:
            # Create a prompt for code modification
            language_hint = f" (this is {language} code)" if language else ""
            prompt = f"Please {instruction} for this code{language_hint}:\n\n```\n{code}\n```\n\nPlease provide the modified code."

            cmd = ["copilot"]

            # Add model parameter if provided
            model = kwargs.get('model')
            if model:
                cmd.extend(["--model", model])

            cmd.extend(["-p", prompt, "--allow-all-tools"])

            # Get workspace directory
            workspace = self._get_workspace_dir(kwargs.get('workspace'))

            result = await self._run_command(cmd, timeout=60, cwd=workspace)

            if not result["success"]:
                return {
                    "modified_code": None,
                    "error": result["stderr"] or "Failed to modify code with Copilot CLI",
                    "metadata": {"command": " ".join(cmd)}
                }

            # Extract the modified code from the response
            response_text = self._parse_copilot_output(result["stdout"])
            modified_code = self._extract_code_from_output(response_text)

            return {
                "modified_code": modified_code,
                "explanation": "Code modified using GitHub Copilot CLI",
                "language": language,
                "metadata": {
                    "command": " ".join(cmd),
                    "raw_output": result["stdout"]
                }
            }

        except Exception as e:
            logger.error(f"Error in Copilot modify: {e}")
            return {
                "modified_code": None,
                "error": str(e),
                "metadata": {}
            }

    async def generate_commit_message(self, files: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a commit message using Copilot CLI.

        This is a custom method specific to Copilot adapter.

        Args:
            files: Optional list of files to analyze
            **kwargs: Additional parameters (including workspace)

        Returns:
            Dict containing generated commit message and metadata
        """
        try:
            # Get workspace directory
            workspace = self._get_workspace_dir(kwargs.get('workspace'))
            
            # Use git diff to get changes (disable streaming for quick data fetch)
            diff_cmd = ["git", "diff", "--staged"]
            if files:
                diff_cmd.extend(files)

            diff_result = await self._run_command(diff_cmd, timeout=30, cwd=workspace, stream_output=False)

            if not diff_result["success"] or not diff_result["stdout"].strip():
                return {
                    "generated_message": None,
                    "error": "No staged changes found",
                    "metadata": {}
                }

            # Ask Copilot to generate a commit message
            prompt = f"Please generate a concise and descriptive git commit message for these changes:\n\n{diff_result['stdout']}\n\nReturn only the commit message, nothing else."
            cmd = ["copilot"]

            # Add model parameter if provided
            model = kwargs.get('model')
            if model:
                cmd.extend(["--model", model])
            
            cmd.extend(["-p", prompt, "--allow-all-tools"])

            result = await self._run_command(cmd, timeout=60, cwd=workspace)

            if not result["success"]:
                return {
                    "generated_message": None,
                    "error": result["stderr"] or "Failed to generate commit message",
                    "metadata": {"command": " ".join(cmd)}
                }

            commit_message = self._parse_copilot_output(result["stdout"])

            return {
                "generated_message": commit_message,
                "metadata": {
                    "command": " ".join(cmd),
                    "raw_output": result["stdout"]
                }
            }

        except Exception as e:
            logger.error(f"Error generating commit message: {e}")
            return {
                "generated_message": None,
                "error": str(e),
                "metadata": {}
            }

    def _parse_copilot_output(self, output: str) -> str:
        """
        Parse the output from GitHub Copilot CLI to extract the main response.

        Args:
            output: Raw output from the CLI

        Returns:
            Cleaned response text
        """
        lines = output.strip().split('\n')

        # Remove common CLI output patterns
        filtered_lines = []
        skip_patterns = [
            r'^GitHub Copilot CLI',
            r'^An AI-powered coding assistant',
            r'^═+',
            r'^─+',
            r'^\s*$',  # Empty lines at the beginning
            r'^Loading',
            r'^Thinking',
            r'^Processing'
        ]

        start_content = False
        for line in lines:
            # Skip header lines until we find actual content
            if not start_content:
                if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                    continue
                start_content = True

            if start_content and line.strip():
                filtered_lines.append(line)

        # Join and clean up
        response = '\n'.join(filtered_lines).strip()

        # If no meaningful content found, return the original output
        return response if response else output.strip()

    def _extract_code_from_output(self, output: str) -> str:
        """
        Extract code blocks from Copilot CLI output.

        Args:
            output: Raw output from the CLI

        Returns:
            Extracted code or the cleaned output if no code blocks found
        """
        # Look for code blocks (markdown-style or other common formats)
        code_block_patterns = [
            r'```(?:\w+)?\n(.*?)\n```',  # Markdown code blocks
            r'`([^`\n]+)`',  # Inline code (single line only)
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, output, re.DOTALL)
            if matches:
                # Return the first and longest match
                return max(matches, key=len) if matches else output

        # If no code blocks found, return parsed output
        return self._parse_copilot_output(output)

    def _get_workspace_dir(self, workspace: Optional[str] = None) -> str:
        """
        Get the workspace directory for running commands.
        
        Args:
            workspace: Optional workspace path provided by user
            
        Returns:
            Workspace directory path (either provided workspace or tmp folder)
        """
        if workspace:
            # Use the provided workspace
            return workspace
        else:
            # Default to current working directory's tmp folder
            cwd = os.getcwd()
            tmp_dir = os.path.join(cwd, "tmp")
            
            # Create tmp directory if it doesn't exist
            os.makedirs(tmp_dir, exist_ok=True)
            
            return tmp_dir