from app.domain.motion_prompts import (
    FALLBACK_MOTION,
    QUALITY_CLAUSE,
    SCENE_CLAUSE,
    USER_PROMPT_MAX_CHARS,
    compose_clip_prompt,
)


def test_blank_prompt_still_has_preset_motion_and_clauses() -> None:
    result = compose_clip_prompt("dolly-in", None)
    assert "Glide toward the subject" in result
    assert SCENE_CLAUSE in result
    assert QUALITY_CLAUSE in result


def test_blank_string_prompt_behaves_like_none() -> None:
    result = compose_clip_prompt("dolly-in", "   ")
    assert SCENE_CLAUSE in result
    assert QUALITY_CLAUSE in result


def test_user_prompt_is_included() -> None:
    result = compose_clip_prompt("dolly-in", "a red umbrella")
    assert "a red umbrella" in result


def test_unknown_slug_falls_back() -> None:
    result = compose_clip_prompt("not-a-real-slug", None)
    assert FALLBACK_MOTION in result


def test_long_user_text_is_trimmed() -> None:
    long_prompt = "x" * 500
    result = compose_clip_prompt("dolly-in", long_prompt)
    assert "x" * USER_PROMPT_MAX_CHARS in result
    assert "x" * (USER_PROMPT_MAX_CHARS + 1) not in result


def test_never_returns_empty_string() -> None:
    assert compose_clip_prompt("dolly-in", None) != ""
