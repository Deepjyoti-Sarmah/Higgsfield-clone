# Flow: Explore (home page)

**Source:** screenshots `01`–`14` in `docs/research/screenshots/`, captured 2026-09-13 while signed in (the avatar shows top right).
**Observation only.** Solutions belong in specs.

## Entry point
- `higgsfield.ai`: "Explore" is the active item in the top nav (01).
- Not observed: what a signed-out visitor sees (the screenshots were taken signed in).

## Global chrome (on every page, 01–16)
- **Sticky top nav, left to right:**
  - Logo, then Explore, Image, Video, Audio, MCP.
  - A divider, then ChatGPT Plugin `New`, Genjutsu `Free`, Effects `Free`, Cinema Studio, Marketing Studio, Supercomputer.
  - The last item is cut off at ~1900px width (01 shows "Superco…").
- **Right side:** search icon, Pricing (with a pink `30% OFF` badge), Enterprise, Assets (folder icon), notifications bell, avatar.
- **Styling:** dark theme (near-black background); acid yellow-green accent for primary CTAs, section titles and the active nav item; large condensed uppercase display headings.

## Page sections, top to bottom
| # | Section | What's there | Shot |
|---|---|---|---|
| 1 | Hero carousel | 3 wide video cards, each with an uppercase title and a one-line subtitle (Motion Designer, Effects, Genjutsu) | 01 |
| 2 | Promo + tool cards | Left: "complete tasks & get 55% off" card with a live countdown (`01h 45m 09s`), 2 task checkboxes, "Complete tasks" / "See plans". Right: 6 tool cards (icon, name, one-line description, badges such as `TOP`, `FREE`, and a `Video` / `Image` type chip) | 01 |
| 3 | MCP banner | Full-width banner, "Install … plugin" (primary) + "Explore use cases" (secondary) | 02 |
| 4 | Visual effects | Section title + subtitle, "Try for free" CTA top right. Masonry grid of looping portrait video tiles. **Hover** shows the effect name ("SMASH AND GRAB") + a "Recreate" button; the link goes to `/effects/examples/<slug>` | 03 |
| 5 | Genjutsu | "New model" chip, title, description, "Try free" + "Learn more". Masonry of before/after split-frame videos (the left half is the original, the right half is transformed) | 04 |
| 6 | Video model gallery | Masonry of cinematic video tiles for a model ("The most advanced AI video model") | 05 |
| 7 | Community projects | "Explore the inside of every project": 8 poster cards, each with creator avatar, title, `Public` chip. "Explore community ↗" CTA. Links go to `/@<user>/projects/<slug>` | 06 |
| 8 | Supercomputer banner | Glowing green banner, floating UI mock cards ("UGC Creator 2/2", "Marketing", "Production"), "Try Supercomputer" | 07 |
| 9 | Image model gallery | "GPT IMAGE 2 · 4K images with near-perfect text rendering": masonry of poster-style images | 07–08 |
| 10 | Canvas banner | "New feature" gradient banner + "Try Canvas" | 09 |
| 11 | Marketing Studio gallery | UGC-style talking-head video tiles | 09 |
| 12 | Community model gallery | "Browse … generations from the community": 4-column grid. Hover shows the creator avatar + username and a like count (heart, 333); links go to `/@<username>`. "View all of <model> ↗" | 10–11 |
| 13 | Photodump banner | "Different scenes, same star": build a character once, one click for many scenes | 11 |
| 14 | More galleries | Soul Cinema (video), Soul 2.0 (fashion photo model) | 11–12 |
| 15 | Feature tag cloud | "Explore more AI features": ~40 pill links (models, presets, Edit Image, Upscale, platform-specific formats) | 13 |
| 16 | Footer | Acid-green block. Columns: Create, Video Models, Image Models, Studios, Soul, Platform, Resources, Company, Community. Address, socials, language picker, legal links | 13–14 |

## Inputs and controls observed
- None on this page besides CTAs, hover "Recreate" and links. All creation happens on other pages.

## UI states observed
- Hover state on a gallery tile: name + CTA overlay (03), creator + likes (10).
- Not observed: loading/skeleton states, empty states, signed-out state.

## Credits / cost
- No costs are shown on Explore. Discount messaging appears twice: the `30% OFF` badge on Pricing, and the 55% countdown promo.

## Friction noticed (possible "better than original" angles)
- **Crowded nav:** 13+ top-level items, and the last one is cut off even at ~1900px wide.
- **Heavy promotion:** at least 4 full-width promo banners (MCP, Supercomputer, Canvas, Photodump), a countdown timer and discount badges, all competing with the actual creation entry points.
- **No single clear starting action:** the page is mostly a showcase, with many entry points (Try free, Recreate, Try Canvas, Try Supercomputer…).
- **Effect names are hidden:** they only appear on hover, so there's no text to scan and nothing obvious on touch devices.
- **Heavy page:** dozens of autoplaying videos.
