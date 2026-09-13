---
session_id: b48f72ef
date: 2026-09-13
author: Deepjyoti-Sarmah
model: deepseek-flash
tool: dsh
project: higgsfield-rebuild
total_exchanges: 2
---

# Session Log - 2026-09-13 · T-009-0 design spec 009 Create image + contract (hand-exported from DSH)

DSH (deepseek-flash) transcript for the T-009-0 orchestrator/designer turn: the user prompt, the scope clarification and the assistant's messages. Tool calls and reasoning are omitted; text is verbatim. Exported by the running session at commit time, per the convention recorded in `docs/STATUS.md` § BROKEN (the Claude Code hooks do not cover this harness).

---

[LOG_ENTRY type=PROMPT num=1 session=b48f72ef]
model: user

--- A1: Spec 009 (Create image, P1) design ---
You are the ORCHESTRATOR/DESIGNER for spec 009 (Create image). Read AGENTS.md,
docs/STANDARDS.md, docs/playbooks/spec-new.md, docs/research/flows/image-create.md,
docs/research/product-map.md (row "Image create: prompt + aspect/quality/count → images" = P1),
docs/specs/003-generation-core/design.md (the job/asset/ledger core it must reuse) and
docs/specs/004-create-video/design.md (the page conventions).
GOAL: design the /create/image page (currently a Placeholder) — prompt + aspect/quality/count
→ image job, reusing the existing job/credit/SSE plumbing. Note the backend reality honestly:
there is no image model adapter today (local-motion is video-only), so the design must say
what GENERATION_BACKEND produces an image (a new mock/image adapter, or Gate it to P2 if the
adapter is out of reach) — do not promise a model you cannot run.
DELIVER docs/specs/009-image-create/{spec,design,tasks}.md + docs/tasks/T-009-*/brief.md,
contract additions only if a new route is truly needed, verify with the openapi-paths +
ls T-009 + check-standards triple, commit plain.

--- A2: P1 polish backlog (pick one per session) ---
Each is small, agent-runnable, and spec-backed:
1. Library pagination/delete (spec 005 § out of scope → P1): `?limit` paging + a delete route.
2. Live progress in the Library: reuse the spec-004 SSE watcher for queued/running items.
3. Permanent media route: OG images/videos currently expire with the 1 h presigned URLs.
4. `share_token` revocation (spec 007 § "worth your eye").

[LOG_ENTRY type=PROMPT num=2 session=b48f72ef]
model: user

(scope answer) selected: A1 only (Recommended) — Spec 009 spec/design/tasks + T-009 briefs + any contract additions + commit; A2 stays the standing backlog for a later session.

[LOG_ENTRY type=RESPONSE num=1 session=b48f72ef]
model: deepseek-flash

Read the required sources fresh, then read the implementation the design has to extend: `models/{job,asset,job_step}.py`, `ModelAdapter`/`backend_selection`/`mock`/`local_motion`, `services/{generation_runs,step_completion,job_creation}.py`, the credits/ledger core, `App.tsx`, and the spec-004 page/watcher. Three findings shaped the pack:

1. **The image path is absent at every layer, not just the adapter.** `ModelAdapter` exposes only `generate_video`; `job.preset_slug` and `job.input_asset_id` are `NOT NULL`; `asset.kind` has no `output_image`; `generation_runs`/`step_completion` hard-code `video.mp4 + poster.jpg`. So a real slice needs one additive migration (`job.kind` + per-kind checks, nullable video-only columns, image params, a `job_image` child table) plus a new asset kind — not a small polish change.
2. **No image model can run here.** D-002's LLaDA-Image Turbo on Modal is blocked on an unverified licence, no GPU deployment and the R2 blocker. The design therefore adds an `ImageModelAdapter` port with a deterministic **PNG placeholder** for `local-motion`/`mock` (a real PNG file, so upload/serve/view are exercised for real), returns the `backend` in the response, captions placeholder results in the UI, and keeps `modal`/`openrouter` failing with a refund. Real text→image is P2. **D-014** records this; nothing claims a model we cannot run.
3. **Two pre-existing limits forced clean splits.** `generation_runs.py` is 181 lines and `image_generation_runs` needs its `renew_lease_until_lost`, so the dispatch goes in `worker.py` (no cycle, no 200-line overrun) and `generation_runs.py`/`step_completion.py` stay untouched. The spec-004 `jobStatusWatcher.ts` is 197 lines, so the shared move extracts `isTerminalJobStatus` into `api/jobStatus.ts` and makes the watcher generic over the job type — one SSE implementation for video, image and the future Library.

Delivered: `docs/specs/009-image-create/{spec,design,tasks}.md`; `docs/tasks/T-009-{1..7}/brief.md`; the contract (`domain/image_rules.py`, `schemas/image_jobs.py`, the three 501 stubs in `routers/image_jobs.py`, `main.py`, regenerated `openapi.json`). A third route (`GET /api/v1/image-options`, public) is justified in the design: the Generate button must show the cost before the POST and the cost depends on user-chosen settings, so the server publishes the allowed values and unit costs instead of the client duplicating money maths.

[LOG_ENTRY type=RESPONSE num=2 session=b48f72ef]
model: deepseek-flash

Verify triple (also pasted in `docs/tasks/T-009-0/report.md`):

```
$ python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/credits/topup
/api/v1/image-jobs
/api/v1/image-jobs/{job_id}
/api/v1/image-options
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/public/jobs/{job_id}
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete

$ ls docs/tasks | grep T-009
T-009-0 … T-009-7

$ scripts/check-standards
check-standards: ok (0 violations)
```

Contract discipline: `git diff --numstat packages/contracts/openapi.json` → `451 0`; a structural diff against `HEAD` shows added paths `['/api/v1/image-jobs', '/api/v1/image-jobs/{job_id}', '/api/v1/image-options']`, added schemas `['ImageCreditCosts', 'ImageJobCreateRequest', 'ImageJobCreatedResponse', 'ImageJobResponse', 'ImageOptionsResponse']`, and **0 changed pre-existing paths and 0 changed pre-existing schemas**. Live stub probe: `GET /image-options` → 501, no-cookie `POST /image-jobs` → 401, guest POST/GET → 501, `aspect_ratio: "2:1"` → 422.

Syncing `docs/PLAN.md` (T-009-0 ticked + T-009-1..7 rows), `docs/STATUS.md`, `docs/WORKLOG.md` and `docs/DECISIONS.md` (D-014), then committing the T-009-0 change set with a plain message.
