"""Logging configuration for API4CLIx."""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(level: Optional[str] = None, format_style: str = "detailed"):
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Format style ("simple" or "detailed")
    """
    # Determine log level
    if level is None:
        level = "INFO"

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Define format styles
    formats = {
        "simple": "%(levelname)s: %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }

    log_format = formats.get(format_style, formats["detailed"])

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Generate daily log filename
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = logs_dir / f"{today}.log"

    # Create handlers
    handlers = [
        # Console handler
        logging.StreamHandler(sys.stdout),
        # File handler with rotation (10MB max, keep 30 backup files for daily logs)
        RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
    ]

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True  # Force reconfiguration if already configured
    )

    # Set specific levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Create application logger
    logger = logging.getLogger("api4clix")
    logger.info("Logging configured successfully - console and file output enabled")
    logger.info(f"Log files are saved to: {logs_dir.absolute()}")
    logger.info(f"Today's log file: {log_filename}")

    return logger


def get_cli_logger():
    """Get a specialized logger for CLI tool interactions."""
    return logging.getLogger("api4clix.cli")