# Brief T-011-5: Face swap tab in the studio

**Role:** implementer (web) · **Depends on:** T-011-4 merged · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md` and `DESIGN.md`.

## Goal
Spec 011 AC-5, the UI. A fourth composer tab, **Face swap**, takes a face image and a target image and starts a face-swap job. The result shows on the stage like a still.

## Allowed files
- New: `apps/web/src/features/face-swap/*` (composer, copy, hooks, tests), `apps/web/src/api/faceswapJobs.ts` (+test)
- Edit: `apps/web/src/api/studioContracts.ts` (add `"faceswap"` to `StudioTab`; add an optional `FaceSwapSeed` if needed), `apps/web/src/features/studio/{ComposerTabs,StudioStage,StageActions,railItemTitle,StudioPage}.tsx|ts`, `apps/web/src/api/jobProgress.ts` (a faceswap path), `apps/web/src/features/share/*` (a faceswap renders like a still), `apps/web/src/ui/GenerationBadge.tsx` (label `modal-faceswap` "Face swap")
- `docs/tasks/T-011-5/*`

## The change
1. **`FaceSwapComposer({ onJobStarted, seedTarget })`:**
   - Two image wells, **Face** ("the face to use") and **Target** ("the picture to put it in"). Each takes an upload (reuse `useImageUpload` via `api/`, or the pattern in `features/create-video/useImageUpload.ts`; don't import create-video internals, move shared bits to `api/` per STANDARDS) or a seeded still.
   - `Swap face · 8 credits` in mono, with a visible disabled reason until both are ready.
   - 202 → `onJobStarted(id)`. 402 → `openCredits()`. 422/404 → an inline message. 429 → the limit message.
2. **Stage:**
   - Faceswap items render like stills.
   - For a **still** item, add **"Use as face swap target"** to StageActions: switch to the faceswap tab with the target seeded. Hold the seed inside the composer, **not** from the parent prop, and learn from `useClipInput`'s held-seed fix.
   - Rail titles for faceswap: "Face swap".
3. **Progress:** `fetchJobForProgress("faceswap", id)` → `GET /api/v1/faceswap-jobs/{id}`.
4. **Copy** follows DESIGN.md §9. The tab label is "Face swap".
5. **Tests** (pure): the request body, the disabled reasons, and the job progress path for faceswap.

## Acceptance checks
- [ ] The whole flow works against a local API (a fake adapter is fine locally); a screenshot of the composer at 1440 and 390
- [ ] `grep -rn "create-video/" apps/web/src/features/face-swap` → nothing (no cross-feature internals)

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```
