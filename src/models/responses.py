"""Response models for API endpoints."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Response message or error description")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ChatResponse(BaseResponse):
    """Response model for chat/conversation endpoints."""

    response: Optional[str] = Field(None, description="AI assistant's response")
    assistant_type: str = Field(..., description="Type of AI assistant used")
    context_id: Optional[str] = Field(None, description="Context ID for conversation continuity")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional response metadata")


class CodeResponse(BaseResponse):
    """Response model for code-related operations."""

    original_code: str = Field(..., description="The original code input")
    modified_code: Optional[str] = Field(None, description="Modified code (if applicable)")
    explanation: Optional[str] = Field(None, description="Code explanation")
    suggestions: Optional[List[str]] = Field(default_factory=list, description="Code improvement suggestions")
    language: Optional[str] = Field(None, description="Detected or specified programming language")


class CommitResponse(BaseResponse):
    """Response model for commit operations."""

    commit_hash: Optional[str] = Field(None, description="Git commit hash (if committed)")
    generated_message: Optional[str] = Field(None, description="Generated commit message")
    files_committed: Optional[List[str]] = Field(default_factory=list, description="List of files committed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    available_assistants: List[str] = Field(..., description="List of available AI assistants")
    uptime: float = Field(..., description="Service uptime in seconds")