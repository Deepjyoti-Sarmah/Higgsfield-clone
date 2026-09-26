"""T6b: video-target face swap on Modal, face_swap_core once per frame."""

import base64
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import modal
from fastapi import HTTPException, Request

from face_swap import MODEL_DIR, download_models

MAX_FPS = 10
MAX_FRAMES = 300
FACELESS_RATIO_LIMIT = 0.5
NO_FACE_VIDEO_MESSAGE = "No face found in over half of the video frames"

video_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libgl1", "libglib2.0-0", "ffmpeg")
    .pip_install(
        "insightface==0.7.3", "onnxruntime-gpu==1.19.2", "opencv-python-headless==4.10.0.84",
        "numpy<2", "huggingface_hub", "fastapi", "httpx",
    )
    .env({"INSIGHTFACE_HOME": MODEL_DIR})
    .add_local_python_source("face_swap_core")
    .add_local_python_source("face_swap")
)
weights_volume = modal.Volume.from_name("face-swap-weights", create_if_missing=True)
app = modal.App("higgsfield-video-face-swap", image=video_image)


def plan_frame_sampling(duration_s: float, source_fps: float) -> tuple[float, int]:
    fps = min(max(source_fps, 1.0), MAX_FPS)
    return fps, max(min(int(duration_s * fps), MAX_FRAMES), 1)


def check_faceless_ratio(faceless: int, total: int) -> None:
    from face_swap_core import NO_FACE_IN_TARGET, NoFaceError

    if total <= 0:
        raise NoFaceError(NO_FACE_IN_TARGET)
    if faceless / total > FACELESS_RATIO_LIMIT:
        raise NoFaceError(NO_FACE_VIDEO_MESSAGE)


def build_extract_args(target: Path, pattern: Path, fps: float) -> list[str]:
    return ["-i", str(target), "-vf", f"fps={fps}", str(pattern)]


def build_assemble_args(pattern: Path, target: Path, output: Path, fps: float) -> list[str]:
    return ["-framerate", f"{fps}", "-i", str(pattern), "-i", str(target), "-map", "0:v",
            "-map", "1:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-shortest", str(output)]


def _download_bytes(url: str) -> bytes:
    import httpx

    response = httpx.get(url, timeout=60.0, follow_redirects=True)
    response.raise_for_status()
    return response.content


def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True)


def _probe_target(path: Path) -> tuple[float, float, int, int]:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration:stream=codec_type,width,height,avg_frame_rate",
                             "-of", "json", str(path)], capture_output=True, text=True, check=False)
    payload = json.loads(result.stdout or "{}")
    video = next(s for s in payload["streams"] if s["codec_type"] == "video")
    num, denom = video["avg_frame_rate"].split("/")
    fmt = payload["format"]
    return float(fmt["duration"]), float(num) / float(denom), int(video["width"]), int(video["height"])


def _load_restorer(onnx_path: str):
    import onnxruntime

    return onnxruntime.InferenceSession(onnx_path, providers=["CUDAExecutionProvider"])


@app.cls(gpu="L4", timeout=1800, volumes={"/weights": weights_volume}, scaledown_window=300,
        secrets=[modal.Secret.from_name("huggingface"), modal.Secret.from_name("modal-auth")])
class VideoFaceSwapper:
    @modal.enter()
    def load(self) -> None:
        import insightface
        from insightface.app import FaceAnalysis

        swapper_path, restorer_path = download_models()
        weights_volume.commit()
        self.analyzer = FaceAnalysis(name="buffalo_l", root=MODEL_DIR)
        self.analyzer.prepare(ctx_id=0, det_size=(640, 640))
        self.swapper = insightface.model_zoo.get_model(swapper_path)
        self.restorer = _load_restorer(restorer_path)

    def restore_face(self, crop):
        import cv2
        import numpy as np

        size = self.restorer.get_inputs()[0].shape[2]
        small = cv2.resize(crop, (size, size))
        blob = (np.transpose(cv2.cvtColor(small, cv2.COLOR_BGR2RGB).astype("float32") / 255.0,
                             (2, 0, 1))[None, ...] - 0.5) / 0.5
        out = self.restorer.run(None, {self.restorer.get_inputs()[0].name: blob})[0][0]
        fixed = cv2.cvtColor(np.clip((np.transpose(out, (1, 2, 0)) * 0.5 + 0.5) * 255.0,
                                     0, 255).astype("uint8"), cv2.COLOR_RGB2BGR)
        return cv2.resize(fixed, (crop.shape[1], crop.shape[0]))

    def _swap_frames(self, frames: list[Path], source_face) -> int:
        import cv2
        from face_swap_core import swap_and_restore

        faceless = 0
        for frame_path in frames:
            frame = cv2.imread(str(frame_path))
            faces = self.analyzer.get(frame)
            if not faces:
                faceless += 1
                continue
            swapped = swap_and_restore(frame, faces, source_face, self.swapper, self.restore_face)
            cv2.imwrite(str(frame_path), swapped)
        return faceless

    def _run_swap_video(self, source_url: str, target_url: str) -> tuple[bytes, int, int, int]:
        import cv2
        import numpy as np
        from face_swap_core import require_source_face

        raw = np.frombuffer(_download_bytes(source_url), dtype=np.uint8)
        source_image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if source_image is None:
            raise ValueError(f"could not decode source image from {source_url}")
        with tempfile.TemporaryDirectory(prefix="hf-video-swap-") as directory:
            work_dir = Path(directory)
            target_path = work_dir / "target.mp4"
            target_path.write_bytes(_download_bytes(target_url))
            duration_s, source_fps, width, height = _probe_target(target_path)
            fps, _ = plan_frame_sampling(duration_s, source_fps)
            pattern = work_dir / "frame-%04d.png"
            _run_ffmpeg(build_extract_args(target_path, pattern, fps))
            frames = sorted(work_dir.glob("frame-*.png"))
            source_face = require_source_face(self.analyzer.get(source_image))
            check_faceless_ratio(self._swap_frames(frames, source_face), len(frames))
            output_path = work_dir / "swapped.mp4"
            _run_ffmpeg(build_assemble_args(pattern, target_path, output_path, fps))
            return output_path.read_bytes(), width, height, int(duration_s * 1000)

    @modal.method()
    def swap_video(self, source_url: str, target_url: str) -> tuple[bytes, int, int, int]:
        return self._run_swap_video(source_url, target_url)

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
            video_bytes, width, height, duration_ms = self._run_swap_video(source_url, target_url)
        except NoFaceError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return {"video_base64": base64.b64encode(video_bytes).decode("ascii"), "width": width,
                "height": height, "duration_ms": duration_ms,
                "seconds": round(time.monotonic() - started, 1)}


@app.local_entrypoint()
def main(source: str, target: str, out: str = "build/video-face-swap/result.mp4") -> None:
    swapper = VideoFaceSwapper()
    video_bytes, width, height, duration_ms = swapper.swap_video.remote(source, target)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(video_bytes)
    print(f"wrote {out_path} ({width}x{height} {duration_ms}ms)")
