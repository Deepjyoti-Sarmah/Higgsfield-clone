import math

VIDEO_FACESWAP_CREDITS_PER_SECOND = 2
VIDEO_FACESWAP_STEP_KIND = "swap_face_video"
VIDEO_FACESWAP_BACKEND = "modal-video-faceswap"
VIDEO_FACESWAP_MAX_SECONDS = 30
VIDEO_FACESWAP_MAX_BYTES = 50_000_000
VIDEO_FACESWAP_TARGET_CONTENT_TYPE = "video/mp4"


def video_faceswap_cost(duration_ms: int) -> int:
    if duration_ms <= 0:
        raise ValueError(f"duration_ms must be positive, got {duration_ms}")
    return math.ceil(duration_ms / 1000) * VIDEO_FACESWAP_CREDITS_PER_SECOND
