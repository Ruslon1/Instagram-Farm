import logging
import sys
import os
from typing import Any, Dict
from datetime import datetime
import structlog
from config.settings import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer() if settings.is_development() else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Create formatters
    if settings.is_development():
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler
    log_file = os.path.join(settings.logs_dir, "app.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Application logger
    app_logger = logging.getLogger("instagram_bot")
    app_logger.setLevel(log_level)

    app_logger.info(
        "Logging configured",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": log_level
        }
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name or "instagram_bot")


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func_name: str, **kwargs) -> Dict[str, Any]:
    """Helper to log function calls with parameters."""
    return {
        "function": func_name,
        "parameters": {k: v for k, v in kwargs.items() if not k.startswith('_')},
        "timestamp": datetime.utcnow().isoformat()
    }


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log an error with context."""
    logger = get_logger("error")
    logger.error(
        "Exception occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )


def log_task_progress(task_id: str, progress: int, message: str, **kwargs) -> None:
    """Log task progress."""
    logger = get_logger("task")
    logger.info(
        "Task progress update",
        task_id=task_id,
        progress=progress,
        message=message,
        **kwargs
    )


def log_api_request(method: str, path: str, user_id: str = None, **kwargs) -> None:
    """Log API request."""
    logger = get_logger("api")
    logger.info(
        "API request",
        method=method,
        path=path,
        user_id=user_id,
        **kwargs
    )