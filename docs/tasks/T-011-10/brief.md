# Brief T-011-10: Fix the five T-011-8 live findings

**Role:** implementer (web) · **Depends on:** — · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`, then `docs/verification/T-011-8/report.md` (the findings, with job ids and screenshots).

## Allowed files
- `apps/web/src/features/image-create/*`, `apps/web/src/features/studio/{StageActions,StudioStage,StudioPage}.tsx`, `apps/web/src/features/credits/*`, `apps/web/src/features/share/*` (+ tests)
- `docs/tasks/T-011-10/*`

## Findings to fix (each must get a regression test where it's pure logic)
1. **F1 (medium): the chosen aspect ratio is ignored.** Two live stills made with "Portrait" were stored as `aspect_ratio: "1:1"` (jobs f2ed03d3, 0e2acc4f). The Still composer's submit sends the default settings, not the selected ones. Find where the request body is built (`stillSubmit.ts` / `useStillSubmit.ts` / `useStillSettings.ts` / `StillComposer.tsx`) and send the selected aspect, quality and count. Test: the body builder gets the selected aspect ratio.
2. **F2: face-swap results have no "Animate this".** Treat a succeeded `faceswap` item like a still in `StageActions` (Animate this + Use as face swap target), taking the first image.
3. **F3: after a second still succeeded, the stage didn't show "Use as face swap target"** until a reload of `?item=`. Make sure the stage's actions derive from the refreshed Library item (the one found by `selectedId`), not a stale copy. Check `StudioPage`/`StudioStage` for a memoised or stale item. Explain the root cause in the report.
4. **F4: the credits popover ignores Escape.** Escape must close it and return focus to the button (DESIGN.md §4).
5. **F5: the share caption says "1 stills".** Pluralise correctly ("1 still", "2 stills") everywhere the count is shown. Test the formatter.

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```
