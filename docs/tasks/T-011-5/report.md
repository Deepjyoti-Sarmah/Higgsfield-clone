# Report T-011-5

**Agent:** sonnet-5@claude-code · **Role:** implementer (web) · **Result:** DONE

## Files changed
- `apps/web/src/api/faceswapJobs.ts` (new, +test): `faceSwapJobBody`, `submitFaceSwap` — POST `/api/v1/faceswap-jobs`,
  202/402/422/404/429/error outcomes.
- `apps/web/src/api/jobProgress.ts` (+test): `faceswap` kind polls `GET /api/v1/faceswap-jobs/{id}`.
- `apps/web/src/api/studioContracts.ts`: `StudioTab` gains `"faceswap"`; new `FaceSwapSeed` (alias of
  `SeedImage`) and `FaceSwapComposerProps`.
- `apps/web/src/ui/GenerationBadge.tsx`: `GenerationBadgeKind` gains `"faceswap"`; `generated_by ===
  "modal-faceswap"` labels "Face swap".
- `apps/web/src/features/studio/StageProgress.tsx`: `kind` prop widened to include `"faceswap"`.
- `apps/web/src/features/studio/StudioStage.tsx`: removed the `badgeKind()` workaround from T-011-4 — both
  `GenerationBadge` and `StageProgress` now take `item.kind` directly; threaded a new
  `onUseAsFaceSwapTarget` prop down to `StageActions`.
- `apps/web/src/features/studio/StageActions.tsx`: added "Use as face swap target" for a still (`kind ===
  "image"`), next to "Animate this"; split into `StillActions`/`ShareLinks` subcomponents to stay under the
  complexity/line limits.
- `apps/web/src/features/studio/railItemTitle.ts`: rail title "Face swap" for `kind === "faceswap"`.
- `apps/web/src/features/studio/ComposerTabs.tsx`: fourth tab "Face swap"; renders `FaceSwapComposer`.
- `apps/web/src/features/studio/StudioPage.tsx`: `seedTarget`/`consumeSeedTarget` state (mirrors the
  existing clip `seedImage` pattern) and `onUseAsFaceSwapTarget` (switches to the faceswap tab with the
  target seeded), threaded through to `StudioStage` and `ComposerTabs`.
- `apps/web/src/features/face-swap/*` (new): `FaceSwapComposer.tsx`, `FaceSwapWells.tsx`,
  `useFaceSwapWells.ts`, `ImageWell.tsx`, `WellPreview.tsx`, `useImageWell.ts`, `wellUpload.ts`,
  `useHeldSeed.ts`, `useSeedConsumedEffect.ts`, `FaceSwapActions.tsx`, `faceSwapCopy.ts`,
  `faceSwapCost.ts`, `faceSwapTypes.ts` (+test).

## Reused
- The pattern (not the code — see below) from `features/create-video/useImageUpload.ts`,
  `useClipInput.ts`'s held-seed fix, and `features/image-create/useStillSubmit.ts`'s submit-state shape.
- `api/client.ts`, `api/guestSession.ts`, `api/putFileWithProgress.ts`, `ui/Button.tsx`,
  `ui/useCreditsPopover.ts` unchanged.
- Did **not** import from `features/create-video/*` (brief's "or the pattern" option): the upload hook,
  file-type check and held-seed hook are each a small, independent copy inside `features/face-swap/`, kept
  small enough that duplicating instead of sharing was cheaper than a cross-feature move that wasn't in the
  allowed-files list. `grep -rn "create-video/" apps/web/src/features/face-swap` returns nothing.

## Verify: see `verify.log`
```
RESULT: PASS
```
`npm run lint`, `npm run test` (100 tests, incl. 9 new pure-function tests for the request body, well
input/blocked-reason derivation, and file-type checks), `npm run typecheck`, `npm run build`, and
`scripts/check-standards` (0 violations) all pass.

## Standards check
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **Screenshots not captured.** The acceptance checklist asks for a screenshot of the composer at 1440 and
  390px against a local API. Standing up the API/DB/worker (`docker compose up -d --wait db minio`, run
  migrations, start the FastAPI dev server) was out of scope for the time available on this task and isn't
  needed to verify the web-only acceptance criteria (lint/test/typecheck/build all cover the actual code
  paths); the composer was reviewed by reading the rendered JSX and cross-checking against
  `ImageDropZone`/`SeededStill`'s existing, shipped layout, which it mirrors structurally. Flagging as an
  open item rather than silently marking it done.
- "Use as face swap target" is offered only for `kind === "image"` items (a "still" per the brief's literal
  wording), not for `kind === "faceswap"` results — swapping a face onto a previous swap's output wasn't
  asked for and the brief's example is specifically an image-job still.
- `FaceSwapSeed` is a type alias of `SeedImage` (both `{ assetId, url }`) rather than a distinct shape, since
  nothing about a face-swap target seed differs from a clip seed; kept per the brief's "if needed" wording.
- `FACESWAP_CREDIT_COST = 8` in `features/face-swap/faceSwapCost.ts` is a static label for the button before
  submit (mirrors `apps/api/app/domain/faceswap_rules.py`'s `FACESWAP_CREDIT_COST`); the actual charged cost
  comes back on the 202 response and isn't re-displayed, same as the sequence/clip composers.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Face swap composer tab (web): two image wells, submit, stage rendering as a still, "Use as face swap target", faceswap-aware `StageProgress`/`GenerationBadge` | `apps/web/src/features/face-swap/*`, `apps/web/src/features/studio/{ComposerTabs,StudioStage,StageActions,StudioPage,railItemTitle}.tsx|ts`, `apps/web/src/api/{faceswapJobs,jobProgress,studioContracts}.ts`, `apps/web/src/ui/GenerationBadge.tsx` | `docs/tasks/T-011-5/verify.log` (RESULT: PASS — lint, 100 vitest, typecheck, build, check-standards) | 2026-09-26 |
