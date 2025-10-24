"""Base adapter class for AI programming assistants."""

import asyncio
import subprocess
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Base class for AI programming assistant adapters."""

    def __init__(self, name: str, command: str):
        """
        Initialize the adapter.

        Args:
            name: Human-readable name of the assistant
            command: Base CLI command to execute
        """
        self.name = name
        self.command = command
        self._available = None

    @abstractmethod
    async def chat(self, message: str, context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Send a chat message to the AI assistant.

        Args:
            message: The message to send
            context: Optional context from previous conversations
            **kwargs: Additional parameters specific to the assistant

        Returns:
            Dict containing the response and metadata
        """
        pass

    @abstractmethod
    async def explain_code(self, code: str, language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Ask the AI assistant to explain code.

        Args:
            code: The code to explain
            language: Programming language (optional)
            **kwargs: Additional parameters

        Returns:
            Dict containing explanation and metadata
        """
        pass

    @abstractmethod
    async def modify_code(self, code: str, instruction: str, language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Ask the AI assistant to modify code based on instructions.

        Args:
            code: The code to modify
            instruction: Instructions for modification
            language: Programming language (optional)
            **kwargs: Additional parameters

        Returns:
            Dict containing modified code and metadata
        """
        pass

    async def is_available(self) -> bool:
        """
        Check if the CLI tool is available on the system.

        Returns:
            True if available, False otherwise
        """
        if self._available is not None:
            return self._available

        try:
            # Try to run the base command with --help or --version
            result = await self._run_command([self.command, "--help"], timeout=5)
            self._available = result["success"]
        except Exception as e:
            logger.warning(f"{self.name} CLI not available: {e}")
            self._available = False

        return self._available

    async def _run_command(
        self,
        cmd: List[str],
        input_text: Optional[str] = None,
        timeout: int = 30,
        cwd: Optional[str] = None,
        stream_output: bool = True
    ) -> Dict[str, Any]:
        """
        Run a command asynchronously with real-time output streaming.

        Args:
            cmd: Command and arguments as a list
            input_text: Optional input to send to the command
            timeout: Timeout in seconds
            cwd: Working directory
            stream_output: Whether to stream output in real-time (default: True)

        Returns:
            Dict with success, stdout, stderr, and return_code
        """
        from utils.logging_config import get_cli_logger
        cli_logger = get_cli_logger()

        # Log the command execution attempt
        cmd_str = self._format_command_for_logging(cmd)
        cli_logger.info(f"=== CLI COMMAND EXECUTION START ===")
        cli_logger.info(f"Tool: {self.name} ({self.command})")
        cli_logger.info(f"Command: {cmd_str}")
        if input_text:
            cli_logger.info(f"Input: {input_text}")
        if cwd:
            cli_logger.info(f"Working Directory: {cwd}")

        try:
            logger.debug(f"Running command: {cmd_str}")

            # Ensure environment variables are passed to subprocess
            env = os.environ.copy()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE if input_text else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env
            )

            # Send input if provided
            if input_text:
                process.stdin.write(input_text.encode())
                process.stdin.close()

            # Stream output in real-time if enabled
            if stream_output:
                stdout_data, stderr_data = await self._stream_output(
                    process, timeout, cli_logger
                )
            else:
                # Fall back to wait for completion
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    stdout_data = stdout_bytes.decode('utf-8', errors='replace')
                    stderr_data = stderr_bytes.decode('utf-8', errors='replace')
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

                    result = {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Command timed out after {timeout} seconds",
                        "return_code": -1
                    }

                    # Log timeout
                    cli_logger.error(f"Command timed out after {timeout} seconds")
                    cli_logger.info(f"=== CLI COMMAND EXECUTION END (TIMEOUT) ===")
                    return result

            return_code = process.returncode

            result = {
                "success": return_code == 0,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "return_code": return_code
            }

            # Log the execution result
            cli_logger.info(f"Return Code: {result['return_code']}")
            cli_logger.info(f"Success: {result['success']}")
            if not stream_output:  # Only log full output if not already streamed
                if result['stdout']:
                    cli_logger.info(f"STDOUT:\n{result['stdout']}")
                if result['stderr']:
                    cli_logger.info(f"STDERR:\n{result['stderr']}")
            cli_logger.info(f"=== CLI COMMAND EXECUTION END ===")

            return result

        except Exception as e:
            result = {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1
            }

            # Log the exception
            logger.error(f"Error running command {cmd_str}: {e}")
            cli_logger.error(f"Exception during command execution: {str(e)}")
            cli_logger.info(f"=== CLI COMMAND EXECUTION END (FAILED) ===")

            return result

    async def _stream_output(
        self,
        process: asyncio.subprocess.Process,
        timeout: int,
        cli_logger
    ) -> tuple[str, str]:
        """
        Stream output from a process in real-time.

        Args:
            process: The subprocess to stream from
            timeout: Timeout in seconds
            cli_logger: Logger for CLI output

        Returns:
            Tuple of (stdout_data, stderr_data)
        """
        stdout_lines = []
        stderr_lines = []
        
        async def read_stream(stream, lines_list, prefix):
            """Read from a stream line by line and log in real-time."""
            try:
                while True:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break
                    line = line_bytes.decode('utf-8', errors='replace').rstrip()
                    if line:  # Only log non-empty lines
                        cli_logger.info(f"{prefix} {line}")
                        # Also print to console for immediate feedback
                        # print(f"{prefix} {line}", flush=True)
                    lines_list.append(line)
            except Exception as e:
                logger.error(f"Error reading {prefix}: {e}")

        try:
            # Create tasks to read both stdout and stderr concurrently
            stdout_task = asyncio.create_task(
                read_stream(process.stdout, stdout_lines, "[OUTPUT]")
            )
            stderr_task = asyncio.create_task(
                read_stream(process.stderr, stderr_lines, "[ERROR]")
            )

            # Wait for both streams to finish or timeout
            await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task),
                timeout=timeout
            )
            
            # Wait for process to complete
            await process.wait()

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            cli_logger.error(f"Command timed out after {timeout} seconds")
            stderr_lines.append(f"Command timed out after {timeout} seconds")

        return '\n'.join(stdout_lines), '\n'.join(stderr_lines)

    def _format_command_for_logging(self, cmd: List[str]) -> str:
        """
        Format command for logging with proper quoting for readability.

        Args:
            cmd: Command and arguments as a list

        Returns:
            Formatted command string with proper quoting
        """
        formatted_parts = []
        i = 0
        while i < len(cmd):
            part = cmd[i]

            # If this is a -p flag followed by a prompt, quote the prompt
            if part == "-p" and i + 1 < len(cmd):
                formatted_parts.append(part)
                i += 1
                prompt = cmd[i]
                # Add quotes around the prompt for better readability
                formatted_parts.append(f'"{prompt}"')
            else:
                # For other parts, add quotes if they contain spaces
                if ' ' in part:
                    formatted_parts.append(f'"{part}"')
                else:
                    formatted_parts.append(part)
            i += 1

        return ' '.join(formatted_parts)