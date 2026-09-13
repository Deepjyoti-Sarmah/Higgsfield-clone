"""T-002-5 spike: LTX-2.5 distilled image->video on Modal, uploaded to R2.

Needs `modal token new` plus `r2` and `huggingface` secrets (the model is gated).
"""

import os
import time
import uuid

import modal

MODEL_ID = "Lightricks/LTX-2.5-Diffusers"
CLIP_FRAMES = 121
CLIP_FPS = 24

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
        "git+https://github.com/huggingface/diffusers",
    )
    .env({"HF_HUB_CACHE": "/weights"})
)
weights_volume = modal.Volume.from_name("ltx-weights", create_if_missing=True)
app = modal.App("higgsfield-ltx-spike", image=gpu_image)


def upload_clip_to_r2(local_path: str) -> str:
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    key = f"spikes/{os.path.basename(local_path)}"
    client.upload_file(
        local_path, os.environ["R2_BUCKET"], key, ExtraArgs={"ContentType": "video/mp4"}
    )
    return key


@app.function(
    gpu="A10G",
    timeout=1800,
    volumes={"/weights": weights_volume},
    secrets=[modal.Secret.from_name("r2"), modal.Secret.from_name("huggingface")],
)
def generate_clip(image_url: str, prompt: str) -> dict[str, object]:
    import torch
    from diffusers import LTX2ImageToVideoPipeline
    from diffusers.pipelines.ltx2.utils import (
        DEFAULT_NEGATIVE_PROMPT,
        DISTILLED_SIGMA_VALUES,
    )
    from diffusers.utils import encode_video, load_image

    started = time.monotonic()
    pipeline = LTX2ImageToVideoPipeline.from_pretrained(MODEL_ID, dtype=torch.bfloat16)
    pipeline.enable_sequential_cpu_offload()
    weights_volume.commit()
    loaded = time.monotonic()

    video, audio = pipeline(
        image=load_image(image_url),
        prompt=prompt,
        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
        width=960,
        height=544,
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
            audio_sample_rate=pipeline.vocoder.config.output_sampling_rate,
        )
    generated = time.monotonic()

    return {
        "r2_key": upload_clip_to_r2(local_path),
        "load_seconds": round(loaded - started, 1),
        "generate_seconds": round(generated - loaded, 1),
    }


@app.local_entrypoint()
def main(image: str, prompt: str) -> None:
    print(generate_clip.remote(image, prompt))
