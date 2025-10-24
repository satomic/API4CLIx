"""Request models for API endpoints."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    """Request model for chat/conversation endpoints."""

    message: str = Field(..., description="The message to send to the AI assistant")
    context: Optional[str] = Field(None, description="Additional context or previous conversation")
    assistant_type: str = Field("copilot", description="Type of AI assistant to use (copilot, claude, codex)")
    model: Optional[str] = Field(None, description="Model to use with the assistant")
    workspace: Optional[str] = Field(None, description="Working directory for the assistant (defaults to tmp folder if not provided)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters for the assistant")

    @model_validator(mode='after')
    def set_default_model(self):
        """Set default model based on assistant_type if model is not provided."""
        if self.model is None and self.assistant_type == "copilot":
            self.model = "claude-haiku-4.5"
        return self


class CodeRequest(BaseModel):
    """Request model for code-related operations."""

    code: str = Field(..., description="The code to process")
    operation: str = Field(..., description="Operation to perform (explain, modify, refactor, etc.)")
    message: Optional[str] = Field(None, description="Additional instructions")
    language: Optional[str] = Field(None, description="Programming language")
    assistant_type: str = Field("copilot", description="Type of AI assistant to use")
    model: Optional[str] = Field(None, description="Model to use with the assistant")
    workspace: Optional[str] = Field(None, description="Working directory for the assistant (defaults to tmp folder if not provided)")

    @model_validator(mode='after')
    def set_default_model(self):
        """Set default model based on assistant_type if model is not provided."""
        if self.model is None and self.assistant_type == "copilot":
            self.model = "claude-haiku-4.5"
        return self


class CommitRequest(BaseModel):
    """Request model for commit operations."""

    files: Optional[list[str]] = Field(None, description="List of files to commit")
    message: Optional[str] = Field(None, description="Commit message (if not provided, will be generated)")
    assistant_type: str = Field("copilot", description="Type of AI assistant to use for message generation")
    model: Optional[str] = Field(None, description="Model to use with the assistant")
    workspace: Optional[str] = Field(None, description="Working directory for the assistant (defaults to tmp folder if not provided)")

    @model_validator(mode='after')
    def set_default_model(self):
        """Set default model based on assistant_type if model is not provided."""
        if self.model is None and self.assistant_type == "copilot":
            self.model = "claude-haiku-4.5"
        return self