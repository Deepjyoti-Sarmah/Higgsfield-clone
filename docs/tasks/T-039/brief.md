# Brief T-039: Footer floats mid-page, and thumbnails use three different aspect ratios

**Role:** implementer (small/medium model) · **Visual only, no logic changes**
**MUST run after T-038 is committed** — T-038 owns `features/library/**` and `features/image-create/**`, and editing them at the same time will collide. Check `git log` for the T-038 commit before starting. If it is not there, stop and report BLOCKED.

## Defect 1 — the footer floats with dead space under it
`apps/web/src/ui/AppShell.tsx` line 53 is `<div className="min-h-screen …">` with `<main>` and `<AppFooter />` as ordinary block children. The container is full height, but nothing pushes the footer down, so on short pages (Library, Credits) the footer lands directly under the content with a large black void beneath it. The user screenshotted this on Library.

**Fix:**
- Wrapper: `flex min-h-screen flex-col`
- `<main>`: add `flex-1`
- The footer then sits at the bottom of the viewport on short pages and flows naturally on long ones.
- Check every route at 1440×900 **and** at a tall viewport (1440×1200) — Library, Credits, Explore, Create video, Create image, Share.

## Defect 2 — thumbnails disagree with each other and with their media
Three different conventions are in use today:
| Where | Current | Problem |
|---|---|---|
| `features/library/LibraryItem.tsx:32` | `aspect-[4/3] w-28` | Posters are 1280×720 (16:9), so `object-cover` crops the sides off every one. 112px is also small. |
| `features/create-video/SessionHistoryStrip.tsx:45` | `aspect-square w-24` | Square |
| `features/create-video/ImageThumbnail.tsx:53` | `aspect-video w-full` | 16:9 |
| `features/image-create/ImageResultGrid.tsx` | no aspect set | Unconstrained |

After T-038 the Library holds **both** video jobs (16:9 posters) and image jobs (1:1 images), so no single fixed non-square box can hold both without cropping one badly.

**Decision to implement:** standardise every *list/strip/grid* thumbnail on **`aspect-square` + `object-cover`**, and keep `aspect-video` only where a video actually plays inline (the result player and the create-video canvas). Square crops both kinds predictably and gives consistent rows.
- `LibraryItem`: `aspect-square`, and raise the width from `w-28` to about `w-36` so the row reads properly.
- `SessionHistoryStrip`: already square — leave it.
- `ImageResultGrid`: give each cell `aspect-square overflow-hidden` with `object-cover`.
- `ImageThumbnail` (the uploaded source photo on Create video): leave `aspect-video`, it previews the clip that will be produced.

If a shared thumbnail wrapper is warranted by the rule of two, extract one into `apps/web/src/ui/`; otherwise keep the classes local.

## Allowed files
- `apps/web/src/ui/AppShell.tsx` (and a new `ui/Thumbnail.tsx` only if you extract one)
- `apps/web/src/features/library/LibraryItem.tsx`
- `apps/web/src/features/image-create/ImageResultGrid.tsx`
- `apps/web/src/features/create-video/SessionHistoryStrip.tsx` (only if needed for consistency)

## Do not touch
- Any hook, any `api/` file, any backend file, `imageJobs.ts`, `imageJobHelpers.ts`
- Anything T-038 changed in `features/image-create/` beyond `ImageResultGrid.tsx`'s classes

## Acceptance checks
- [ ] On Library and Credits at 1440×900 the footer sits at the bottom of the viewport with no black void beneath
- [ ] On a long page (Explore) the footer still flows after the content, not pinned over it
- [ ] Library rows show square thumbnails, sized consistently, with video posters no longer side-cropped
- [ ] Image jobs and video jobs in the Library look consistent with each other
- [ ] No horizontal scroll at 390px on any route
- [ ] lint, test, typecheck, build, check-standards all pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```
Then screenshot Library and Credits at 1440×900 into `docs/verification/T-039/` — the footer position is the point of those shots.

## Out of scope
Footer content or copy, the header, page padding elsewhere, Explore's gallery (T-036 settled it), new features.

## Report
`docs/tasks/T-039/report.md`. Commit by exact path, plain message, no attribution trailers, include `.agent-logs/`.
