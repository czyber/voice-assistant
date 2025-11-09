"""
Shared logging utilities for the voice assistant project.

This module centralizes logging configuration so every package can emit
consistent, high-signal telemetry without each contributor copy/pasting
handlers or worrying about duplicate configuration.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)s | run=%(run_id)s | %(name)s:%(lineno)d | %(message)s"
)
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

_RUN_ID = os.getenv("VOICE_ASSISTANT_LOG_RUN_ID") or uuid.uuid4().hex[:8]
_CONFIGURED = False


class _ContextFilter(logging.Filter):
    """Attaches run-scoped metadata to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        record.run_id = _RUN_ID
        return True


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    normalized = str(level).strip().upper()
    return getattr(logging, normalized, logging.INFO)


def setup_logging(level: str | int | None = None) -> None:
    """
    Configure the root logger once.

    Respects VOICE_ASSISTANT_LOG_LEVEL/FORMAT/FILE env vars so teammates can
    tailor the verbosity without touching the codebase.
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    selected_level = level or os.getenv("VOICE_ASSISTANT_LOG_LEVEL", "INFO")
    log_level = _resolve_level(selected_level)
    formatter = logging.Formatter(
        os.getenv("VOICE_ASSISTANT_LOG_FORMAT", DEFAULT_FORMAT),
        os.getenv("VOICE_ASSISTANT_LOG_TIME_FORMAT", DEFAULT_TIME_FORMAT),
    )

    context_filter = _ContextFilter()
    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    handlers.append(stream_handler)

    log_file = os.getenv("VOICE_ASSISTANT_LOG_FILE")
    if log_file:
        file_path = Path(log_file).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    logging.captureWarnings(True)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger with the shared configuration."""

    setup_logging()
    return logging.getLogger(name)


def _format_details(details: dict[str, object] | None) -> str:
    if not details:
        return ""
    serialized = " ".join(f"{key}={value}" for key, value in details.items())
    return f" | {serialized}"


@contextmanager
def log_activity(
    logger: logging.Logger,
    activity: str,
    *,
    details: dict[str, object] | None = None,
) -> Iterator[None]:
    """
    Emit structured start/end logs with execution timing.

    This is intentionally logging-only: exceptions are re-raised untouched so
    runtime behavior stays identical.
    """

    start = time.perf_counter()
    logger.info("START %s%s", activity, _format_details(details))
    try:
        yield
    except Exception:
        logger.exception("FAILED %s%s", activity, _format_details(details))
        raise
    else:
        elapsed = time.perf_counter() - start
        data = dict(details or {})
        data["duration_s"] = f"{elapsed:.3f}"
        logger.info("END %s%s", activity, _format_details(data))


__all__ = ["get_logger", "log_activity", "setup_logging"]
