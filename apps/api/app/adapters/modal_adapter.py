from app.adapters.model_adapter import (
    BackendNotConfiguredError,
    GenerationError,
    GenerationRequest,
    GenerationResult,
)
from app.settings import Settings


class ModalAdapter:
    name = "modal"

    def __init__(self, settings: Settings) -> None:
        self._endpoint_url = settings.modal_endpoint_url

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        if not self._endpoint_url:
            raise BackendNotConfiguredError("modal backend not configured: set MODAL_ENDPOINT_URL")
        raise GenerationError("modal backend not implemented yet")
