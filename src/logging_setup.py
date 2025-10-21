"""
Structured logging setup for Lambda & local development.

PURPOSE:
- Configure consistent JSON-formatted logs for both AWS Lambda and local runs.
- Logs are structured so they can be easily queried in CloudWatch Insights.

CONTEXT:
- Used by the FinSense agent’s backend and Lambda entrypoint.
- Relies on structlog to enrich logs with metadata and timestamps.

CREDITS:
- Original work — no external code reuse.
NOTE:
- Functionality unchanged; comments/docstrings only.
"""

from __future__ import annotations
import logging
import os
import sys
import structlog


def configure_logging():
    """
    Configure structured JSON logging for the current environment.

    returns:
    - structlog.BoundLogger – pre-configured logger instance bound with service metadata.

    behaviour:
    - Reads log level from LOG_LEVEL environment variable (default = INFO).
    - Directs logs to stdout so AWS Lambda automatically captures them.
    - Formats logs as JSON to make them easily parsable by CloudWatch Insights.

    example log entry:
    {
      "event": "response.success",
      "level": "info",
      "timestamp": "2025-10-21T13:00:00Z",
      "service": "FinSense",
      "env": "dev",
      "latency_ms": 123.4
    }
    """
    # Read desired log level; default to INFO for safety.
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure Python's built-in logging to forward to stdout.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level, logging.INFO),
    )

    # Configure structlog processors:
    # - Add timestamps, log level, and structured exception info.
    # - Render logs as JSON instead of plain text for better observability.
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Return a pre-bound logger with service and environment context.
    return structlog.get_logger().bind(service="FinSense", env=os.getenv("ENV", "dev"))
