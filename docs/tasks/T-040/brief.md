# Brief T-040: Clicking a Library row gives no feedback that anything opened

**Role:** implementer (small/medium model) · **Visual + interaction only, no data or API changes**

## The problem
The user clicks a row in the Library and it feels like nothing happens. Two causes:

1. **Selected is indistinguishable from hover.** `LibraryItem.tsx` lines 21-23:
   ```
   const rowClasses = isSelected ? "border-accent/60" : "border-border hover:border-accent/60"
   ```
   Hovering any row produces the same border as selecting it.
2. **The result appears off-screen with no connection to the click.** `LibraryPage.tsx` renders `<LibraryList>` then `<LibraryResultView>` in plain vertical flow. On a 1440×900 viewport with two or three rows, the player is below the fold. Nothing scrolls, nothing announces it, so the click appears to do nothing.

## The fix

### 1. Make the selected row unmistakable (`LibraryItem.tsx`)
Selected must differ from hover in **more than one** way:
- A solid accent left edge: `border-l-4 border-l-accent` (hover keeps only the subtle outer border).
- A brighter surface: `bg-surface` → something one step lighter when selected.
- A small accent chip in the row, reading `Viewing` (add the string to `libraryCopy.ts`).
- Keep `aria-current="true"` as it is.
Hover stays subtle — a slightly lighter border only.

### 2. Signal that the row is playable (`LibraryItem.tsx`)
On the thumbnail of a **video** row (`item.kind === "video"`), overlay a small circular play triangle, bottom-right, over a soft scrim so it reads on any image. Image rows get no play glyph. Mark it `aria-hidden="true"` — the row's existing `aria-label` already describes the action.

### 3. Scroll the result into view on select (`LibraryPage.tsx`)
When `selectedJobId` changes to a non-null value, scroll the result panel into view:
```
resultRef.current?.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" })
```
- Reuse the existing `usePrefersReducedMotion` hook (it is already in the codebase — find it before writing a new one).
- Only scroll on a *change* of selection, never on first mount, and never when the panel is already fully visible.

### 4. Announce it for screen readers (`LibraryPage.tsx` / `LibraryResultView.tsx`)
- Give the result panel `tabIndex={-1}` and move focus to it after the scroll, so keyboard users land where the content appeared.
- Give it `aria-live="polite"` and a heading naming what opened (preset name for video, prompt for image).

## Allowed files
- `apps/web/src/features/library/{LibraryItem,LibraryPage,LibraryResultView,libraryCopy}.tsx|ts`

## Do not touch
- Any hook outside `features/library/`, `api/`, backend files, `imageJobs.ts`, `imageJobHelpers.ts`
- The Create video session-history strip (out of scope; flag in the report if it has the same problem)

## Acceptance checks
- [ ] A selected row is obviously different from a hovered row at a glance (edge + surface + chip)
- [ ] Clicking a row brings the player into view without the user scrolling
- [ ] With `prefers-reduced-motion: reduce`, the scroll jumps instead of animating
- [ ] Video rows show a play glyph on the thumbnail; image rows do not
- [ ] Keyboard: Tab to a row, press Enter — focus lands on the result panel and it is announced
- [ ] No scroll on first page load, even when `?job=<id>` is in the URL
- [ ] lint, test, typecheck, build, check-standards all pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```
Then, with the local stack running and at least one video job and one image job in the Library, screenshot: a hovered row, a selected row, and the page after clicking. Save to `docs/verification/T-040/`.

## Deploying
**A web deploy only counts if the live JS bundle hash changes.** `railway up` exiting 0 and `/api/health/deep` returning 200 prove nothing about the frontend — this exact trap cost us two silent failed deploys today. After deploying from a clean detached worktree, confirm:
```
curl -s https://api-production-8afc.up.railway.app/ | grep -o 'index-[A-Za-z0-9_-]*\.js'
```
differs from the hash before you deployed, and check `railway deployment list` shows SUCCESS. Only then take live screenshots.

## Report
`docs/tasks/T-040/report.md`. Commit by exact path, plain message, no attribution trailers, include `.agent-logs/`.
