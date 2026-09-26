# UX fixes applied (spec 012 foundation: T1–T5)

Spec 012 opens with no prior tasks of its own; T6 (video-target face swap) builds on the five
spec-011 face-swap/trim tasks below, all live and verified 2026-09-26. Condensed from each
task's `docs/tasks/<T>/report.md` (+ `verify.log`).

## T1 — T-011-3: face-swap endpoint on Modal (GPU)

- **Changed:** `apps/gpu/face_swap.py` (new; app `higgsfield-face-swap`, L4, bearer-auth POST
  `{source_url, target_url}` → `{image_base64, width, height, seconds}`, 422 on no-face);
  `apps/gpu/face_swap_core.py` (new; face-picking, square-box crop, feathered paste-back, 70/30
  GFPGAN blend); `apps/gpu/tests/test_face_swap_core.py` (13 unit tests).
- **Verify:** 13 passed, `check-standards` ok; live cold 19.9 s / warm 6.5–7.2 s per swap, 401 on
  missing bearer, `NoFaceError` on a faceless landscape. Deployed endpoint recorded in report.
  Licence note: inswapper/buffalo_l are non-commercial research licences (see DECISIONS D-016).

## T2 — T-011-4: face swap jobs (contract, data, create/read, worker step)

- **Changed:** migration `0008_face_swap.py` + `models/job.py` (`faceswap` kind, source/target FKs,
  checks); `domain/faceswap_rules.py` (`FACESWAP_CREDIT_COST=8`, step `swap_face`); schemas, repo,
  `services/faceswap_job_creation.py` (lock → idempotency → limits → HOLD → notify),
  `services/faceswap_job_views.py`, `adapters/face_swap_adapter.py` (422 detail verbatim),
  `services/faceswap_runs.py`, `routers/faceswap_jobs.py`, `main.py`, `worker.py`, `settings.py` +
  `.env.example`, Library/share still-shape mapping, regenerated `openapi.json` + `schema.d.ts`
  (diff: only the two new paths + `JobKind`); 3 minimal out-of-brief web fixes for the widened
  `JobKind`; new `tests/test_faceswap_{jobs_api,step,library}.py`.
- **Verify:** 271 pytest passed, ruff + mypy clean, alembic upgrade/downgrade/upgrade, openapi
  export, web codegen + `tsc -b`, `check-standards` ok. RESULT: PASS.

## T3 — T-011-5: face swap tab in the studio (web)

- **Changed:** `api/faceswapJobs.ts` (submit outcomes) + `api/jobProgress.ts` (polls the new GET);
  `StudioTab` gains `"faceswap"`, fourth composer tab, `seedTarget`/`consumeSeedTarget` mirroring
  the clip seed pattern, "Use as face swap target" stage action; new `features/face-swap/*`
  (composer, wells, upload hooks, actions, copy, cost); `GenerationBadge`/`StageProgress` widened
  to `"faceswap"` (removing T2's `badgeKind()` workaround); rail title "Face swap".
- **Verify:** lint + 100 vitest (9 new) + typecheck + build + `check-standards` all pass.
  RESULT: PASS. No imports from `features/create-video/*` (verified by grep).

## T4 — T-011-6: clip trim in sequences (API + stitcher)

- **Changed:** `domain/sequence_rules.py` (`MIN_TRIMMED_SECONDS=1.0`); `SequenceClipIn` gains
  `trim_start_ms`/`trim_end_ms` + validator; `models/job_sequence_clip.py` + migration `0009`;
  repos, creation/views pass-through; `stitch_runs.py` → `ffmpeg_stitcher`/`stitch_filtergraph.py`
  (per-input `trim=…setpts` prefix, trimmed-length total); regenerated contract; mechanical
  `sequenceDraftView.ts` + test-fixture updates for typecheck; new `tests/test_sequence_trim.py` (5).
- **Verify:** `scripts/task verify` green (pytest incl. a real-ffmpeg trimmed-crossfade duration
  test, ruff, mypy, openapi byte-check, `check-standards`). RESULT: PASS.

## T5 — T-011-7: trim UI, tool links, start-page showcase hooks (web)

- **Changed:** `SequenceDraftClip` gains `durationMs`/`trimStartMs`/`trimEndMs` + `setTrim` through
  `draftOps.ts`/`useSequenceDraft.ts`; new `TrimControls.tsx` (0.5 s steppers + mono readout);
  `SequenceStrip` renders trims per clip; `ClipPicker` uses Library durations; top bar gains a
  `Face swap` tool link (`/studio?tab=faceswap`); draft/sequence tests extended (clamp, totals,
  payload); one-line out-of-brief `StudioPage.tsx` fix for the new required field.
- **Verify:** lint + typecheck + test + build + `check-standards` all pass. RESULT: PASS.
  (Showcase content itself was split to T-011-9; T-011-10 fixed the T-011-8 live findings;
  full 7/7 live re-check in T-011-11 — spec 011 DONE.)
