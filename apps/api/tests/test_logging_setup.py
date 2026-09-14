import json
import logging
from typing import Any

from app.logging_setup import (
    JobContextFilter,
    JsonLogFormatter,
    clear_job_context,
    configure_logging,
    scrub_line,
    set_job_context,
    truncate_prompt,
)
from app.settings import Settings


def _record(message: str = "hello", **extra: Any) -> logging.LogRecord:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_emits_parseable_line() -> None:
    line = JsonLogFormatter().format(_record())
    payload = json.loads(line)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert payload["message"] == "hello"
    assert "timestamp" in payload


def test_context_fields_land_on_the_record() -> None:
    set_job_context(job_id="j1", step_id="s1", user_id="u1", backend="modal", attempt=2)
    try:
        record = _record()
        assert JobContextFilter().filter(record) is True
        payload = json.loads(JsonLogFormatter().format(record))
        assert (payload["job_id"], payload["step_id"], payload["user_id"]) == ("j1", "s1", "u1")
        assert (payload["backend"], payload["attempt"]) == ("modal", "2")
    finally:
        clear_job_context()
    payload = json.loads(JsonLogFormatter().format(_record()))
    assert "job_id" not in payload


def test_outcome_extras_are_included() -> None:
    record = _record("done", outcome="succeeded", generated_by="modal", duration_ms=145200)
    payload = json.loads(JsonLogFormatter().format(record))
    assert (payload["outcome"], payload["generated_by"], payload["duration_ms"]) == (
        "succeeded", "modal", 145200)


def test_truncate_prompt() -> None:
    assert truncate_prompt(None) is None
    assert truncate_prompt("short") == "short"
    assert truncate_prompt("x" * 80) == "x" * 80
    long_prompt = "y" * 200
    assert truncate_prompt(long_prompt) == "y" * 80 + "…"


def test_scrub_line_redacts_signatures_and_bearers() -> None:
    url = "https://r2.dev/k?X-Amz-Algorithm=AWS4&X-Amz-Signature=abc123"
    assert "abc123" not in scrub_line(url)
    assert "REDACTED" in scrub_line(url)
    assert scrub_line("Authorization: Bearer secret-token") == "Authorization: Bearer REDACTED"
    assert scrub_line("plain message") == "plain message"


def test_configure_logging_json_and_text(capsys: Any) -> None:
    root = logging.getLogger()
    saved = list(root.handlers)
    try:
        configure_logging("json")
        logging.getLogger("t-json").info("structured")
        assert json.loads(capsys.readouterr().err.strip())["message"] == "structured"
        configure_logging("text")
        logging.getLogger("t-text").info("plain")
        assert capsys.readouterr().err.strip().endswith("plain")
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in saved:
            root.addHandler(handler)


def test_effective_log_format() -> None:
    assert Settings(env="local").effective_log_format == "text"
    assert Settings(env="production", session_secret="s3cret").effective_log_format == "json"
    assert Settings(env="local", log_format="json").effective_log_format == "json"
    assert Settings(env="production", session_secret="s3cret",
                    log_format="text").effective_log_format == "text"
