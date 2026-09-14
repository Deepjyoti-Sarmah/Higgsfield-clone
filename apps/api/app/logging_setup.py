"""Structured logging for both entrypoints, stdlib only.

Job-scoped fields travel on a contextvar, so every line emitted while a step
runs carries them without threading ids through every call. Anything sensitive
is scrubbed at format time, never at the call site.
"""

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

CONTEXT_FIELDS = ("job_id", "step_id", "user_id", "backend", "attempt")
OUTCOME_FIELDS = ("outcome", "generated_by", "duration_ms", "prompt")
PROMPT_LOG_LIMIT = 80

SCRUB_PATTERNS = (
    re.compile(r"([?&](?:X-Amz-Signature|signature|token|key)=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(Bearer\s+)\S+", re.IGNORECASE),
)

_log_context: ContextVar[dict[str, str] | None] = ContextVar("hf_log_context", default=None)


def set_job_context(**fields: str | int) -> None:
    _log_context.set({key: str(value) for key, value in fields.items()})


def clear_job_context() -> None:
    _log_context.set({})


def truncate_prompt(prompt: str | None, limit: int = PROMPT_LOG_LIMIT) -> str | None:
    if prompt is None:
        return None
    if len(prompt) <= limit:
        return prompt
    return prompt[:limit] + "…"


def scrub_line(line: str) -> str:
    for pattern in SCRUB_PATTERNS:
        line = pattern.sub(r"\1REDACTED", line)
    return line


class JobContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in (_log_context.get() or {}).items():
            setattr(record, key, value)
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrub_line(record.getMessage()),
        }
        for key in CONTEXT_FIELDS + OUTCOME_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info is not None and record.exc_info[0] is not None:
            payload["exception"] = scrub_line(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(log_format: str) -> None:
    formatter: logging.Formatter = (
        JsonLogFormatter()
        if log_format == "json"
        else logging.Formatter("%(asctime)s %(name)s %(message)s")
    )
    handler = logging.StreamHandler()
    handler.addFilter(JobContextFilter())
    handler.setFormatter(formatter)
    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
