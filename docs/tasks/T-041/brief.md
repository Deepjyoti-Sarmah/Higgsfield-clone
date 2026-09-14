# Brief T-041: Session history tiles give almost no feedback (same defect as T-040, Create video)

**Role:** implementer (small/medium model) · **Visual + interaction only, no data or API changes**
**Follows T-040**, which fixed the equivalent problem in the Library. Read `docs/tasks/T-040/report.md` first and match its treatment so the two surfaces feel like one product.

## The problem
`apps/web/src/features/create-video/SessionHistoryStrip.tsx`:
1. **The active tile's only signal is a 2px border** — `border-accent` when active, `border-transparent` otherwise.
2. **There is no hover state at all**, so the tiles do not read as clickable.
3. **The caption is `text-muted` whether active or not.**
4. **Clicking scrolls nothing and moves no focus.** The canvas it updates sits *above* the strip, so on a short viewport the thing that changed can be off-screen upward — the click appears to do nothing.
5. **No play affordance** on tiles whose job succeeded.

## The fix (mirror T-040's approach, scaled to a 96px tile)

**Active tile** — more than one signal, since the tiles are small:
- `border-accent` **plus** `ring-2 ring-accent/40`
- The caption becomes `text-text font-medium` instead of `text-muted`
- No "Viewing" chip here — the tile is too small; the ring plus the caption weight carries it

**Hover / focus** — currently nothing:
- `hover:border-border` on the tile frame plus a subtle brightness lift, so an unselected tile visibly responds
- Keep the existing `focus-visible:outline` as it is

**Play glyph:**
- On tiles with `entry.status === "succeeded"`, a small play triangle bottom-right over a soft scrim, `aria-hidden="true"`
- The existing status dot for queued/running/failed stays where it is

**Scroll + focus on open** (`CreateVideoPage.tsx`):
- When the active job changes **because a history tile was clicked**, scroll the canvas into view and move focus to it — the same pattern T-040 used for the Library result panel
- Reuse the existing `usePrefersReducedMotion` hook (already in `features/create-video/`), `behavior: "auto"` when reduced motion is set
- Only on an actual change caused by a click — never on mount, and never when the canvas is already fully visible
- Use `preventScroll` on `focus()` so it does not double-scroll, as T-040 did

## Allowed files
- `apps/web/src/features/create-video/{SessionHistoryStrip,CreateVideoPage,CreateVideoCanvas,createVideoCopy}.tsx|ts`

## Do not touch
- Any hook, `api/`, backend files, the Library feature, `imageJobs.ts`, `imageJobHelpers.ts`

## Acceptance checks
- [ ] An active tile is obviously distinct from an inactive one (border + ring + caption weight)
- [ ] An unselected tile visibly responds to hover
- [ ] Succeeded tiles show a play glyph; queued/running/failed keep their status dot
- [ ] Clicking a tile brings the canvas into view without the user scrolling, and focus lands there
- [ ] With `prefers-reduced-motion: reduce` the scroll jumps rather than animating
- [ ] No scroll on first mount
- [ ] The strip still scrolls horizontally with no page-level horizontal scroll at 390px
- [ ] lint, test, typecheck, build, check-standards all pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```
Screenshot an inactive strip, a hovered tile and an active tile into `docs/verification/T-041/`.

**Local guest cap:** generating several jobs to populate the strip may exhaust the local 5/day cap, as it did in T-040. If that happens, say so in the report rather than resetting the rate-limit table — verifying the effect logic by reading it is an acceptable substitute, exactly as T-040 did.

## Deploying
A web deploy only counts if the **live JS bundle hash changes**. Build the clean worktree standalone first (`npm ci && npm run build`) to catch any uncommitted-import failure, then deploy, then confirm `railway deployment list` shows SUCCESS *and* the live hash differs from `index-BmE4QhRj.js`. Exit code 0 and a green health check prove nothing about the frontend.

## Report
`docs/tasks/T-041/report.md`. Commit by exact path, plain message, no attribution trailers, include `.agent-logs/`.
