# Brief T-010-10: Start page and share viewer

**Role:** implementer (visual) · **Suggested model:** medium · **Depends on:** T-010-7 merged · **Wave:** W3

## Start here (any harness)
1. `scripts/task claim T-010-10 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Web, and **`DESIGN.md`**, especially §5 (start page), §9 (voice) and §10 (banned). Read spec 010 AC-5 and AC-18.
3. Skim the `design-taste-frontend` skill. Where it disagrees with DESIGN.md, DESIGN.md wins. For example, the skill wants a bento grid; DESIGN.md §5 says an asymmetric split and a vertical three-step stack.
4. Read `features/start/*` (the stub and `groupPresetsByCategory` from T-010-7), `features/share/*`, `api/presets.ts`, `api/webMedia.ts` and `api/share.ts`.
5. Questions: `scripts/task say T-010-10 QUESTION "…"`.

## Goal
`/` introduces Reel & Still in one screen, with real media from our storage, and sends people into the studio. `/v/:id` is a calm share viewer for clips, stills and sequences.

## Allowed files (touch nothing else)
- `apps/web/src/features/start/*` (replace the stub; keep `groupPresetsByCategory`)
- `apps/web/src/features/share/*`
- `docs/tasks/T-010-10/report.md`, `docs/verification/T-010-10/*.png`

## The change
1. **Start page** (DESIGN.md §5):
   - **Left 5/12:**
     - The display headline in Instrument Serif. Write it yourself: plain and specific, for example "Stills that move. Clips that cut together." No "AI-powered" and no exclamation marks.
     - One sentence saying what the studio does: make a still, animate it, cut clips into a short sequence.
     - One primary button, "Open the studio" → `/studio`.
   - **Right 7/12:** three stacked steps, **Still → Clip → Sequence**. Each has real media and a one-line mono caption:
     - Still: a poster or still from `webMedia`'s showcase stills, or a preset preview poster.
     - Clip: a looping muted preview clip from `usePresets()` `preview_url`, `motion-safe` autoplay, poster otherwise.
     - Sequence: two small preset posters joined by a `XFADE` chip glyph, to illustrate cutting.
   - **Below:** one row of motion-preset chips grouped by category (`groupPresetsByCategory`). Each links to `/studio?tab=clip&preset=<slug>`.
   - **States:** presets loading shows skeleton tiles; a presets error hides the preset row and the step 2 media falls back to a poster. The page never breaks.
   - Below 768px everything stacks in a single column, with media after the text.
2. **Share viewer** (`SharePage` and friends), signed out, with no studio or credits UI:
   - A small brand mark linking to `/`.
   - The media: a video for clips and sequences, the images for stills.
   - A title: the preset name, "Sequence", or "Still".
   - A mono meta line: `clip · 0:05`, or `3 shots · 0:14`, or `2 stills`.
   - One button, "Make your own" → `/studio`.
   - The existing loading, not-found and failed states, restyled per DESIGN.md.
   - Use the `kind`, `image_urls`, `clip_count` and `duration_ms` fields from T-010-1/T-010-4.
3. **Copy:** `startCopy.ts` and `shareCopy.ts`. No "Higgsfield". Run `no-ai-slop` Detect mode over both and note the results.
4. **Tests:**
   - The start page renders one primary CTA pointing to `/studio`.
   - Preset chips link to `?tab=clip&preset=`.
   - The share page renders the sequence meta (`3 shots`) and an image grid for `kind="image"`.
   - Mock the hooks.

## Acceptance checks
- [ ] AC-5 and AC-18 hold
- [ ] All start-page media come from our storage or R2 via existing `api/` helpers. No stock or external hotlinks
- [ ] Asymmetric layout, one CTA, no centred hero, no three equal cards (DESIGN.md §5 and §10)
- [ ] 390px: single column, no horizontal scroll; both themes readable
- [ ] `grep -rni higgsfield apps/web/src/features/{start,share}` returns nothing
- [ ] lint, test, typecheck, build and check-standards pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && ! grep -rni higgsfield apps/web/src/features/start apps/web/src/features/share
```
Save screenshots of `/` and of a share page at 390 and 1440px, light and dark, to `docs/verification/T-010-10/`.

## Out of scope
- The studio, composers and backend.

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-10`
2. `scripts/task submit T-010-10 --as <you> [--transcript <file>]`
