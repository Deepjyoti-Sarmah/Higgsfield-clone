from app.domain.preset_catalog import PRESET_CATALOG

FALLBACK_MOTION = "Subtle, slow camera motion."
SCENE_CLAUSE = (
    "Keep the same subject, scene, framing and lighting as the input image; "
    "no new objects, no scene change."
)
QUALITY_CLAUSE = "Cinematic, smooth camera motion, natural detail, stable exposure."
USER_PROMPT_MAX_CHARS = 300

_PRESET_MOTION_BY_SLUG = {preset.slug: preset.description for preset in PRESET_CATALOG}


def compose_clip_prompt(preset_slug: str, user_prompt: str | None) -> str:
    parts = [_PRESET_MOTION_BY_SLUG.get(preset_slug, FALLBACK_MOTION)]
    trimmed_user_prompt = (user_prompt or "").strip()
    if trimmed_user_prompt:
        parts.append(trimmed_user_prompt[:USER_PROMPT_MAX_CHARS])
    parts.append(SCENE_CLAUSE)
    parts.append(QUALITY_CLAUSE)
    return " ".join(parts)
