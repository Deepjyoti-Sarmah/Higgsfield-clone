"""Capture Reel & Still studio screenshots against a running app.

Usage: /usr/bin/python3 docs/verification/T-050/capture.py [base_url] [out_dir]
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "docs/verification/T-050")
OUT.mkdir(parents=True, exist_ok=True)

R2 = "https://pub-e14a8ad582a945a7a46dd46e2b138ec2.r2.dev"
SEQUENCE_URL = (
    R2 + "/users/62fc7a93-fbfc-49a6-a228-05a5c6184337/jobs/"
    "42e05b9f-08be-4876-bdce-1cac0b608ab5/video.mp4"
)
SEQUENCE_POSTER = (
    R2 + "/users/62fc7a93-fbfc-49a6-a228-05a5c6184337/jobs/"
    "42e05b9f-08be-4876-bdce-1cac0b608ab5/poster.jpg"
)
STILL = "/showcase/sample-01.jpg"
PORTRAIT = "/showcase/sample-03.jpg"


def preview(slug: str) -> str:
    return R2 + "/previews/" + slug + ".jpg"


def preview_mp4(slug: str) -> str:
    return R2 + "/previews/" + slug + ".mp4"


def item(**overrides: object) -> dict:
    base = {
        "id": "00000000-0000-4000-8000-000000000000",
        "kind": "video",
        "status": "succeeded",
        "preset_slug": None,
        "preset_name": None,
        "prompt": None,
        "thumbnail_url": None,
        "video_url": None,
        "image_urls": [],
        "images": [],
        "clip_count": None,
        "duration_ms": 5000,
        "generated_by": "modal",
        "error_message": None,
        "created_at": "2026-09-26T05:00:00+00:00",
    }
    base.update(overrides)
    return base


ITEMS = [
    item(id="11111111-1111-4111-8111-111111111111", preset_slug="dolly-in",
         preset_name="Dolly In", prompt="Neon alley, slow push in",
         thumbnail_url=preview("dolly-in"), video_url=preview_mp4("dolly-in")),
    item(id="22222222-2222-4222-8222-222222222222", preset_slug="orbit-push",
         preset_name="Orbit Push", prompt="Desert canyon orbit",
         thumbnail_url=preview("orbit-push"), video_url=preview_mp4("orbit-push")),
    item(id="33333333-3333-4333-8333-333333333333", kind="video_faceswap",
         prompt="Portrait, face swapped", thumbnail_url=PORTRAIT,
         video_url=SEQUENCE_URL, duration_ms=6000),
    item(id="44444444-4444-4444-8444-444444444444", kind="image",
         prompt="Forest path in morning light", thumbnail_url=STILL,
         image_urls=[STILL],
         images=[{"asset_id": "55555555-5555-4555-8555-555555555555", "url": STILL}],
         duration_ms=None),
    item(id="66666666-6666-4666-8666-666666666666", kind="sequence", prompt=None,
         thumbnail_url=SEQUENCE_POSTER, video_url=SEQUENCE_URL, clip_count=2,
         duration_ms=7000),
]


def fulfill_jobs(route) -> None:
    route.fulfill(status=200, content_type="application/json",
                  body=json.dumps({"items": ITEMS}))


def shot(page: Page, name: str, full: bool = False) -> None:
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1400)
    page.screenshot(path=str(OUT / name), full_page=full)
    print("saved", name)


def studio_sequence(page: Page) -> None:
    page.get_by_role("tab", name="Sequence").click()
    page.wait_for_timeout(400)
    panel = page.locator('section[aria-label="Add a shot"]')
    panel.get_by_role("button", name="Add", exact=True).first.click()
    page.wait_for_timeout(300)
    panel.get_by_role("button", name="Add", exact=True).first.click()
    page.wait_for_timeout(400)


def verify_handoff(page: Page) -> None:
    page.get_by_role("tab", name="Sequence").click()
    page.wait_for_timeout(400)
    panel = page.locator('section[aria-label="Add a shot"]')
    panel.get_by_role("button", name="Add", exact=True).first.click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="Face swap shot 1").click()
    page.wait_for_timeout(700)
    tool_tab = page.get_by_role("tab", name="Face swap").get_attribute("aria-selected")
    video_tab = page.get_by_role("tab", name="Video target").get_attribute("aria-selected")
    print("HANDOFF face-swap selected:", tool_tab, "| video target selected:", video_tab)
    page.screenshot(path=str(OUT / "swap-handoff-light-1440.png"), full_page=True)


def capture(scheme: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900},
                                      color_scheme=scheme)
        page = context.new_page()
        page.route("**/api/v1/jobs*", fulfill_jobs)
        page.goto(BASE + "/", wait_until="load")
        shot(page, "start-" + scheme + "-1440.png", full=True)
        page.goto(BASE + "/studio", wait_until="load")
        page.wait_for_timeout(2500)
        shot(page, "studio-still-" + scheme + "-1440.png")
        studio_sequence(page)
        shot(page, "studio-sequence-" + scheme + "-1440.png", full=True)
        page.get_by_role("tab", name="Face swap").click()
        shot(page, "studio-faceswap-" + scheme + "-1440.png")
        if scheme == "light":
            verify_handoff(page)
        context.close()
        mobile = browser.new_context(viewport={"width": 390, "height": 844},
                                     color_scheme=scheme)
        mpage = mobile.new_page()
        mpage.route("**/api/v1/jobs*", fulfill_jobs)
        mpage.goto(BASE + "/studio", wait_until="load")
        mpage.wait_for_timeout(2000)
        studio_sequence(mpage)
        shot(mpage, "studio-sequence-" + scheme + "-390.png", full=True)
        mobile.close()
        browser.close()


if __name__ == "__main__":
    for color_scheme in ("light", "dark"):
        capture(color_scheme)
