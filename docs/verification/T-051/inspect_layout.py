"""Measure studio layout boxes on a running app."""
import json, sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://api-production-8afc.up.railway.app"

SCRIPT = """() => {
  const box = (sel) => { const el = document.querySelector(sel); if (!el) return null;
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return {sel, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
            pad: s.padding, mar: s.margin, display: s.display, fs: s.fontSize}; };
  const byText = (text) => { const els = [...document.querySelectorAll('h1,h2,h3,p,span,button,a')];
    const el = els.find(e => e.textContent.trim() === text); if (!el) return null;
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return {text, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), fs: s.fontSize, fw: s.fontWeight, ff: s.fontFamily.split(',')[0]}; };
  return { header: box('header'), main: box('main'), aside: box('aside'), nav: box('nav[aria-label=Tools]'),
    railHeader: byText('Your work'), newStill: byText('New still'), all: byText('All'), firstRow: box('aside nav button'),
    composer: box('section[aria-label=Composer]'), flow: box('[role=tablist]'), credits: byText('174 credits') };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.goto(BASE + "/studio", wait_until="load")
    page.wait_for_timeout(2500)
    print(json.dumps(page.evaluate(SCRIPT), indent=1))
    out = sys.argv[2] if len(sys.argv) > 2 else "docs/verification/T-051/live-before-1440.png"
    page.screenshot(path=out)
    browser.close()
