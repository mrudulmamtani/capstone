"""Structured logging setup using structlog.

Every log line is a JSON object in production and a nicely coloured line in
development. Log records carry a ``request_id`` contextvar when available so
traces can be correlated across the API, the worker, and the vision pipeline.
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

from app.core.config import settings

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str | None) -> None:
    _request_id_ctx.set(value)


def _add_request_id(_, __, event_dict):
    rid = _request_id_ctx.get()
    if rid:
        event_dict.setdefault("request_id", rid)
    return event_dict


def configure_logging() -> None:
    """Configure the root logger and structlog processors."""
    level = getattr(logging, settings.app_log_level.upper(), logging.INFO)

    # Silence noisy libraries unless we're debugging.
    for name in ("uvicorn.access", "uvicorn.error", "ultralytics", "mediapipe"):
        logging.getLogger(name).setLevel(max(level, logging.INFO))

    shared_processors: list = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        _add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
