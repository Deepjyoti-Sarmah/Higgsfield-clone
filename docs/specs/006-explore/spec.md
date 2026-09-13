# Spec 006: Explore (signed-out landing page)

**Status:** APPROVED  ·  **Priority:** P0
**Research refs:** `docs/research/flows/explore.md` (sections 1, 2, 4; screenshots `01`, `03`); verdicts in `docs/research/product-map.md` rows 10 and 11
**Depends on:** spec 003 contract (`GET /api/v1/presets`), spec 004 `?preset=` deep link
**Handoff:** the delivery of this pack (spec + design + tasks + briefs) is the user's approval, the same convention spec 004 uses.

## Problem / why
Explore is the first thing a visitor sees and the only signed-out surface. The original buries the creation entry
points under four promo banners, a countdown and discount badges, and hides effect names behind hover so they
cannot be read on touch. Ours should be the opposite: one hero, five tool cards, and every effect visible as
scannable text with a one-click "Recreate" into Create video.

This is the second P0 slice of the core loop: spec 004 can generate, but nothing on the landing page leads there.

## User story
As a visitor (signed out), I want to see the available effects and what I can do with them, so that I can pick one
and land in Create video with that effect already selected, without signing up or hunting through the page.

## Acceptance criteria (each one testable; verify-slice checks exactly these)
- **AC-1 Layout:** `/` serves the Explore page, top to bottom: hero → tool cards → effect gallery. No promo
  banners, countdowns, discount badges or "New" chips anywhere on the page.
- **AC-2 Hero:** one `h1`, a one-line subtitle, and a primary CTA link to `/create/video`. Readable and usable
  signed out.
- **AC-3 Tool cards:** exactly 5, in this order — Explore (`/`), Create video (`/create/video`),
  Create image (`/create/image`), Library (`/library`), Credits (`/credits`). Each card is one link with a
  visible label and a one-line description, keyboard-focusable with a visible focus ring.
- **AC-4 Effect gallery:** on mount the page calls `GET /api/v1/presets` once and renders **every** returned
  preset, grouped into the fixed category order camera → cinematic → dynamic, one labelled section per
  non-empty category.
- **AC-5 Preset card:** every card shows the preset **name as visible text** (never hover-only), its category,
  its real `credit_cost` ("20 credits") and a "Recreate" action. No names may require hover to be read.
- **AC-6 Recreate:** activating "Recreate" navigates to `/create/video?preset=<slug>` (slug URL-encoded), where
  the existing `usePresetSelection` picks the `?preset=` parameter up and preselects that preset (spec 004 AC-3).
- **AC-7 Signed out:** browsing, the tool cards and Recreate all work with no session; nothing on Explore opens
  a login wall. `GET /api/v1/presets` is public and needs no credentials.
- **AC-8 States:** loading shows skeleton tiles in an `aria-busy` region; error (network or non-200) shows
  "We couldn't load the effects." with a Retry action that re-fetches; empty (200 with zero presets) shows the
  empty message; success shows the gallery.
- **AC-9 Accessibility:** the gallery is a labelled region with one heading per category; each "Recreate" is a
  real link (keyboard and middle-click work); the card name is text; decorative tiles are `aria-hidden`.
- **AC-10 No contract change:** no route or schema is added or changed; after `scripts/export-openapi`,
  `packages/contracts/openapi.json` is byte-identical.

## UI states (every one must be designed)
- **Empty:** 200 with `presets: []` → "No effects yet." / "Effects will appear here as soon as they are published."
- **Loading:** three category headings with skeleton tiles inside an `aria-busy="true"` region.
- **Error:** "We couldn't load the effects." / "Check your connection and try again." / Retry button.
- **Success:** hero + tool cards + the grouped effect gallery.

## Out of scope
- **P1 model / sample-outputs gallery** (`product-map.md` row 12): one gallery of our own sample outputs. It
  needs real sample assets; if it ever needs a public list route, that is a new contract and a follow-up spec.
- **Per-preset video previews:** `preview_url` is `null` for all 12 presets today, so cards fall back to a static
  tile. When real previews exist the card already renders them; generating them is not this spec.
- Everything `D-012` cut from Explore: promo banners, countdown, discount badges, MCP / Supercomputer / Canvas /
  Photodump banners, community projects and profiles, search, the footer link cloud, more than 5 nav items.
- Library (005), Share page (007), Credits + top-up (008), sign-up/sign-in screens, image create (P1).

## Open questions
- None blocking. `preview_url` is nullable and currently always `null`; the card treats it as optional.
