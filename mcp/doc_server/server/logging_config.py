"""
Logging Configuration - Structured logging with loguru.

All server and build script logging uses loguru with structured context fields.
Logs to stderr (separate from MCP protocol on stdout).
"""

import sys
from typing import Literal

from loguru import logger


def configure_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO") -> None:
    """
    Configure loguru for structured logging to stderr.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Log Format:
        - Timestamp (YYYY-MM-DD HH:mm:ss.SSS)
        - Level (color-coded)
        - Module:function:line
        - Message
        - Structured context fields (key=value)
    """
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level> {extra}",
        level=level,
        serialize=False,  # Human-readable by default; JSON for production
        backtrace=True,
        diagnose=True,
    )
    logger.info("Logging configured", level=level)


# Export logger instance for use throughout codebase
log = logger
