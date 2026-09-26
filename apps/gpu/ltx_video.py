"""T-011-1: faithful LTX-2.5 image->clip endpoint, model loaded once per container.

Needs the same secrets as `ltx_spike.py`: `huggingface` and `modal-auth`
(the API's MODAL_WEBHOOK_SECRET as the bearer token).
"""

import time
import uuid

import modal
from fastapi import HTTPException, Request

MODEL_ID = "Lightricks/LTX-2.5-Diffusers"
CLIP_FRAMES = 121
CLIP_FPS = 24
SCALEDOWN_WINDOW_SECONDS = 300

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
        "pillow",
        "fastapi",
        "git+https://github.com/huggingface/diffusers",
    )
    .env({"HF_HUB_CACHE": "/weights"})
    .add_local_file("apps/gpu/fit_input.py", "/root/fit_input.py")
)
weights_volume = modal.Volume.from_name("ltx-weights", create_if_missing=True)
app = modal.App("higgsfield-ltx-video", image=gpu_image)


def _check_auth(request: Request) -> None:
    import os

    expected = f"Bearer {os.environ['MODAL_WEBHOOK_SECRET']}"
    if request.headers.get("authorization") != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def _parse_body(body: dict[str, object]) -> tuple[str, str]:
    image_url = body.get("image_url")
    prompt = body.get("prompt", "")
    if not isinstance(image_url, str) or not image_url:
        raise HTTPException(status_code=422, detail="image_url is required")
    if not isinstance(prompt, str) or not prompt.strip():
        raise HTTPException(status_code=422, detail="prompt is required")
    return image_url, prompt


@app.cls(
    gpu="H100",
    timeout=1800,
    scaledown_window=SCALEDOWN_WINDOW_SECONDS,
    volumes={"/weights": weights_volume},
    secrets=[
        modal.Secret.from_name("huggingface"),
        modal.Secret.from_name("modal-auth"),
    ],
)
class LtxVideoService:
    @modal.enter()
    def load_pipeline(self) -> None:
        import torch
        from diffusers import LTX2ImageToVideoPipeline

        self.pipeline = LTX2ImageToVideoPipeline.from_pretrained(MODEL_ID, dtype=torch.bfloat16)
        self.pipeline.enable_model_cpu_offload()
        weights_volume.commit()

    def _render(self, image_url: str, prompt: str, width: int, height: int) -> str:
        from diffusers.pipelines.ltx2.utils import (
            DEFAULT_NEGATIVE_PROMPT,
            DISTILLED_SIGMA_VALUES,
        )
        from diffusers.utils import encode_video, load_image

        from fit_input import fit_to_output

        fitted, fit_width, fit_height = fit_to_output(load_image(image_url))
        assert (fit_width, fit_height) == (width, height)
        video, audio = self.pipeline(
            image=fitted,
            prompt=prompt,
            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_frames=CLIP_FRAMES,
            frame_rate=float(CLIP_FPS),
            sigmas=DISTILLED_SIGMA_VALUES,
            guidance_scale=1.0,
            output_type="np",
            return_dict=False,
        )
        local_path = f"/tmp/{uuid.uuid4()}.mp4"
        if audio is None:
            encode_video(video[0], fps=CLIP_FPS, output_path=local_path)
        else:
            encode_video(
                video[0],
                fps=CLIP_FPS,
                output_path=local_path,
                audio=audio[0].float().cpu(),
                audio_sample_rate=self.pipeline.vocoder.config.output_sampling_rate,
            )
        return local_path

    @modal.fastapi_endpoint(method="POST")
    async def generate_clip_endpoint(self, request: Request) -> dict[str, object]:
        import base64

        from diffusers.utils import load_image

        from fit_input import fit_to_output

        _check_auth(request)
        body = await request.json()
        image_url, prompt = _parse_body(body)

        started = time.monotonic()
        _, width, height = fit_to_output(load_image(image_url))
        local_path = self._render(image_url, prompt, width, height)
        generated = time.monotonic()

        with open(local_path, "rb") as clip:
            video_base64 = base64.b64encode(clip.read()).decode("ascii")
        return {
            "video_base64": video_base64,
            "width": width,
            "height": height,
            "duration_ms": round(CLIP_FRAMES / CLIP_FPS * 1000),
            "load_seconds": 0.0,
            "generate_seconds": round(generated - started, 1),
        }
