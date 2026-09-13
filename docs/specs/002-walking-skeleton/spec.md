# Spec 002: Walking skeleton (live, deployable, guest session)

**Status:** APPROVED (part of M2 in the approved plan)  ·  **Priority:** P0
**Research refs:** global chrome in `docs/research/flows/explore.md` (nav, dark theme, accent CTA); screenshot `01`

## Problem / why
Deploying is the biggest time risk in a 24h build. So a thin slice (DB + API + worker + SPA) goes live **first**, and every feature after it ships onto a pipeline that already works. It also sets up the stack, the contract flow and the standards tooling that every later task follows.

## User story
As a first-time visitor, I want to open the public link and start a guest session in one click, so that I can use the product without signing up.

## Acceptance criteria
- **AC-1:** Given the live URL, when `GET /api/health` is called while signed out, then it returns `200 {"status":"ok","database":"ok"}`.
- **AC-2:** Given a signed-out browser, when the live URL opens, then the app shell appears:
  - dark theme
  - nav with Explore, Create video, Create image, Library, Credits
  - a primary "Continue as guest" button
- **AC-3:** Given the shell, when "Continue as guest" is clicked, then:
  - a guest user is created
  - an httpOnly, Secure, SameSite=Lax session cookie is set
  - the header shows `Guest · <first 6 chars of id>`
  - after a reload, the header still shows the same guest
- **AC-4:** Given no session cookie, when `GET /api/v1/me` is called, then it returns `401`.
- **AC-5:** Given the same container image started with `APP_ROLE=worker`, when it boots, then it connects to the DB and logs a heartbeat line every 10s.
- **AC-6 (Modal spike):** Given a Modal token and R2 keys, when `modal run apps/gpu/ltx_spike.py --image <url> --prompt "<text>"` runs, then a ≤5s mp4 is generated with LTX-2.5 distilled, uploaded to R2, and its object key and generation time are printed.
- **AC-7:** All of these pass: `scripts/check-standards`, `ruff`, `pytest`, `tsc --noEmit`, `eslint`.

## UI states
- **Empty:** shell + "Continue as guest" (signed out).
- **Loading:** button shows a spinner and is disabled while the guest request runs.
- **Error:** inline message under the button if the API fails ("Couldn't start a session. Try again.").
- **Success:** header shows the guest label; the CTA is replaced by a "Create video" link (a placeholder route for spec 003).

## Out of scope
- Explore content, presets, generation, credits UI, Google OAuth, share pages (specs 003+).

## Open questions
- Railway, Neon, R2 and Modal credentials come from the user (see `docs/STATUS.md` BROKEN).
