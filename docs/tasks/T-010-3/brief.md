# Brief T-010-3: Sequence API (create with HOLD, validation and idempotency; read)

**Role:** implementer · **Suggested model:** medium/strong (touches the credit ledger) · **Depends on:** T-010-1, T-010-2 merged · **Wave:** W2

## Start here (any harness)
1. `scripts/task claim T-010-3 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md`, and `docs/specs/010-reel-and-still/design.md` § "API contract" and § "Flow → Create a sequence".
3. **Read the pattern you are mirroring, line by line:** `services/image_job_creation.py`, `repositories/image_jobs.py`, `routers/image_jobs.py`, `services/image_job_views.py`. Your code should read like a sibling of those files.
4. Questions: `scripts/task say T-010-3 QUESTION "…"`.

## Goal
`POST /api/v1/sequence-jobs` creates a sequence job with exactly one HOLD of 1 credit, one `stitch_video` step and ordered clip rows, all in one transaction. `GET /api/v1/sequence-jobs/{id}` returns it. Both replace the T-010-1 stubs.

## Allowed files (touch nothing else)
- `apps/api/app/repositories/sequence_jobs.py` (new)
- `apps/api/app/services/sequence_job_creation.py` (new)
- `apps/api/app/services/sequence_job_views.py` (new)
- `apps/api/app/routers/sequence_jobs.py` (replace the stub bodies; keep the signatures and `responses=`)
- `apps/api/tests/test_sequence_jobs_api.py` (new; split into two files if it passes 200 lines)
- `docs/tasks/T-010-3/report.md`

## Must reuse (do not re-implement)
- `lock_user_row`, `find_job_by_idempotency_key`, `enforce_creation_limits`, `InsufficientCreditsError`, `hold_amount`, `insert_ledger_entry`, `sum_user_balance`, `insert_job_step` and `notify_job_event`.
- `IdempotencyKeyConflictError`, imported from `services/image_job_creation.py`.
- `find_user_asset` for the audio asset. `build_asset_url` (as `image_job_views` uses it) for URLs.
- The constants from `domain/sequence_rules.py`: `SEQUENCE_CREDIT_COST`, `STITCH_STEP_KIND`, `MIN_CLIPS`/`MAX_CLIPS`.

## The change
1. **`repositories/sequence_jobs.py`:**
   - `insert_sequence_job(session, *, user_id, audio_asset_id, idempotency_key, credit_cost) -> Job` (kind `sequence`, status `queued`)
   - `insert_sequence_clips(session, job_id, clips: list[tuple[uuid.UUID, str]])`: position = index, and `clips[0]`'s transition is forced to `"cut"`
   - `find_clip_source_jobs(session, user_id, job_ids) -> dict[uuid.UUID, Job]`: the user's own jobs only
   - `find_owned_sequence_job(session, user_id, job_id) -> Job | None`
   - `list_sequence_clips(session, job_id) -> list[tuple[JobSequenceClip, uuid.UUID | None]]`: each clip plus its source job's `output_poster_asset_id`, ordered by position
2. **`services/sequence_job_creation.py`:** `create_sequence_job(session, user_id, *, clips, audio_asset_id, idempotency_key) -> SequenceJobCreation`, following design.md's Flow steps 2–6 exactly. Errors:
   - `SequenceClipNotFoundError` (a clip id that isn't the user's) → 404
   - `SequenceClipIneligibleError(job_id, reason)` (not `video`, not `succeeded`, or no output video) → 422
   - `AudioAssetNotFoundError` (not the user's, not `input_audio`, or not `ready`) → 404

   Keep the IntegrityError race handling from the image path. The replay of a `sequence` key returns the same job with no second HOLD.
3. **`services/sequence_job_views.py`:** `read_owned_sequence_job(...) -> SequenceJobResponse | None`. It fills `clips[].thumbnail_url` from the source posters, `has_audio`, `video_url`/`poster_url` (only when the job succeeded and the assets are ready), `duration_ms`, `generated_by` and `error_message`.
4. **`routers/sequence_jobs.py`:** thin. Parse, call the service, then map the errors:
   - 404 / 422 / 402 (the `InsufficientCreditsResponse` body, as image jobs do) / 429 (the same `_limit_response` shape as `routers/image_jobs.py`, and the same wording);
   - GET 404 when the job isn't found or isn't the user's.

   If you need `_limit_response`/`_insufficient_credits_response` and they are private in `routers/image_jobs.py`, **don't import private helpers**. Write the tiny equivalents in your router and note it in the report, since moving them is out of scope.
5. **Tests** (`test_sequence_jobs_api.py`), each through the HTTP API with the existing client and guest fixtures. For source clips, insert succeeded video jobs the way existing tests do, or through repositories.
   - [ ] Creating with 2 succeeded clips → 202; exactly one HOLD of −1; one `stitch_video` step; clip rows at positions 0 and 1; the first transition is stored as `cut`
   - [ ] The same idempotency key → the same id, still one HOLD
   - [ ] A key that belongs to an image job → 422
   - [ ] Another user's clip → 404; a queued clip → 422; an image job as a clip → 422
   - [ ] An audio asset that isn't `input_audio` → 404
   - [ ] Balance 0 → 402 with `balance`/`required`, and no job row
   - [ ] The daily cap reached → 429
   - [ ] GET own → 200 with clips in order and thumbnail URLs; GET another user's → 404

## Acceptance checks
- [ ] One transaction per create; no HOLD without a job and no job without a HOLD
- [ ] No private helper imported across modules; files ≤ 200 lines; names follow STANDARDS
- [ ] `openapi.json` unchanged (the contract was published in T-010-1)
- [ ] ruff, mypy, pytest and check-standards pass

## Verify command
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
```

## Out of scope
- The worker or ffmpeg (T-010-6), the Library/share fields (T-010-4), any web code.

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-3`
2. `scripts/task submit T-010-3 --as <you> [--transcript <file>]`
