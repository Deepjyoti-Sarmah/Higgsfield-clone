from app.adapters.model_adapter import (
    BackendNotConfiguredError,
    GenerationError,
    GenerationRequest,
    GenerationResult,
)
from app.settings import Settings


class OpenRouterAdapter:
    name = "openrouter"

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.openrouter_api_key

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        if not self._api_key:
            raise BackendNotConfiguredError("openrouter backend not configured: set OPENROUTER_API_KEY")
        raise GenerationError("openrouter backend not implemented yet")
