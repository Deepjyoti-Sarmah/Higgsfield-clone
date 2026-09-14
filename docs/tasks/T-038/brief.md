# Brief T-038: Image generation has no progress, no result, and never reaches the Library

**Role:** implementer (strong model) · **Blocks the walkthrough — Create image currently looks broken to a user**

## Evidence
The user generated "cat on a mat" on the live site. Worker logs:
```
image generation succeeded ... duration_ms=50497 prompt="cat on a mat " generated_by="modal"
```
**The generation worked.** The page still showed a bare `Queued` and never updated, the image was never displayed, and it does not appear in the Library. Screenshot: the user's 09:24 capture of `/create/image`.

## Three root causes (all confirmed)
1. **No status watching on the image page at all.** `grep -rn "useJobEvents\|EventSource\|jobStatusWatcher\|poll" apps/web/src/features/image-create/` returns **nothing**. The page submits the job, renders a static "Queued", and never checks again. The video page has the full SSE + 5s-poll-fallback machinery; images got none of it.
2. **The Library query excludes images.** `apps/api/app/repositories/jobs.py::list_owned_jobs` filters `Job.kind == "video"`. Image jobs can never appear.
3. **No progress UI parity.** The video page has `JobProgressView` with status and an elapsed timer. The image page has one line of text.

## The work

### A. Wire status watching into the image page (reuse, do not rewrite)
- `apps/web/src/api/jobStatusWatcher.ts` already lives in the shared `api/` folder and has 9 unit tests. The SSE route is already kind-agnostic — see the comment at `apps/api/app/repositories/jobs.py:57`: *"Ownership only, kind-agnostic: the SSE route streams image jobs too."* So `GET /api/v1/jobs/{id}/events` already works for image jobs.
- Reuse `useJobEvents.ts` and `useElapsedSeconds.ts` from `features/create-video/`. If they need to be shared, **move** them to a shared location and update the video imports — do not copy-paste.
- On terminal `succeeded`, fetch `GET /api/v1/image-jobs/{id}` and render the images via the existing `ImageResultGrid.tsx`.
- On `failed`, render the existing `ImageFailureView.tsx` with the refund message.

### B. Progress parity with video
- Queued → Generating → Done, with an elapsed timer, matching `JobProgressView.tsx`'s structure and copy tone. Reuse that component if it fits; extract a shared one only if it genuinely does (rule of two).
- Expect ~50s warm and up to ~200s cold for FLUX, so the waiting state must look deliberate, not hung.

### C. Images in the Library
- **Backend:** make `list_owned_jobs` kind-agnostic (both video and image, newest first).
- **Contract change (intended):** `LibraryItemResponse` currently assumes video — `preset_slug`, `preset_name`, `video_url`. Image jobs have no preset and have `image_urls: list[str]`. Extend it so an item can represent either:
  - add `kind: "video" | "image"`
  - make `preset_slug` / `preset_name` optional
  - add `image_urls: list[str]` (empty for video)
  - `thumbnail_url` = poster for video, first image for an image job
  Regenerate `packages/contracts/openapi.json` and say so in the report.
- **Frontend:** `LibraryItem.tsx` / `LibraryResultView.tsx` must render both kinds — an image job shows its grid, not a video player, and the label shows the prompt instead of a preset name.

## Allowed files
- `apps/api/app/repositories/jobs.py`, `apps/api/app/services/job_views.py`, `apps/api/app/schemas/jobs.py`, `apps/api/app/routers/jobs.py`
- `apps/api/tests/**`, `packages/contracts/openapi.json`
- `apps/web/src/features/image-create/**`, `apps/web/src/features/library/**`
- `apps/web/src/features/create-video/{useJobEvents,useElapsedSeconds,JobProgressView}.tsx|ts` (only if moving them to shared)
- `apps/web/src/api/**` **except** `imageJobs.ts` and `imageJobHelpers.ts` — another agent's in-flight work, never stage or commit those

## Acceptance checks
- [ ] Submitting an image job shows live status (Queued → Generating → Done) with an elapsed timer, driven by SSE with the poll fallback
- [ ] On success the generated images render on the page without a manual refresh
- [ ] On failure the refund message shows
- [ ] `GET /api/v1/jobs` returns both video and image jobs, newest first
- [ ] The Library lists image jobs with a thumbnail, and selecting one shows the images
- [ ] Existing video behaviour is unchanged (its tests still pass)
- [ ] `openapi.json` regenerated; the diff is only the LibraryItem changes

## Verify command (paste full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --stat packages/contracts/openapi.json
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
scripts/check-standards
```
Then deploy from a clean detached worktree (`railway up --path-as-root`, api + worker) and generate ONE real image on the live site end to end, confirming progress → result → Library. Screenshot to `docs/verification/T-038/`.

**Cost limit:** one image job (~$0.06). Do not loop generations.

## Out of scope
Video behaviour changes, new image features (editing, upscale, reference images), pagination, delete.

## Report
`docs/tasks/T-038/report.md`, noting the contract change explicitly. Commit by exact path, plain message, no attribution trailers, include `.agent-logs/`.
