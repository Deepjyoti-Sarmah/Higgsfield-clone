from app.domain.image_rules import ImageAspectRatio, ImageQuality

FLUX_PIXEL_SIZES: dict[ImageAspectRatio, tuple[int, int]] = {
    "1:1": (1024, 1024),
    "4:5": (832, 1216),
    "3:2": (1216, 832),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
}

FLUX_STEPS: dict[ImageQuality, int] = {"standard": 4, "high": 8}


def steps_for_quality(quality: ImageQuality) -> int:
    return FLUX_STEPS[quality]
