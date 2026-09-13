from app.adapters.local_motion_adapter import LocalMotionAdapter
from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.modal_adapter import ModalAdapter
from app.adapters.model_adapter import ModelAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.settings import Settings


def select_model_adapter(settings: Settings) -> ModelAdapter:
    if settings.generation_backend == "mock":
        return MockModelAdapter(settings)
    if settings.generation_backend == "modal":
        return ModalAdapter(settings)
    if settings.generation_backend == "openrouter":
        return OpenRouterAdapter(settings)
    return LocalMotionAdapter()
