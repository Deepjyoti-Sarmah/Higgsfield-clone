from typing import Literal

ImageAspectRatio = Literal["1:1", "4:5", "3:2", "16:9", "9:16"]
ImageQuality = Literal["standard", "high"]

ASPECT_RATIOS: tuple[ImageAspectRatio, ...] = ("1:1", "4:5", "3:2", "16:9", "9:16")
QUALITIES: tuple[ImageQuality, ...] = ("standard", "high")
MAX_IMAGE_COUNT = 4

IMAGE_CREDIT_COST_STANDARD = 10
IMAGE_CREDIT_COST_HIGH = 15

IMAGE_PIXEL_SIZES: dict[ImageAspectRatio, tuple[int, int]] = {
    "1:1": (512, 512),
    "4:5": (448, 560),
    "3:2": (600, 400),
    "16:9": (640, 360),
    "9:16": (360, 640),
}


def image_credit_cost(quality: ImageQuality, count: int) -> int:
    unit = IMAGE_CREDIT_COST_HIGH if quality == "high" else IMAGE_CREDIT_COST_STANDARD
    return unit * count
