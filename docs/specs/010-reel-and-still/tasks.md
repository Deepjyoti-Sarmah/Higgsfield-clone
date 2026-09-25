# Tasks 010: Reel & Still

Rules:
- One task = one agent run, in its own worktree (`scripts/task claim`).
- No two tasks in the same wave write the same file (checked against design.md § Files).
- **Sequential hand-offs, each through a merged commit:**
  - `routers/sequence_jobs.py` and `routers/credits.py` get stubs in T-010-1; T-010-3 and T-010-4 fill the bodies.
  - `repositories/sequence_jobs.py` is created in T-010-3; T-010-4 may add `count_clips_by_job`.
- Every task has one verify command (the first fenced block under `## Verify command` in its brief).
- A task gets its `status` file (`open`) only once its dependencies are **accepted and merged**. Until then it is not on the board.

**Waves:**
- W1: T-010-1 ∥ T-010-2 ∥ T-010-5
- W2: T-010-3 ∥ T-010-6 ∥ T-010-7
- W3: T-010-4 ∥ T-010-9 ∥ T-010-10 ∥ T-010-11
- W4: T-010-8
- W5: T-010-12, then T-010-13 (orchestrator)

**Cut line:** T-010-1, 2, 5, 7, 8 and 10 are the must-ship set: identity, the studio, create, share. Sequences (3, 6, 9) come next. Credits (4, 11) and docs (12) follow.

- [x] **T-010-0** · Spec, design, `DESIGN.md`, tasks and briefs (orchestrator)
- [x] **T-010-1** · Contract: the new and changed schemas, the sequence and ledger 501 stubs, `main.py`, regenerate `openapi.json`
  - Files: `apps/api/app/schemas/{sequence_jobs,credits,jobs,uploads,share}.py`, `apps/api/app/routers/{sequence_jobs,credits}.py`, `apps/api/app/main.py`, `packages/contracts/openapi.json`, `apps/web/src/api/generated/schema.d.ts`, `apps/api/tests/test_contract_010.py`
  - Suggested model: small/medium · Depends on: —
- [x] **T-010-2** · Data: migration `0007`, models, `sequence_rules`, guest cap raised to 30
  - Files: `apps/api/migrations/versions/0007_sequences.py`, `apps/api/app/models/{job,asset,job_sequence_clip,__init__}.py`, `apps/api/app/domain/{sequence_rules,credit_rules}.py`, `apps/api/tests/test_sequence_data.py`
  - Suggested model: medium · Depends on: —
- [x] **T-010-3** · Sequence API: create (HOLD, validation, idempotency) and read
  - Files: `apps/api/app/repositories/sequence_jobs.py`, `apps/api/app/services/{sequence_job_creation,sequence_job_views}.py`, `apps/api/app/routers/sequence_jobs.py`, `apps/api/tests/test_sequence_jobs_api.py`
  - Suggested model: medium/strong (money path) · Depends on: T-010-1, T-010-2
- [x] **T-010-4** · API additions: still → clip input, audio uploads, the ledger read, Library and share fields
  - Files: `apps/api/app/services/{job_creation,uploads,credits,job_views,library_media,share_views,share_html}.py`, `apps/api/app/repositories/{ledger,sequence_jobs}.py` (add-only), `apps/api/app/routers/credits.py`, `apps/api/tests/test_api_additions_010.py`
  - Suggested model: medium · Depends on: T-010-3
- [x] **T-010-5** · Design tokens, fonts, brand, top bar, UI primitives
  - Files: `apps/web/index.html`, `apps/web/src/styles.css`, `apps/web/src/ui/*`, `apps/web/public/favicon.svg`
  - Suggested model: medium (visual) · Depends on: —
- [x] **T-010-6** · Worker: the `stitch_video` step (ffmpeg normalise, transitions, music, poster)
  - Files: `apps/api/app/adapters/{ffmpeg_process,stitch_filtergraph,ffmpeg_stitcher}.py`, `apps/api/app/repositories/{stitch_inputs,jobs}.py`, `apps/api/app/services/{stitch_runs,step_completion}.py`, `apps/api/app/worker.py`, `apps/api/tests/test_stitch_{filtergraph,stitcher,runs}.py`
  - Suggested model: medium/strong (worker path) · Depends on: T-010-2
- [x] **T-010-7** · The studio: routes, redirects, rail, stage, tab host, sequence-draft state
  - Files: `apps/web/src/App.tsx`, `apps/web/src/features/studio/*`, `apps/web/src/api/{studioContracts,jobProgress}.ts`, `apps/web/src/ui/{CreditsPopoverContext.tsx,usePrefersReducedMotion.ts}`, a `features/start/StartPage.tsx` stub + the moved `groupPresetsByCategory`; deletes `apps/web/src/features/{library,explore}/*`
  - Suggested model: medium/strong · Depends on: T-010-1, T-010-5
- [x] **T-010-8** · Still and Clip composers: compact, "Animate this" seeding, backend captions
  - Files: `apps/web/src/features/{image-create,create-video}/*`, the Still/Clip swap in `features/studio/ComposerTabs.tsx`, removing the `--animate-hf-*` aliases from `styles.css`
  - Suggested model: medium · Depends on: T-010-4, T-010-7, T-010-9 (both edit `ComposerTabs.tsx`; T-010-9 creates `api/putFileWithProgress.ts`)
- [x] **T-010-9** · Sequence tab: strip, transitions, music, eligibility, render and progress
  - Files: `apps/web/src/features/sequence/*`, `apps/web/src/api/{sequenceJobs,audioUpload,putFileWithProgress}.ts` (+ tests), the `SequencePlaceholder` swap in `features/studio/ComposerTabs.tsx`
  - Suggested model: medium/strong · Depends on: T-010-3, T-010-7
- [x] **T-010-10** · Start page and share viewer
  - Files: `apps/web/src/features/{start,share}/*`
  - Suggested model: medium (visual) · Depends on: T-010-7
- [x] **T-010-11** · Credits button and popover with the ledger
  - Files: `apps/web/src/features/credits/*`, `apps/web/src/api/{ledger,credits}.ts` (+ tests), the one `creditsSlot` line in `App.tsx`
  - Suggested model: small/medium · Depends on: T-010-4, T-010-7
- [x] **T-010-12** · Docs and smoke: the D-015 decision, WALKTHROUGH, README brand, `scripts/smoke-sequence`
  - Files: `docs/DECISIONS.md`, `docs/WALKTHROUGH.md`, `README.md`, `scripts/smoke-sequence`
  - Suggested model: small · Depends on: T-010-3, T-010-6, T-010-9
- [ ] **T-010-13** · Deploy and verify-slice live (orchestrator)
  - Deploy gate: the live bundle hash changes, then `scripts/smoke-sequence` against the public URL, then `verify-slice` screenshots in both themes at 390 and 1440px
