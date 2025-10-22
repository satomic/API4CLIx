"""Main FastAPI application for API4CLIx."""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from models.requests import ChatRequest, CodeRequest, CommitRequest
from models.responses import (
    ChatResponse, CodeResponse, CommitResponse, HealthResponse
)
from services.assistant_manager import AssistantManager
from utils.logging_config import setup_logging, get_cli_logger

__version__ = "1.0.0"

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
request_logger = get_cli_logger()

# Global variables
assistant_manager: AssistantManager = None
start_time: float = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global assistant_manager, start_time

    # Startup
    logger.info("Starting API4CLIx...")
    start_time = time.time()
    assistant_manager = AssistantManager()
    await assistant_manager.initialize()
    logger.info("API4CLIx started successfully")

    yield

    # Shutdown
    logger.info("Shutting down API4CLIx...")
    await assistant_manager.cleanup()
    logger.info("API4CLIx shut down complete")


# Create FastAPI app
app = FastAPI(
    title="API4CLIx",
    description="Unified REST API layer for AI programming assistant CLI tools",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_assistant_manager() -> AssistantManager:
    """Dependency to get the assistant manager."""
    if assistant_manager is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return assistant_manager


@app.get("/health", response_model=HealthResponse)
async def health_check(manager: AssistantManager = Depends(get_assistant_manager)):
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        available_assistants=manager.get_available_assistants(),
        uptime=time.time() - start_time if start_time else 0
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    manager: AssistantManager = Depends(get_assistant_manager)
):
    """
    Send a message to an AI programming assistant.

    This endpoint allows you to have a conversation with various AI assistants
    like Copilot CLI, Claude Code, etc.
    """
    # Log the incoming request
    request_logger.info(f"=== EXTERNAL REQUEST START ===")
    request_logger.info(f"Endpoint: POST /chat")
    request_logger.info(f"Assistant Type: {request.assistant_type}")
    request_logger.info(f"Model: {request.model}")
    request_logger.info(f"Message: {request.message}")
    if request.context:
        request_logger.info(f"Context: {request.context}")
    if request.parameters:
        request_logger.info(f"Parameters: {request.parameters}")

    try:
        logger.info(f"Chat request for {request.assistant_type}: {request.message[:100]}...")

        response = await manager.chat(
            assistant_type=request.assistant_type,
            message=request.message,
            context=request.context,
            model=request.model,
            **request.parameters
        )

        result = ChatResponse(
            success=True,
            response=response.get("response"),
            assistant_type=request.assistant_type,
            context_id=response.get("context_id"),
            metadata=response.get("metadata", {})
        )

        # Log the response
        request_logger.info(f"Response Success: {result.success}")
        request_logger.info(f"Response Length: {len(result.response) if result.response else 0} characters")
        request_logger.info(f"=== EXTERNAL REQUEST END ===")

        return result

    except ValueError as e:
        request_logger.error(f"Invalid assistant type: {e}")
        request_logger.info(f"=== EXTERNAL REQUEST END (ERROR) ===")
        logger.error(f"Invalid assistant type: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        request_logger.error(f"Chat error: {e}")
        request_logger.info(f"=== EXTERNAL REQUEST END (ERROR) ===")
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/code/explain", response_model=CodeResponse)
async def explain_code(
    request: CodeRequest,
    manager: AssistantManager = Depends(get_assistant_manager)
):
    """
    Ask an AI assistant to explain code.

    Provide code and get a detailed explanation of what it does,
    how it works, and any potential improvements.
    """
    # Log the incoming request
    request_logger.info(f"=== EXTERNAL REQUEST START ===")
    request_logger.info(f"Endpoint: POST /code/explain")
    request_logger.info(f"Assistant Type: {request.assistant_type}")
    request_logger.info(f"Language: {request.language}")
    request_logger.info(f"Code:\n{request.code}")
    if request.message:
        request_logger.info(f"Message: {request.message}")

    try:
        logger.info(f"Code explanation request for {request.assistant_type}")

        response = await manager.explain_code(
            assistant_type=request.assistant_type,
            code=request.code,
            language=request.language,
            message=request.message,
            model=request.model
        )

        result = CodeResponse(
            success=True,
            original_code=request.code,
            explanation=response.get("explanation"),
            suggestions=response.get("suggestions", []),
            language=response.get("language", request.language)
        )

        # Log the response
        request_logger.info(f"Response Success: {result.success}")
        request_logger.info(f"Explanation Length: {len(result.explanation) if result.explanation else 0} characters")
        request_logger.info(f"=== EXTERNAL REQUEST END ===")

        return result

    except ValueError as e:
        request_logger.error(f"Invalid request: {e}")
        request_logger.info(f"=== EXTERNAL REQUEST END (ERROR) ===")
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        request_logger.error(f"Code explanation error: {e}")
        request_logger.info(f"=== EXTERNAL REQUEST END (ERROR) ===")
        logger.error(f"Code explanation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/code/modify", response_model=CodeResponse)
async def modify_code(
    request: CodeRequest,
    manager: AssistantManager = Depends(get_assistant_manager)
):
    """
    Ask an AI assistant to modify code based on instructions.

    Provide code and modification instructions to get improved or
    refactored code.
    """
    try:
        logger.info(f"Code modification request for {request.assistant_type}")

        if not request.message:
            raise ValueError("Modification instructions are required")

        response = await manager.modify_code(
            assistant_type=request.assistant_type,
            code=request.code,
            instruction=request.message,
            language=request.language,
            model=request.model
        )

        return CodeResponse(
            success=True,
            original_code=request.code,
            modified_code=response.get("modified_code"),
            explanation=response.get("explanation"),
            suggestions=response.get("suggestions", []),
            language=response.get("language", request.language)
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Code modification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/git/commit", response_model=CommitResponse)
async def generate_commit(
    request: CommitRequest,
    manager: AssistantManager = Depends(get_assistant_manager)
):
    """
    Generate and optionally create a git commit with AI assistance.

    The AI assistant will analyze staged changes and generate an appropriate
    commit message, and optionally commit the changes.
    """
    try:
        logger.info(f"Commit generation request for {request.assistant_type}")

        response = await manager.generate_commit(
            assistant_type=request.assistant_type,
            files=request.files,
            message=request.message,
            model=request.model
        )

        return CommitResponse(
            success=True,
            commit_hash=response.get("commit_hash"),
            generated_message=response.get("generated_message"),
            files_committed=response.get("files_committed", [])
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Commit generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/assistants")
async def list_assistants(manager: AssistantManager = Depends(get_assistant_manager)):
    """List all available AI assistants and their status."""
    assistants = await manager.get_assistant_status()
    return {"assistants": assistants}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )