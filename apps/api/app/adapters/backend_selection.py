from app.adapters.image_model_adapter import ImageModelAdapter
from app.adapters.local_motion_adapter import LocalMotionAdapter
from app.adapters.mock_model_adapter import MockModelAdapter
from app.adapters.modal_adapter import ModalAdapter
from app.adapters.modal_image_adapter import FallbackImageAdapter, ModalImageAdapter
from app.adapters.model_adapter import ModelAdapter
from app.adapters.openrouter_adapter import OpenRouterAdapter
from app.adapters.placeholder_image_adapter import PlaceholderImageAdapter
from app.settings import Settings

PAID_VIDEO_BACKENDS = ("modal", "openrouter")
PLACEHOLDER_IMAGE_NAME = "placeholder"


def select_model_adapter(settings: Settings) -> ModelAdapter:
    if settings.generation_backend == "mock":
        return MockModelAdapter(settings)
    if settings.generation_backend == "modal":
        return ModalAdapter(settings)
    if settings.generation_backend == "openrouter":
        return OpenRouterAdapter(settings)
    return LocalMotionAdapter()


def select_fallback_model_adapter(settings: Settings) -> ModelAdapter | None:
    """A paid backend always has a free local fallback so a visitor still gets a clip."""
    if settings.generation_backend in PAID_VIDEO_BACKENDS:
        return LocalMotionAdapter()
    return None


def select_image_adapter(settings: Settings) -> ImageModelAdapter:
    if settings.image_generation_backend == "modal":
        return FallbackImageAdapter(
            ModalImageAdapter(settings), PlaceholderImageAdapter(PLACEHOLDER_IMAGE_NAME)
        )
    if settings.image_generation_backend == "mock":
        return PlaceholderImageAdapter("mock")
    return PlaceholderImageAdapter(PLACEHOLDER_IMAGE_NAME)
