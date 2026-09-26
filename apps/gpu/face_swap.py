"""T-011-3: face-swap endpoint on Modal (insightface swapper + GFPGAN restore).

Models come from the `facefusion/models-3.0.0` Hugging Face repo (inswapper,
GFPGAN) plus insightface's own `buffalo_l` detector bundle, all cached on a
Modal Volume so a warm container never re-downloads them.
"""

import base64
import os
import time

import modal
from fastapi import HTTPException, Request

MODELS_REPO = "facefusion/models-3.0.0"
SWAPPER_FILE = "inswapper_128_fp16.onnx"
RESTORER_FILE = "gfpgan_1.4.onnx"
MODEL_DIR = "/weights"

gpu_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libgl1", "libglib2.0-0")
    .pip_install(
        "insightface==0.7.3",
        "onnxruntime-gpu==1.19.2",
        "opencv-python-headless==4.10.0.84",
        "numpy<2",
        "huggingface_hub",
        "fastapi",
        "httpx",
    )
    .env({"INSIGHTFACE_HOME": MODEL_DIR})
    .add_local_python_source("face_swap_core")
)
weights_volume = modal.Volume.from_name("face-swap-weights", create_if_missing=True)
app = modal.App("higgsfield-face-swap", image=gpu_image)


def download_models() -> tuple[str, str]:
    from huggingface_hub import hf_hub_download

    swapper_path = hf_hub_download(
        repo_id=MODELS_REPO, filename=SWAPPER_FILE, local_dir=MODEL_DIR
    )
    restorer_path = hf_hub_download(
        repo_id=MODELS_REPO, filename=RESTORER_FILE, local_dir=MODEL_DIR
    )
    return swapper_path, restorer_path


def load_image_from_url(url: str):
    import cv2
    import httpx
    import numpy as np

    response = httpx.get(url, timeout=30.0, follow_redirects=True)
    response.raise_for_status()
    array = np.frombuffer(response.content, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"could not decode image from {url}")
    return image


@app.cls(
    gpu="L4",
    timeout=600,
    volumes={"/weights": weights_volume},
    scaledown_window=300,
    secrets=[modal.Secret.from_name("huggingface"), modal.Secret.from_name("modal-auth")],
)
class FaceSwapper:
    @modal.enter()
    def load(self) -> None:
        import insightface
        from insightface.app import FaceAnalysis

        swapper_path, restorer_path = download_models()
        weights_volume.commit()
        self.analyzer = FaceAnalysis(name="buffalo_l", root=MODEL_DIR)
        self.analyzer.prepare(ctx_id=0, det_size=(640, 640))
        self.swapper = insightface.model_zoo.get_model(swapper_path)
        self.restorer = _load_gfpgan(restorer_path)

    def restore_face(self, crop):
        import cv2
        import numpy as np

        input_size = self.restorer.get_inputs()[0].shape[2]
        resized = cv2.resize(crop, (input_size, input_size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        blob = rgb.astype("float32") / 255.0
        blob = (blob - 0.5) / 0.5
        blob = np.transpose(blob, (2, 0, 1))[None, ...]
        output = self.restorer.run(None, {self.restorer.get_inputs()[0].name: blob})[0][0]
        output = np.transpose(output, (1, 2, 0))
        output = np.clip((output * 0.5 + 0.5) * 255.0, 0, 255).astype("uint8")
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        return cv2.resize(output, (crop.shape[1], crop.shape[0]))

    def _run_swap(self, source_url: str, target_url: str) -> tuple[bytes, int, int]:
        from face_swap_core import require_source_face, require_target_faces, swap_and_restore

        source_image = load_image_from_url(source_url)
        target_image = load_image_from_url(target_url)
        source_face = require_source_face(self.analyzer.get(source_image))
        target_faces = require_target_faces(self.analyzer.get(target_image))
        output = swap_and_restore(
            target_image, target_faces, source_face, self.swapper, self.restore_face
        )
        import cv2

        success, buffer = cv2.imencode(".png", output)
        if not success:
            raise ValueError("could not encode result as PNG")
        height, width = output.shape[:2]
        return buffer.tobytes(), width, height

    @modal.method()
    def swap(self, source_url: str, target_url: str) -> tuple[bytes, int, int]:
        return self._run_swap(source_url, target_url)

    @modal.fastapi_endpoint(method="POST")
    async def endpoint(self, request: Request) -> dict[str, object]:
        from face_swap_core import NoFaceError

        expected = f"Bearer {os.environ['MODAL_WEBHOOK_SECRET']}"
        if request.headers.get("authorization") != expected:
            raise HTTPException(status_code=401, detail="unauthorized")
        body = await request.json()
        source_url = body.get("source_url")
        target_url = body.get("target_url")
        if not isinstance(source_url, str) or not isinstance(target_url, str):
            raise HTTPException(status_code=422, detail="source_url and target_url are required")
        started = time.monotonic()
        try:
            png_bytes, width, height = self._run_swap(source_url, target_url)
        except NoFaceError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {
            "image_base64": base64.b64encode(png_bytes).decode("ascii"),
            "width": width,
            "height": height,
            "seconds": round(time.monotonic() - started, 1),
        }


def _load_gfpgan(onnx_path: str):
    import onnxruntime

    return onnxruntime.InferenceSession(onnx_path, providers=["CUDAExecutionProvider"])


@app.local_entrypoint()
def main(source: str, target: str, out: str = "build/face-swap/result.png") -> None:
    from pathlib import Path

    swapper = FaceSwapper()
    result = swapper.swap.remote(source, target)
    png_bytes, width, height = result
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png_bytes)
    print(f"wrote {out_path} ({width}x{height})")
