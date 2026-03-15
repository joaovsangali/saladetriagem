"""Structured JSON logging configuration.

Usage:
    from app.logging_config import configure_logging
    configure_logging(app)

JSON log format:
    {
        "timestamp": "2026-03-15T10:30:00.000Z",
        "level": "INFO",
        "logger": "app.intake.routes",
        "message": "...",
        "request_id": "abc123"
    }
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include any extra fields attached to the record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
            }:
                try:
                    json.dumps(value)  # only include JSON-serialisable extras
                    log_obj[key] = value
                except (TypeError, ValueError):
                    pass

        return json.dumps(log_obj, ensure_ascii=False)


def configure_logging(app) -> None:
    """Configure structured JSON logging for *app* in production mode."""
    if app.debug:
        return  # Keep human-readable logs during development

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate output
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.setLevel(logging.INFO)

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    app.logger.info("Structured JSON logging configured")
