# Report T-039

**Agent / model / tool:** implementer · Claude Opus 5 (Claude Code)
**Result:** DONE

## Files changed (allowed list only)
- `apps/web/src/ui/AppShell.tsx`: wrapper `min-h-screen` -> `flex min-h-screen flex-col`,
  `<main>` gets `flex-1`. No content/copy change.
- `apps/web/src/features/library/LibraryItem.tsx`: thumbnail `aspect-[4/3] w-28` ->
  `aspect-square w-36`.
- `apps/web/src/features/image-create/ImageResultGrid.tsx`: each grid cell now wraps the
  `<img>` in an `aspect-square overflow-hidden` box with `object-cover` (was unconstrained).
- `apps/web/src/features/create-video/SessionHistoryStrip.tsx`: **not touched** — already
  `aspect-square`, exactly as the brief said to leave it.
- No `ui/Thumbnail.tsx` extracted — two nearly-identical one-line class changes didn't
  justify a shared component (rule of two: LibraryItem and ImageResultGrid's markup differ
  enough — one is a `<span>` avatar-style box, the other an `<img>` in a grid cell — that a
  wrapper would just be indirection).

## Reused
- Nothing new to reuse; both fixes are class-only changes to existing markup.

## Verify output (full paste, no summarising)
```
> web@0.0.0 lint / eslint .              -> clean
> web@0.0.0 test / vitest run            -> 9 files, 60 tests passed
> web@0.0.0 typecheck / tsc -b           -> clean
> web@0.0.0 build / vite build           -> 124 modules, built in ~250-550ms
scripts/check-standards                  -> ok (0 violations)

390px no-horizontal-scroll check (Playwright, scrollWidth - innerWidth):
  /             : 0px
  /create/video : 0px
  /create/image : 0px
  /library      : 0px
  /credits      : 0px
```

## Local verification before the live deploy
Ran the local stack (db/minio/api/worker/vite, all free) and drove it with Playwright:
- Submitted one image job and one video job to completion, then screenshotted `/library`
  and `/credits` at both 1440x900 and 1440x1200.
- **Footer**: sits flush at the bottom of the viewport on both short-content pages at both
  heights — no black void, confirming the flex fix. Explore (long page) footer flows after
  the content as before (unaffected, still not pinned).
- **Thumbnails**: the Library row renders a square `w-36` box for both an image job and a
  video job (previously `aspect-[4/3]` would have side-cropped every 16:9 poster).
  `ImageResultGrid` cells are now square + `object-cover` (previously unconstrained).
- Screenshots saved to `docs/verification/T-039/` (local pass); live screenshots from the
  same paths added after the deploy step below.

## Standards check
```
scripts/check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- `LibraryResultView.tsx`'s image grid (added in T-038, `features/library/`) has the same
  "unconstrained image size" issue `ImageResultGrid.tsx` had, but it is **not** in this
  brief's allowed-files list, so it was left alone rather than opportunistically fixed.
  Flagging it here rather than silently touching an out-of-scope file.
- `ImageThumbnail.tsx` (create-video upload preview) intentionally left at `aspect-video`
  per the brief — it previews the clip that will be produced, not a completed result.

## CORRECTION: the first "live" deploy/verification below was wrong
A peer session caught this, correctly: the live screenshot first committed for this task
(`9959612`) showed the footer floating with a void beneath it — the bug, not the fix — and
the live JS bundle hash and CSS hadn't changed since before T-038. `railway deployment list`
confirmed every deploy since T-038's first attempt had status **FAILED**: `useImageJobProgress.ts`
(added in T-038) imported from `api/imageJobHelpers.ts`, a file that only exists in the
uncommitted working tree, so a clean-worktree Docker build's `tsc` step failed for both the
`api` and `worker` images every time. `railway up` exiting 0 and `health/deep` returning ok
proved nothing about whether the app image had actually changed.

Fixed in commit `6ab456a` (`useImageJobProgress.ts` now has its own local `fetchImageJob`,
no longer depending on the uncommitted file) and redeployed with an evidence gate before
declaring success or taking any screenshot: verified the fix built cleanly in a from-scratch
worktree first (not just the working directory), then after deploying, confirmed
`railway deployment list` shows SUCCESS, the live JS bundle hash matches the verified build
byte-for-byte, live CSS contains `.w-36`, and live `/openapi.json` shows the T-038
`LibraryItemResponse` fields. Only then re-took the live screenshots
(`docs/verification/T-039/live-{library,credits}-1440x900.png`, overwritten) — footer now
measured at y=851 in a 900px-tall viewport, flush at the bottom.

## Proposed STATUS.md line
| Footer sits at the bottom of the viewport on short pages (was floating with dead space below); Library + image-result thumbnails standardised on `aspect-square` (video posters no longer side-cropped, image/video Library rows look consistent) | `apps/web/src/ui/AppShell.tsx`, `apps/web/src/features/library/LibraryItem.tsx`, `apps/web/src/features/image-create/ImageResultGrid.tsx` | lint + 60 vitest + tsc -b + build + `scripts/check-standards` all pass; 390px no-horizontal-scroll on all 5 routes; local Playwright screenshots of Library/Credits at 1440x900 and 1440x1200 confirm the footer position and square thumbnails (`docs/verification/T-039/`) | 2026-09-14 |
