"""
Structured logging for FreeStack.

Provides JSON logging with correlation IDs, structured fields,
and integration with structlog for rich context.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from .config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    log_config = settings.logging

    # Create log directory
    log_path = Path(log_config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_config.level.upper()),
    )

    # Configure structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_config.file,
        maxBytes=log_config.max_bytes,
        backupCount=log_config.backup_count,
        encoding=log_config.encoding,
    )
    file_handler.setLevel(getattr(logging, log_config.level.upper()))

    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        import contextvars
        correlation_id = contextvars.copy_context().get("correlation_id")
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to current logger."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def log_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra: Any
) -> None:
    """Log HTTP request with structured fields."""
    logger.info(
        "http_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra
    )


def log_error(
    logger: structlog.stdlib.BoundLogger,
    error: Exception,
    **extra: Any
) -> None:
    """Log error with structured fields."""
    logger.error(
        "error",
        error_type=type(error).__name__,
        error_message=str(error),
        **extra
    )


def log_db_query(
    logger: structlog.stdlib.BoundLogger,
    query: str,
    duration_ms: float,
    rows_affected: Optional[int] = None,
    **extra: Any
) -> None:
    """Log database query with structured fields."""
    logger.debug(
        "db_query",
        query=query,
        duration_ms=duration_ms,
        rows_affected=rows_affected,
        **extra
    )


def log_job(
    logger: structlog.stdlib.BoundLogger,
    job_name: str,
    status: str,
    duration_ms: Optional[float] = None,
    **extra: Any
) -> None:
    """Log background job with structured fields."""
    logger.info(
        "job",
        job_name=job_name,
        status=status,
        duration_ms=duration_ms,
        **extra
    )