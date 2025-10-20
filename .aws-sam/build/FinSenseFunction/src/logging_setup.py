"""
Structured logging setup for Lambda & local dev.
Produces JSON logs compatible with CloudWatch Insights.
"""

from __future__ import annotations
import logging
import os
import sys
import structlog


def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Standard logging -> structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level, logging.INFO),
    )

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

    return structlog.get_logger().bind(service="FinSense", env=os.getenv("ENV", "dev"))
