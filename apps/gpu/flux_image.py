"""T-017: FLUX.1-schnell text->image on Modal (H100), returned to the API as base64 PNG."""

import base64
import io
import os
import time
from pathlib import Path

import modal
from fastapi import HTTPException, Request

MODEL_ID = "black-forest-labs/FLUX.1-schnell"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 4
LOCAL_OUTPUT_DIR = "build/flux"

gpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "torch==2.8.0",
        "torchvision==0.23.0",
        "transformers",
        "accelerate",
        "sentencepiece",
        "av",
        "boto3",
        "fastapi",
        "git+https://github.com/huggingface/diffusers",
    )
    .env({"HF_HUB_CACHE": "/weights"})
)
weights_volume = modal.Volume.from_name("ltx-weights", create_if_missing=True)
app = modal.App("higgsfield-flux-image", image=gpu_image)


def render_images(prompt: str, width: int, height: int, steps: int, count: int):
    import torch
    from diffusers import FluxPipeline

    started = time.monotonic()
    pipeline = FluxPipeline.from_pretrained(MODEL_ID, dtype=torch.bfloat16)
    pipeline.enable_model_cpu_offload()
    weights_volume.commit()
    loaded = time.monotonic()
    images = pipeline(
        prompt=prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=0.0,
        num_images_per_prompt=count,
        max_sequence_length=256,
    ).images
    generated = time.monotonic()
    return images, round(loaded - started, 1), round(generated - loaded, 1)


def encode_png(image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _positive_int(body: dict, key: str, default: int) -> int:
    value = body.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HTTPException(status_code=422, detail=f"{key} must be a positive integer")
    return value


@app.function(
    gpu="H100",
    timeout=1800,
    volumes={"/weights": weights_volume},
    secrets=[modal.Secret.from_name("huggingface")],
)
def generate_images(
    prompt: str,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    count: int = 1,
) -> dict[str, object]:
    images, load_seconds, generate_seconds = render_images(
        prompt, width, height, steps, count
    )
    return {
        "images_base64": [encode_png(image) for image in images],
        "width": width,
        "height": height,
        "load_seconds": load_seconds,
        "generate_seconds": generate_seconds,
    }


@app.function(
    gpu="H100",
    timeout=1800,
    volumes={"/weights": weights_volume},
    secrets=[
        modal.Secret.from_name("huggingface"),
        modal.Secret.from_name("modal-auth"),
    ],
)
@modal.fastapi_endpoint(method="POST")
async def generate_images_endpoint(request: Request) -> dict[str, object]:
    if (
        request.headers.get("authorization")
        != f"Bearer {os.environ['MODAL_WEBHOOK_SECRET']}"
    ):
        raise HTTPException(status_code=401, detail="unauthorized")
    body = await request.json()
    prompt = body.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise HTTPException(status_code=422, detail="prompt is required")
    count = _positive_int(body, "count", 1)
    if count > 4:
        raise HTTPException(status_code=422, detail="count must be <= 4")
    width = _positive_int(body, "width", DEFAULT_WIDTH)
    height = _positive_int(body, "height", DEFAULT_HEIGHT)
    steps = _positive_int(body, "steps", DEFAULT_STEPS)
    images, load_seconds, generate_seconds = render_images(
        prompt, width, height, steps, count
    )
    return {
        "images_base64": [encode_png(image) for image in images],
        "width": width,
        "height": height,
        "load_seconds": load_seconds,
        "generate_seconds": generate_seconds,
    }


@app.local_entrypoint()
def main(
    prompt: str,
    count: int = 1,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
) -> None:
    result = generate_images.remote(prompt, width, height, steps, count)
    out_dir = Path(LOCAL_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    images = result["images_base64"]
    assert isinstance(images, list)
    for index, encoded in enumerate(images, start=1):
        assert isinstance(encoded, str)
        (out_dir / f"image-{index}.png").write_bytes(base64.b64decode(encoded))
    timings = {
        key: result[key]
        for key in ("width", "height", "load_seconds", "generate_seconds")
    }
    print(f"timings={timings} images={len(images)} dir={out_dir}")
