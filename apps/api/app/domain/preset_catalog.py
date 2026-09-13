from dataclasses import dataclass
from typing import Literal

from app.domain.credit_rules import VIDEO_CREDIT_COST

PresetCategory = Literal["camera", "cinematic", "dynamic"]
PREVIEW_PREFIX = "previews"


@dataclass(frozen=True)
class PresetDefinition:
    slug: str
    name: str
    description: str
    category: PresetCategory
    sort_order: int
    credit_cost: int = VIDEO_CREDIT_COST
    preview_key: str | None = None


def preview_key_for(slug: str) -> str:
    return f"{PREVIEW_PREFIX}/{slug}.mp4"


PRESET_CATALOG: tuple[PresetDefinition, ...] = (
    PresetDefinition(
        "dolly-in",
        "Dolly In",
        "Glide toward the subject for a slow, cinematic reveal.",
        "camera",
        1,
        preview_key=preview_key_for("dolly-in"),
    ),
    PresetDefinition(
        "dolly-out",
        "Dolly Out",
        "Pull back to reveal the whole scene.",
        "camera",
        2,
        preview_key=preview_key_for("dolly-out"),
    ),
    PresetDefinition(
        "pan-left",
        "Pan Left",
        "Sweep the frame smoothly to the left.",
        "camera",
        3,
        preview_key=preview_key_for("pan-left"),
    ),
    PresetDefinition(
        "pan-right",
        "Pan Right",
        "Sweep the frame smoothly to the right.",
        "camera",
        4,
        preview_key=preview_key_for("pan-right"),
    ),
    PresetDefinition(
        "tilt-up",
        "Tilt Up",
        "Rise from the bottom of the frame to the top.",
        "camera",
        5,
        preview_key=preview_key_for("tilt-up"),
    ),
    PresetDefinition(
        "ken-burns",
        "Ken Burns",
        "Slow push across the image, the classic documentary move.",
        "cinematic",
        6,
        preview_key=preview_key_for("ken-burns"),
    ),
    PresetDefinition(
        "orbit-push",
        "Orbit Push",
        "Push in while the camera arcs slightly around the subject.",
        "cinematic",
        7,
        preview_key=preview_key_for("orbit-push"),
    ),
    PresetDefinition(
        "slow-drift",
        "Slow Drift",
        "A barely-there diagonal float that brings stills to life.",
        "cinematic",
        8,
        preview_key=preview_key_for("slow-drift"),
    ),
    PresetDefinition(
        "crash-zoom",
        "Crash Zoom",
        "A punchy snap zoom straight into the subject.",
        "dynamic",
        9,
        preview_key=preview_key_for("crash-zoom"),
    ),
    PresetDefinition(
        "whip-pan",
        "Whip Pan",
        "A fast, motion-blurred swing across the frame.",
        "dynamic",
        10,
        preview_key=preview_key_for("whip-pan"),
    ),
    PresetDefinition(
        "handheld",
        "Handheld",
        "Subtle shake, like a camera held by hand.",
        "dynamic",
        11,
        preview_key=preview_key_for("handheld"),
    ),
    PresetDefinition(
        "spiral-in",
        "Spiral In",
        "Twist inward while zooming for a dramatic entrance.",
        "dynamic",
        12,
        preview_key=preview_key_for("spiral-in"),
    ),
)

PRESET_SLUGS: frozenset[str] = frozenset(preset.slug for preset in PRESET_CATALOG)
PREVIEW_KEYS: dict[str, str] = {
    preset.slug: preset.preview_key for preset in PRESET_CATALOG if preset.preview_key
}
