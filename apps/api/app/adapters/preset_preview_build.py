from pathlib import Path

from app.adapters.model_adapter import GenerationRequest

VIDEO_CONTENT_TYPE = "video/mp4"
POSTER_CONTENT_TYPE = "image/jpeg"
PREVIEW_DIR = "previews"


def preview_paths(slug: str) -> tuple[str, str]:
    return f"{PREVIEW_DIR}/{slug}.mp4", f"{PREVIEW_DIR}/{slug}.jpg"


def build_preview_request(slug: str, source: Path, output_dir: Path) -> GenerationRequest:
    return GenerationRequest(
        job_id=None,
        preset_slug=slug,
        prompt=None,
        input_image_path=source,
        input_image_url="",
        work_dir=output_dir / slug,
    )
