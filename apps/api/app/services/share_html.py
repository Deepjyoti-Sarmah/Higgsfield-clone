import html
import re
from pathlib import Path

from app.services.share_views import PublicJobView

SITE_NAME = "Higgsfield"
OG_TYPE = "video.other"
GENERIC_TITLE = "Higgsfield"
UNKNOWN_DESCRIPTION = "Watch AI-generated videos on Higgsfield."
GENERATING_DESCRIPTION = "This video is still being generated on Higgsfield."
FAILED_DESCRIPTION = "This video isn't available on Higgsfield."

TITLE_PATTERN = re.compile(r"<title>.*?</title>", re.DOTALL)

# Used when the built shell is absent (API-only env, or before `npm run build`).
FALLBACK_SHELL = (
    "<!doctype html>\n"
    '<html lang="en">\n'
    "<head>\n"
    '<meta charset="utf-8" />\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
    "<title>Higgsfield</title>\n"
    "</head>\n"
    "<body>\n"
    '<div id="root"></div>\n'
    "</body>\n"
    "</html>\n"
)


def share_url_for(base_url: str, job_id: str) -> str:
    return f"{base_url.rstrip('/')}/v/{job_id}"


def page_title(view: PublicJobView | None) -> str:
    return GENERIC_TITLE if view is None else f"{view.preset_name} \u00b7 Higgsfield"


def describe_public_job(view: PublicJobView | None) -> str:
    if view is None:
        return UNKNOWN_DESCRIPTION
    if view.job.status == "succeeded":
        return f"A 5-second AI-generated video made with the {view.preset_name} effect on Higgsfield."
    if view.job.status == "failed":
        return FAILED_DESCRIPTION
    return GENERATING_DESCRIPTION


def read_shell(static_dir: str) -> str:
    try:
        return (Path(static_dir) / "index.html").read_text(encoding="utf-8")
    except OSError:
        return FALLBACK_SHELL


def meta_tag(attribute: str, key: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    return f'    <meta {attribute}="{key}" content="{escaped}" />'


def build_meta_block(view: PublicJobView | None, share_url: str) -> str:
    title = page_title(view)
    poster_url = None if view is None else view.poster_url
    video_url = None if view is None else view.video_url
    tags = [
        meta_tag("property", "og:title", title),
        meta_tag("property", "og:description", describe_public_job(view)),
        meta_tag("property", "og:type", OG_TYPE),
        meta_tag("property", "og:site_name", SITE_NAME),
        meta_tag("property", "og:url", share_url),
    ]
    if poster_url is not None:
        tags.append(meta_tag("property", "og:image", poster_url))
        tags.append(meta_tag("name", "twitter:image", poster_url))
    if video_url is not None:
        tags.append(meta_tag("property", "og:video", video_url))
    card = "player" if video_url is not None else "summary_large_image"
    tags.append(meta_tag("name", "twitter:card", card))
    tags.append(meta_tag("name", "twitter:title", title))
    return "\n".join(tags)


def inject_meta(shell: str, title: str, meta_block: str) -> str:
    with_title = TITLE_PATTERN.sub(f"<title>{html.escape(title)}</title>", shell, count=1)
    return with_title.replace("</head>", f"{meta_block}\n  </head>", 1)


def render_share_page(shell: str, view: PublicJobView | None, share_url: str) -> str:
    return inject_meta(shell, page_title(view), build_meta_block(view, share_url))
