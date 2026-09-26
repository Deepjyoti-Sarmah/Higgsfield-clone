# Brief T-011-9: Real showcase on the start page

**Role:** implementer (web, visual) · **Depends on:** `docs/tasks/T-011-7/showcase.json` existing on main (written by the T-011-8 live run) · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md` and `DESIGN.md` §5.

## Goal
Spec 011 AC-7, split out of T-011-7. The start page shows real outputs of the fixed pipeline, not test patterns or preset stand-ins.

## Allowed files
- `apps/web/src/api/webMedia.ts`, `apps/web/src/features/start/*` (+tests)
- `docs/tasks/T-011-9/*`, `docs/verification/T-011-9/*`

## The change
1. Read `showcase.json` (keys: `still`, `clip`, `faceswap`, `sequence`, `clip_poster`, `sequence_poster`). Add them to `webMedia.ts` as one typed `SHOWCASE` constant. Keep the existing constants if other code still uses them.
2. The start page's three steps use: Still → `still`; Clip → `clip` (muted, looped, `motion-safe` autoplay, `clip_poster` as the poster); Sequence → `sequence` (with `sequence_poster`).
3. Add a compact showcase row under the steps, with four items: still, clip, face swap, sequence. Use DESIGN.md §5's layout rules: a 2fr/1fr/1fr grid or a horizontal scroll row, never three equal cards. Each item gets a one-line mono caption (e.g. `clip · dolly in · 0:05`, `face swap`, `2 shots · 0:07`).
4. If any URL fails to load, the item falls back to its poster or hides itself. The page never breaks.
5. Test (pure): the showcase config has all four items, with captions.

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```
Evidence: screenshots of `/` at 1440 and 390 (vite dev) in `docs/verification/T-011-9/`.
