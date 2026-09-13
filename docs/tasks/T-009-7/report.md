# Report T-009-7

**Agent / model / tool:** reviewer/implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE, with **one upstream bug found and reported** (not fixed — out of scope): the shared SSE route 404s for image jobs.

## Files changed
- `apps/web/src/App.tsx` (edit, 48 → 36 lines; `+2/−14`): `import { CreateImagePage } from "./features/image-create/CreateImagePage"` and `<Route path="create/image" element={<CreateImagePage />} />`. Every other route and import is untouched.
  - **Forced cleanup, disclosed:** routing `create/image` left `Placeholder` (and its `EmptyState` import) with **no remaining caller** — `credits` already renders `CreditsPage`. `tsc -b` (`noUnusedLocals`) and eslint would both fail on the dead code, so the function and the import were removed. The brief anticipated `Placeholder` might survive "for credits"; it does not.
- `docs/tasks/T-009-7/report.md`: this report (only other file touched).

## Reused
- `CreateImagePage` (T-009-6) as-is; `AppShell` layout route + `outletContext` exactly as before.
- No new dependency and no change to `features/image-create/**`, `api/**`, `ui/**`, the API, contract, migration or adapters.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc -b


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 119 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-Sa38Dsze.css   27.78 kB │ gzip:   5.82 kB
dist/assets/index-iYYxr7L3.js   354.40 kB │ gzip: 108.06 kB

✓ built in 277ms
check-standards: ok (0 violations)
```
`CreateImagePage` is now in the bundle: **119 modules** (vs 103 after spec 007). `tsc -b` is a real gate (and runs again inside `build`).

## Standards check
```
check-standards: ok (0 violations)
```
`App.tsx` = 36 lines; no function over 40 lines.

## End-to-end slice check (evidence)
Environment: `docker compose up -d --wait db` → healthy; `alembic upgrade head` → exit 0; the API on `:8000` (`uvicorn --reload`, which picked up the committed image routes); a worker started as `GENERATION_BACKEND=mock uv run python -m app.worker` — it logged `backend=mock image_backend=mock lease=300s poll=1.0s`. **Per your instruction I used `mock`; the brief's step 4 expected `local-motion`, so the observed `backend` is `"mock"`** (both are T-009-3 placeholder backends; `local-motion` would report `local-motion`). The worker was stopped afterwards and no `app.worker` process remains.

**1. `GET /api/v1/image-options` (public, no cookie):**
```
{"aspect_ratios":["1:1","4:5","3:2","16:9","9:16"],"qualities":["standard","high"],"max_count":4,"credit_costs":{"standard":10,"high":15}}
```

**2. Guest → create → HOLD:**
```
guest HTTP 201
credits BEFORE: {"balance":60}
POST HTTP 202
created: {"id":"1530804c-7b4b-4f6f-b944-a6e8cd7e3f19","status":"queued","credit_cost":20,"image_count":2}
credits AFTER HOLD: {"balance":40}
```

**3. Idempotent repeat:**
```
idempotent repeat: {"id":"1530804c-7b4b-4f6f-b944-a6e8cd7e3f19","status":"queued","credit_cost":20,"image_count":2}
same id? True
credits after repeat (must stay 40): {"balance":40}
```

**4. Terminal read + SETTLE** (SSE subscription attempt failed — see the bug below; progress came through the poll fallback):
```
terminal status: succeeded (after 3 polls)
credits AFTER SETTLE: {"balance":40}
{
    "id": "1530804c-...", "status": "succeeded", "prompt": "a cat", "aspect_ratio": "16:9",
    "quality": "standard", "count": 2, "credit_cost": 20, "backend": "mock",
    "image_urls": [
        "http://localhost:9000/media/users/4b73f16b-.../jobs/1530804c-.../image-1.png?X-Amz-...",
        "http://localhost:9000/media/users/4b73f16b-.../jobs/1530804c-.../image-2.png?X-Amz-..."
    ],
    "error_message": null,
    "created_at": "2026-09-13T17:55:08.189580Z",
    "started_at": "2026-09-13T17:55:09.090250Z",
    "finished_at": "2026-09-13T17:55:09.352352Z"
}
```
Observed progress sequence on a fresh job via rapid polling (the poll fallback the page uses): **`queued -> running -> succeeded`**.

**5. The images are real PNGs** (downloaded from the presigned URL, not a renamed fixture):
```
download HTTP 200 bytes=614840
signature: b'\x89PNG\r\n\x1a\n'
IHDR chunk: b'IHDR'
dimensions: 640 x 360
REAL PNG at 16:9: OK
```
For contrast, the mock fixtures are 242 B (`mock-poster.jpg`) and 2 205 B (`mock-video.mp4`); this is a freshly encoded 614 KB 640×360 PNG.

**6. Video Library discipline (AC-11):**
```
GET /api/v1/jobs items: {"items":[]}
GET /api/v1/jobs/<image_id>       -> HTTP 404
GET /api/v1/image-jobs/<image_id> -> HTTP 200
```

**7. Out of credits:**
```
guest2 HTTP 201 ; credits: {"balance":60}
first  high/4: {"id":"cfdb924e-...","status":"queued","credit_cost":60,"image_count":4} HTTP 202
second high/4: {"detail":"Not enough credits","balance":0,"required":60} HTTP 402
credits after: {"balance":0}
```

**8. `/create/image` is a routable SPA path and the bundle carries the page:**
```
HTTP 200 content-type=text/html; charset=utf-8
/assets/index-iYYxr7L3.js
354402 /tmp/t009-7-bundle.js
Create image                                               1
Describe the image first.                                  1
Demo placeholder images - a real image model ships later.   1
Number of images                                           1
Aspect ratio                                               1
Library                                                    1
```
(The `Add 100 credits` control string is 0 by design — it is a template literal on the Credits page, not a literal in the bundle.)

**Cross-kind idempotency key (recorded, not fixed):** a video job created with key `t009-cross-9` (202), then `POST /image-jobs` with the same key → **422** `{"detail":"Idempotency key already belongs to another job type"}`. This matches T-009-4's report; the contract has no 409 and adding one would break AC-12's byte-identical check.

**No browser pass.** This CLI session has no browser, so step 8 is the accepted curl + bundle-grep substitute; the in-browser AC pass remains for `verify-slice`.

## Cross-check of T-009-1…T-009-6 reports against the code

- **🔴 BUG (running code wins): `GET /api/v1/jobs/{image_id}/events` returns 404, so AC-6's SSE half does not work for image jobs.**
  ```
  GET /api/v1/jobs/<image_id>/events -> HTTP 404  {"detail":"Job not found"}
  ```
  Cause: `routers/jobs.py::stream_job_events` authorises with `read_owned_job(...)` (line 141), and T-009-1 made `find_user_job` filter `Job.kind == "video"` for AC-11. T-009-1's report ("`read_job_status` is deliberately not filtered, so the shared SSE route still streams both kinds") and T-009-4's ("the SSE route is reused unchanged") are **both wrong**: `read_job_status` is unfiltered, but the SSE handler never gets that far — its ownership check 404s first. The design's Flow 5 ("watched via `GET /jobs/{id}/events`") is therefore not met for images. **Impact:** `useImageJob`'s watcher falls back to the 5 s poll, which is why the flow above still completes and shows `queued -> running -> succeeded`; there is simply no live stream. **Suggested fix (not done — out of scope):** give the stream a kind-agnostic owner check (e.g. authorise via `find_job` + `user_id` comparison, or a `find_owned_job` that does not filter `kind`). This is a one-line change in `routers/jobs.py`/`repositories/jobs.py`, but both files are outside this task's allowed list.
- **T-009-1 — confirmed**, including the two disclosed guards. `git diff 9786fdd HEAD -- apps/api/app/services/generation_runs.py` is exactly the guard (`+2/−1`); the migration/repositories/filters behave as reported (an image job is absent from `GET /jobs` and 404s on `GET /jobs/{id}`).
- **T-009-2 — confirmed**: `api/jobStatus.ts` + `api/jobStatusWatcher.ts` exist and `features/create-video/jobStatusWatcher.ts` is deleted.
- **T-009-3 — confirmed**: the generated file is a genuine PNG (`\x89PNG` + `IHDR` 640×360, 614 KB), not a renamed 242 B fixture; `backend` is reported honestly.
- **T-009-4 — confirmed on every count except the SSE claim above** (contract byte-identical, one HOLD per job, idempotent repeat, top-level 402, owner scoping, cross-kind 422).
- **T-009-5 — confirmed**: `services/step_completion.py` has **no diff** vs the T-009-0 commit, and `generation_runs.py`'s only diff is T-009-1's guard — T-009-5 added nothing to either. The image success path writes `output_image` + `job_image` and settles (the ledger shows `HOLD -20` then `SETTLE 0`, balance 40).
- **T-009-6 — confirmed**: the page mounts, reads the options, computes the cost, submits, and renders progress via the watcher's poll fallback; every string comes from `imageCreateCopy` (the bundle grep above).

## Open issues / guesses / things skipped
- **The SSE bug is the headline.** It is reported, not fixed, per the brief's out-of-scope rule. It does not block the demo (the poll fallback works and is proven), but AC-6's "reuse the SSE stream" is only half-true until it is fixed.
- **Forced dead-code cleanup in `App.tsx`** (`Placeholder` + the `EmptyState` import removed). Any editor flagging "touched more than the route" should read this as the minimum change that keeps lint/tsc green.
- **`backend` is `"mock"`, not `"local-motion"`**, because your instruction specified `GENERATION_BACKEND=mock` while the brief's step 4 said `local-motion`. Both select T-009-3's placeholder adapter; the API reports whichever backend ran.
- **Stray shared-DB step:** on startup the worker immediately claimed a leftover `generate_video` step from an earlier test (attempt 2) whose input object is not in MinIO, so it failed with a 404 and released. It was harmless (the reaper/refund path worked) but it is a symptom of the shared dev DB noted in `docs/STATUS.md` BROKEN.
- **No commit** (per the brief) and no stray process left: the worker was stopped and `pgrep -af app.worker` is clean.
- `.agent-logs/` was not written for this task (DSH harness without auto-capture); the orchestrator owns capture and the commit.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Create image assembled: `/create/image` renders `CreateImagePage` (119-module bundle) and the whole slice runs live with `GENERATION_BACKEND=mock` — guest 60 → 202 `{queued, 20, 2}` → balance 40 → `succeeded` with 2 `image_urls` (real 640×360 PNGs downloaded) → SETTLE keeps 40; Library stays video-only; high/4 → 60 then 402. **Known bug: `GET /jobs/{id}/events` 404s for image jobs** (video-only ownership check), so the page relies on the poll fallback | `apps/web/src/App.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → 119 modules, 0 violations; full curl evidence + the SSE 404 + the poll `queued→running→succeeded` sequence in `docs/tasks/T-009-7/report.md` | 2026-09-13 23:26 |
