"""T-011-3: pure-ish face swap pipeline, importable without Modal or onnxruntime.

Heavy model calls (detection, swap, restore) take plain numpy arrays and
model handles as arguments, so this file stays testable with numpy alone.
"""

from __future__ import annotations

import numpy as np

NO_FACE_IN_SOURCE = "No face found in the face image"
NO_FACE_IN_TARGET = "No face found in the target image"


class NoFaceError(ValueError):
    """Raised when detection finds zero faces in an input image."""


def face_area(bbox: tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def pick_largest_face(faces: list):
    """Return the detected face with the biggest bounding-box area, or None."""
    if not faces:
        return None
    return max(faces, key=lambda face: face_area(face.bbox))


def require_source_face(faces: list):
    face = pick_largest_face(faces)
    if face is None:
        raise NoFaceError(NO_FACE_IN_SOURCE)
    return face


def require_target_faces(faces: list) -> list:
    if not faces:
        raise NoFaceError(NO_FACE_IN_TARGET)
    return faces


def feather_mask(height: int, width: int, feather_px: int) -> np.ndarray:
    """Elliptical mask, 1 in the centre, fading to 0 over `feather_px` at the edge."""
    y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
    center_y, center_x = height / 2.0, width / 2.0
    radius_y = max(height / 2.0 - feather_px, 1.0)
    radius_x = max(width / 2.0 - feather_px, 1.0)
    normalized = ((y_coords - center_y) / radius_y) ** 2 + (
        (x_coords - center_x) / radius_x
    ) ** 2
    mask = np.clip(1.0 - np.sqrt(np.maximum(normalized - 1.0, 0.0)), 0.0, 1.0)
    mask[normalized <= 1.0] = 1.0
    return mask.astype(np.float32)


def paste_with_mask(
    base: np.ndarray, patch: np.ndarray, mask: np.ndarray, top_left: tuple[int, int]
) -> np.ndarray:
    """Alpha-blend `patch` into `base` at `top_left`, weighted by `mask` (0..1)."""
    x, y = top_left
    height, width = patch.shape[:2]
    result = base.copy()
    region = result[y : y + height, x : x + width].astype(np.float32)
    blended = region * (1 - mask[..., None]) + patch.astype(np.float32) * mask[..., None]
    result[y : y + height, x : x + width] = np.clip(blended, 0, 255).astype(np.uint8)
    return result


def clamp_box(
    bbox: tuple[float, float, float, float], image_width: int, image_height: int
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(int(x1), image_width - 1))
    y1 = max(0, min(int(y1), image_height - 1))
    x2 = max(x1 + 1, min(int(x2), image_width))
    y2 = max(y1 + 1, min(int(y2), image_height))
    return x1, y1, x2, y2


def square_box(
    bbox: tuple[float, float, float, float],
    image_width: int,
    image_height: int,
    margin: float = 0.15,
) -> tuple[int, int, int, int]:
    """Expand `bbox` to a centred square (plus margin) so a resize to a square
    model input doesn't stretch the face out of proportion."""
    x1, y1, x2, y2 = bbox
    center_x, center_y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    half_side = max(x2 - x1, y2 - y1) * (1.0 + margin) / 2.0
    half_side = min(half_side, image_width / 2.0, image_height / 2.0)
    return clamp_box(
        (center_x - half_side, center_y - half_side, center_x + half_side, center_y + half_side),
        image_width,
        image_height,
    )


def swap_and_restore(
    target_image: np.ndarray,
    target_faces: list,
    source_face,
    swapper,
    restorer,
    feather_px: int = 8,
) -> np.ndarray:
    """Swap `source_face` onto every `target_faces` box, run `restorer`, paste back."""
    output = target_image.copy()
    for face in target_faces:
        output = swapper.get(output, face, source_face, paste_back=True)
        x1, y1, x2, y2 = square_box(face.bbox, output.shape[1], output.shape[0])
        crop = output[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        restored = restorer(crop)
        # GFPGAN over-sharpens relative to the rest of the photo; blending it
        # 70/30 with the plain swap avoids a "pasted sticker" look at the edges.
        softened = (restored.astype(np.float32) * 0.7 + crop.astype(np.float32) * 0.3).astype(
            np.uint8
        )
        crop_feather = max(feather_px, min(crop.shape[0], crop.shape[1]) // 6)
        mask = feather_mask(softened.shape[0], softened.shape[1], crop_feather)
        output = paste_with_mask(output, softened, mask, (x1, y1))
    return output
