from dataclasses import dataclass

SUPERSAMPLE = 4
FRAMES = 120
FPS = 24
LANDSCAPE_RATIO = 1.2

_SMOOTHSTEP = "((on/119)*(on/119)*(3-2*(on/119)))"
_ROTATE_SMOOTHSTEP = "((n/119)*(n/119)*(3-2*(n/119)))"
_CENTER_X = "(iw/2-(iw/zoom/2))"
_CENTER_Y = "(ih/2-(ih/zoom/2))"


@dataclass(frozen=True)
class MotionRecipe:
    zoom: str
    x: str
    y: str
    margin: float = 1.0
    rotate: str | None = None
    blur_frames: int | None = None


MOTION_RECIPES: dict[str, MotionRecipe] = {
    "dolly-in": MotionRecipe(zoom="1+0.35*E", x="CX", y="CY"),
    "dolly-out": MotionRecipe(zoom="1.35-0.35*E", x="CX", y="CY"),
    "pan-left": MotionRecipe(zoom="1.2", x="(iw-iw/zoom)*(1-E)", y="CY"),
    "pan-right": MotionRecipe(zoom="1.2", x="(iw-iw/zoom)*E", y="CY"),
    "tilt-up": MotionRecipe(zoom="1.2", x="CX", y="(ih-ih/zoom)*(1-E)"),
    "ken-burns": MotionRecipe(
        zoom="1.1+0.2*E", x="(iw-iw/zoom)*(0.2+0.6*E)", y="(ih-ih/zoom)*(0.2+0.6*E)"
    ),
    "orbit-push": MotionRecipe(
        zoom="1.05+0.25*E", x="CX", y="CY", margin=1.1, rotate="-0.035+0.07*n/119"
    ),
    "slow-drift": MotionRecipe(
        zoom="1.08+0.08*E", x="(iw-iw/zoom)*(0.3+0.4*E)", y="(ih-ih/zoom)*(0.6-0.2*E)"
    ),
    "crash-zoom": MotionRecipe(zoom="1+0.5*(1-pow(1-min(on/30,1),3))+0.1*on/119", x="CX", y="CY"),
    "whip-pan": MotionRecipe(zoom="1.25", x="(iw-iw/zoom)/(1+exp(-(on-60)/5))", y="CY", blur_frames=4),
    "handheld": MotionRecipe(
        zoom="1.1",
        x="(iw-iw/zoom)*(0.5+0.15*sin(on/6.3)+0.08*sin(on/2.9+1.3))",
        y="(ih-ih/zoom)*(0.5+0.15*sin(on/7.7+0.5)+0.08*sin(on/3.7))",
    ),
    "spiral-in": MotionRecipe(zoom="1+0.4*E", x="CX", y="CY", margin=1.25, rotate="0.105*E"),
}


def pick_canvas(input_width: int, input_height: int) -> tuple[int, int]:
    ratio = input_width / input_height
    if ratio > LANDSCAPE_RATIO:
        return 1280, 720
    if ratio < 1 / LANDSCAPE_RATIO:
        return 720, 1280
    return 720, 720


def build_motion_filter(recipe: MotionRecipe, width: int, height: int) -> str:
    scaled_width = _even(width * recipe.margin)
    scaled_height = _even(height * recipe.margin)
    filters = [
        f"scale={scaled_width * SUPERSAMPLE}:{scaled_height * SUPERSAMPLE}"
        ":force_original_aspect_ratio=increase",
        f"crop={scaled_width * SUPERSAMPLE}:{scaled_height * SUPERSAMPLE}",
        "setsar=1",
        f"zoompan=z='{_expand(recipe.zoom)}':x='{_expand(recipe.x)}':y='{_expand(recipe.y)}'"
        f":d={FRAMES}:s={scaled_width}x{scaled_height}:fps={FPS}",
    ]
    if recipe.rotate is not None:
        filters.append(f"rotate=a='{_expand_rotation(recipe.rotate)}':ow=iw:oh=ih:c=black")
        filters.append(f"crop={width}:{height}")
    if recipe.blur_frames is not None:
        filters.append(f"tmix=frames={recipe.blur_frames}")
    filters.append("format=yuv420p")
    return ",".join(filters)


def _expand(expression: str) -> str:
    return expression.replace("E", _SMOOTHSTEP).replace("CX", _CENTER_X).replace("CY", _CENTER_Y)


def _expand_rotation(expression: str) -> str:
    return expression.replace("E", _ROTATE_SMOOTHSTEP)


def _even(value: float) -> int:
    rounded = int(round(value))
    return rounded if rounded % 2 == 0 else rounded - 1
