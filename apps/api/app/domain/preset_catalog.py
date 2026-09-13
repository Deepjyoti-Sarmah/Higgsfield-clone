from dataclasses import dataclass
from typing import Literal

from app.domain.credit_rules import VIDEO_CREDIT_COST

PresetCategory = Literal["camera", "cinematic", "dynamic"]


@dataclass(frozen=True)
class PresetDefinition:
    slug: str
    name: str
    description: str
    category: PresetCategory
    sort_order: int
    credit_cost: int = VIDEO_CREDIT_COST


PRESET_CATALOG: tuple[PresetDefinition, ...] = (
    PresetDefinition(
        "dolly-in", "Dolly In", "Glide toward the subject for a slow, cinematic reveal.", "camera", 1
    ),
    PresetDefinition("dolly-out", "Dolly Out", "Pull back to reveal the whole scene.", "camera", 2),
    PresetDefinition("pan-left", "Pan Left", "Sweep the frame smoothly to the left.", "camera", 3),
    PresetDefinition("pan-right", "Pan Right", "Sweep the frame smoothly to the right.", "camera", 4),
    PresetDefinition("tilt-up", "Tilt Up", "Rise from the bottom of the frame to the top.", "camera", 5),
    PresetDefinition(
        "ken-burns",
        "Ken Burns",
        "Slow push across the image, the classic documentary move.",
        "cinematic",
        6,
    ),
    PresetDefinition(
        "orbit-push",
        "Orbit Push",
        "Push in while the camera arcs slightly around the subject.",
        "cinematic",
        7,
    ),
    PresetDefinition(
        "slow-drift",
        "Slow Drift",
        "A barely-there diagonal float that brings stills to life.",
        "cinematic",
        8,
    ),
    PresetDefinition(
        "crash-zoom", "Crash Zoom", "A punchy snap zoom straight into the subject.", "dynamic", 9
    ),
    PresetDefinition(
        "whip-pan", "Whip Pan", "A fast, motion-blurred swing across the frame.", "dynamic", 10
    ),
    PresetDefinition("handheld", "Handheld", "Subtle shake, like a camera held by hand.", "dynamic", 11),
    PresetDefinition(
        "spiral-in", "Spiral In", "Twist inward while zooming for a dramatic entrance.", "dynamic", 12
    ),
)

PRESET_SLUGS: frozenset[str] = frozenset(preset.slug for preset in PRESET_CATALOG)
