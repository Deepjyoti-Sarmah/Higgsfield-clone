from typing import Any, Literal

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    duration_ms: int
    detail: str | dict[str, Any] | None = None


class DeepHealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    duration_ms: int
    checks: dict[str, HealthCheckResponse]
