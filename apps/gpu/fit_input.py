"""Pure Pillow helper: crop and resize an input image to a clip's output size."""

from PIL import Image

LANDSCAPE_SIZE = (960, 544)
PORTRAIT_SIZE = (544, 960)
SQUARE_SIZE = (704, 704)
LANDSCAPE_THRESHOLD = 1.2
PORTRAIT_THRESHOLD = 0.83


def _pick_output_size(width: int, height: int) -> tuple[int, int]:
    aspect = width / height
    if aspect >= LANDSCAPE_THRESHOLD:
        return LANDSCAPE_SIZE
    if aspect <= PORTRAIT_THRESHOLD:
        return PORTRAIT_SIZE
    return SQUARE_SIZE


def _center_crop_to_aspect(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    target_aspect = target_width / target_height
    width, height = image.size
    current_aspect = width / height
    if current_aspect > target_aspect:
        crop_width = round(height * target_aspect)
        left = (width - crop_width) // 2
        return image.crop((left, 0, left + crop_width, height))
    crop_height = round(width / target_aspect)
    top = (height - crop_height) // 2
    return image.crop((0, top, width, top + crop_height))


def fit_to_output(image: Image.Image) -> tuple[Image.Image, int, int]:
    """Crop to the nearest supported aspect, then resize to that exact size."""
    width, height = _pick_output_size(*image.size)
    cropped = _center_crop_to_aspect(image, width, height)
    fitted = cropped.resize((width, height), Image.LANCZOS)
    return fitted, width, height
