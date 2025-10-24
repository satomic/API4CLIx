"""Assistant manager for handling multiple AI programming assistants."""

from typing import Dict, Any, List, Optional
import logging

from adapters.base import BaseAdapter
from adapters.copilot import CopilotAdapter

logger = logging.getLogger(__name__)


class AssistantManager:
    """Manages multiple AI programming assistant adapters."""

    def __init__(self):
        """Initialize the assistant manager."""
        self.adapters: Dict[str, BaseAdapter] = {}
        self.available_adapters: Dict[str, BaseAdapter] = {}

    async def initialize(self):
        """Initialize all available adapters."""
        logger.info("Initializing AI assistant adapters...")

        # Register all adapters
        self.adapters = {
            "copilot": CopilotAdapter(),
            # Add more adapters here as they are implemented
            # "claude": ClaudeAdapter(),
            # "codex": CodexAdapter(),
        }

        # Check availability of each adapter
        for name, adapter in self.adapters.items():
            try:
                is_available = await adapter.is_available()
                if is_available:
                    self.available_adapters[name] = adapter
                    logger.info(f"✓ {adapter.name} is available")
                else:
                    logger.warning(f"✗ {adapter.name} is not available")
            except Exception as e:
                logger.error(f"Error checking {adapter.name} availability: {e}")

        if not self.available_adapters:
            logger.warning("No AI assistants are available!")
        else:
            logger.info(f"Initialized {len(self.available_adapters)} AI assistants")

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up assistant manager...")
        # Add any cleanup logic here if needed

    def get_available_assistants(self) -> List[str]:
        """Get list of available assistant names."""
        return list(self.available_adapters.keys())

    async def get_assistant_status(self) -> Dict[str, Any]:
        """Get detailed status of all assistants."""
        status = {}
        for name, adapter in self.adapters.items():
            is_available = name in self.available_adapters
            status[name] = {
                "name": adapter.name,
                "available": is_available,
                "command": adapter.command
            }
        return status

    def _get_adapter(self, assistant_type: str) -> BaseAdapter:
        """
        Get adapter for the specified assistant type.

        Args:
            assistant_type: Type of assistant (e.g., "copilot", "claude")

        Returns:
            BaseAdapter instance

        Raises:
            ValueError: If assistant type is not available
        """
        if assistant_type not in self.available_adapters:
            available = ", ".join(self.available_adapters.keys())
            raise ValueError(
                f"Assistant '{assistant_type}' is not available. "
                f"Available assistants: {available}"
            )
        return self.available_adapters[assistant_type]

    async def chat(
        self,
        assistant_type: str,
        message: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat message to the specified assistant.

        Args:
            assistant_type: Type of assistant to use
            message: Message to send
            context: Optional context from previous conversations
            **kwargs: Additional parameters for the assistant

        Returns:
            Dict containing response and metadata

        Raises:
            ValueError: If assistant type is not available
        """
        adapter = self._get_adapter(assistant_type)
        logger.debug(f"Sending chat message to {adapter.name}")

        result = await adapter.chat(message=message, context=context, **kwargs)

        if "error" in result:
            logger.error(f"Chat error from {adapter.name}: {result['error']}")

        return result

    async def explain_code(
        self,
        assistant_type: str,
        code: str,
        language: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ask the specified assistant to explain code.

        Args:
            assistant_type: Type of assistant to use
            code: Code to explain
            language: Programming language (optional)
            message: Additional context or instructions
            **kwargs: Additional parameters for the assistant

        Returns:
            Dict containing explanation and metadata

        Raises:
            ValueError: If assistant type is not available
        """
        adapter = self._get_adapter(assistant_type)
        logger.debug(f"Requesting code explanation from {adapter.name}")

        result = await adapter.explain_code(
            code=code,
            language=language,
            message=message,
            **kwargs
        )

        if "error" in result:
            logger.error(f"Code explanation error from {adapter.name}: {result['error']}")

        return result

    async def modify_code(
        self,
        assistant_type: str,
        code: str,
        instruction: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ask the specified assistant to modify code.

        Args:
            assistant_type: Type of assistant to use
            code: Code to modify
            instruction: Modification instructions
            language: Programming language (optional)
            **kwargs: Additional parameters for the assistant

        Returns:
            Dict containing modified code and metadata

        Raises:
            ValueError: If assistant type is not available
        """
        adapter = self._get_adapter(assistant_type)
        logger.debug(f"Requesting code modification from {adapter.name}")

        result = await adapter.modify_code(
            code=code,
            instruction=instruction,
            language=language,
            **kwargs
        )

        if "error" in result:
            logger.error(f"Code modification error from {adapter.name}: {result['error']}")

        return result

    async def generate_commit(
        self,
        assistant_type: str,
        files: Optional[List[str]] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a commit message and optionally commit changes.

        Args:
            assistant_type: Type of assistant to use
            files: Optional list of files to commit
            message: Optional predefined commit message
            **kwargs: Additional parameters for the assistant

        Returns:
            Dict containing commit information and metadata

        Raises:
            ValueError: If assistant type is not available
        """
        adapter = self._get_adapter(assistant_type)
        logger.debug(f"Requesting commit generation from {adapter.name}")

        if message:
            # If message is provided, use it directly
            # This is a simple implementation - could be enhanced to actually commit
            return {
                "generated_message": message,
                "commit_hash": None,  # Would need actual git commit implementation
                "files_committed": files or [],
                "metadata": {"provided_message": True}
            }

        # For Copilot adapter, use the specific method
        if hasattr(adapter, 'generate_commit_message'):
            result = await adapter.generate_commit_message(files=files, **kwargs)
        else:
            # Fallback: use chat to generate commit message
            # Get git diff and ask for commit message
            import subprocess
            try:
                diff_result = subprocess.run(
                    ["git", "diff", "--staged"] + (files or []),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if diff_result.returncode == 0 and diff_result.stdout.strip():
                    diff_text = diff_result.stdout
                    commit_query = f"Generate a concise git commit message for these changes:\\n{diff_text}"
                    result = await adapter.chat(message=commit_query)
                    result["generated_message"] = result.get("response")
                else:
                    result = {
                        "generated_message": None,
                        "error": "No staged changes found",
                        "metadata": {}
                    }
            except Exception as e:
                result = {
                    "generated_message": None,
                    "error": f"Error getting git diff: {e}",
                    "metadata": {}
                }

        if "error" in result:
            logger.error(f"Commit generation error from {adapter.name}: {result['error']}")

        return result