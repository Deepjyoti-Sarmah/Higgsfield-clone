from typing import Literal

SEQUENCE_CREDIT_COST = 1
MIN_CLIPS = 2
MAX_CLIPS = 6
TRANSITIONS: tuple[str, ...] = ("cut", "crossfade", "fade_black")
SEQUENCE_TRANSITIONS: tuple[str, ...] = TRANSITIONS
SequenceTransition = Literal["cut", "crossfade", "fade_black"]
TRANSITION_SECONDS = 0.5
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 720
OUTPUT_FPS = 24
MUSIC_FADE_SECONDS = 1.0
POSTER_AT_SECONDS = 1.0
STITCH_STEP_KIND = "stitch_video"
# "ffmpeg" is not a paid backend, so sequences stay out of paid-spend accounting.
STITCH_BACKEND = "ffmpeg"
MAX_AUDIO_BYTES = 10 * 1024 * 1024
MIN_TRIMMED_SECONDS = 1.0
