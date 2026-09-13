# Report T-009-1

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH Web) — not wrapped by `scripts/agent-run`
**Result:** DONE (with one disclosed, user-approved out-of-list change — see below)

## Files changed
- `apps/api/migrations/versions/0004_image_jobs.py` (new): the additive migration. `asset`: recreate `ck_asset_kind` with `output_image`. `job`: add `kind` (`NOT NULL`, `server_default 'video'`) + `ck_job_kind`; add nullable `aspect_ratio`/`quality`/`image_count` + `ck_job_image_params`; make `preset_slug`/`input_asset_id` nullable + `ck_job_inputs_by_kind`. New `job_image` table (`uq_job_image_position`, `uq_job_image_asset`, `job_id` FK `ON DELETE CASCADE`). The downgrade reverts exactly those objects.
- `apps/api/app/models/job.py` (edit): `kind`/params columns and the three checks (the check SQL mirrors the migration as module constants); `preset_slug`/`input_asset_id` are now `Mapped[.. | None]`.
- `apps/api/app/models/asset.py` (edit): `ck_asset_kind` gains `output_image`.
- `apps/api/app/models/job_image.py` (new): the `JobImage` model.
- `apps/api/app/repositories/jobs.py` (edit): `insert_job` writes `kind="video"`; `find_user_job` and `list_owned_jobs` filter `Job.kind == "video"` (AC-11). `read_job_status` is deliberately **not** filtered, so the shared SSE route still streams both kinds.
- `apps/api/app/repositories/image_jobs.py` (new): `insert_image_job`, `insert_job_image`, `list_job_images`, `find_owned_image_job` — raw SQLAlchemy, no business rules.
- `apps/api/app/services/job_views.py` (edit): `read_owned_job` returns `None` for a non-video/param-less job; `list_owned_jobs_view` narrows per job and passes `preset_slug` explicitly to `_library_item_view`; `_referenced_asset_ids` skips a `None` input id.
- `apps/api/app/services/share_views.py` + `apps/api/app/services/generation_runs.py` (edit — **out of the brief's list, approved by the user mid-task**): see "Disclosed deviation".
- `apps/api/tests/test_image_job_data.py` (new, 191 lines): 9 tests.
- `docs/tasks/T-009-1/report.md`: this report.

## Reused
- `repositories/assets.insert_asset`/`find_assets_by_ids`, `repositories/job_steps.insert_job_step` (for T-009-4), `repositories/presets.find_active_preset`, the `AsyncSession`/`session_maker`/`guest_client`/`other_guest_client` fixtures, `job_api_helpers.create_queued_job`/`current_user_id`, and the alembic + fixture style of `0002_create_generation_tables.py`.
- The existing `ix_job_user_created`, `uq_job_user_idempotency_key`, `ck_job_status` and every other pre-existing constraint/index — untouched.

## Verify output (full paste, no summarising)
```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Running 
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
docker exit=0
alembic exit=0
All checks passed!
ruff exit=0
Success: no issues found in 32 source files
mypy exit=0
........................................................................ [ 50%]
......................................................................   [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
142 passed, 2 warnings in 53.51s
pytest exit=0
wrote packages/contracts/openapi.json
export exit=0
contract-diff exit=0
check-standards: ok (0 violations)
standards exit=0
```
`142 passed` = the 133 before this task + my 9. `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` exited **0** — the migration changed no schema. The `test_migrations.py` downgrade→upgrade test ran inside that suite, so `0004`'s downgrade is exercised too.

DB shape actually applied (evidence, `alembic_version = 0004`):
```
job checks: ck_job_image_params, ck_job_inputs_by_kind, ck_job_kind, ck_job_status
ck_asset_kind: ... 'input_image','output_video','output_poster','output_image'
job_image constraints: job_image_pkey, job_image_job_id_fkey, job_image_asset_id_fkey,
                       uq_job_image_position, uq_job_image_asset
job nullability: kind=NO, preset_slug=YES, input_asset_id=YES, aspect_ratio=YES,
                 quality=YES, image_count=YES
```

## Standards check
```
check-standards: ok (0 violations)
```
Sizes: migration 91 lines, `models/job.py` 74, `models/job_image.py` 31, `repositories/image_jobs.py` 67, `tests/test_image_job_data.py` 191 — all ≤200. `mypy --strict` green (32 files).

## Acceptance checks
- [x] `alembic upgrade head` on a `0003` DB applied cleanly; a re-run is a no-op; `downgrade -1` → `upgrade head` round-trips (`test_migrations.py` + the migration ran in the chain above).
- [x] the Library/read filters are proven: `test_an_image_job_is_hidden_from_the_library_and_the_video_read` (an image job is absent from `GET /jobs` and **404s** on `GET /jobs/{id}`), while `test_a_video_job_still_round_trips_through_the_api` keeps the video path green.
- [x] `scripts/export-openapi && git diff --exit-code` → byte-identical.
- [x] ruff, mypy (32 files) and the full suite green.
- [x] the checks reject a video job without preset/input, an image job with a preset, `image_count` 0/5 and an image job with NULL params — each asserted with `pytest.raises(IntegrityError)`; `asset.kind='output_image'` is accepted by `_insert_output_image`.

## Disclosed deviation (agreed with the user mid-task)
The brief allows only a fixed file list, but making `job.preset_slug`/`input_asset_id` nullable necessarily breaks every reader of those columns, and `mypy` failed in **two files outside the list**. I asked the user and they approved adding the guards:
- `services/share_views.py`: `read_public_job` now returns `None` when `preset_slug is None`. This is a **correctness fix, not just a typing fix** — otherwise `GET /api/v1/public/jobs/{image_id}` would have built a `PublicJobView(preset_name=None)` and 500'd in pydantic; it now 404s, and the `/v/{id}` HTML route falls back to the generic meta it already handles. (The public share page stays video-only, spec 007.)
- `services/generation_runs.py`: `load_step_inputs` returns `None` when the input asset or preset is missing, so the video loader is defensive (an image step is dispatched away from it by T-009-5).
Both are 1-line guards plus a why-comment. **The design's Files table and T-009-5's "generation_runs.py is untouched" claim should be updated by the orchestrator** to list `services/share_views.py` and `services/generation_runs.py` as T-009-1 edits.

## Open issues / guesses / things skipped
- **`read_job_status` deliberately keeps no kind filter**, so `GET /jobs/{id}/events` continues to stream image jobs (the design reuses it for AC-6). Only the owner-scoped *read* and the Library list are video-only.
- **The downgrade fails if image jobs exist** (`preset_slug`/`input_asset_id` go back to `NOT NULL`). That is normal for an additive migration and is what the round-trip test exercises on a clean DB; note it for the deploy runbook.
- **Concurrency note:** while I was working, another session's untracked `apps/web/src/api/imageJobs.ts` briefly pushed the **repo-wide** `scripts/check-standards` to a failure (219 lines). It was theirs (T-009-2) and they fixed it; the green run above is with their file at ≤200. My own test file was 204 lines on the first run and I trimmed it to 191 with a `_image_job_fields` helper.
- **No commit** (per the brief). No web file, no service, no route and no adapter was touched by this task.
- The known `test_lease_reaper` flake did **not** fire this run.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Image job data foundation: migration `0004` (job `kind` + `ck_job_kind`/`ck_job_inputs_by_kind`/`ck_job_image_params`, nullable `preset_slug`/`input_asset_id` + `aspect_ratio`/`quality`/`image_count`, `output_image` asset kind, `job_image` table) and the image repositories; the Library (`GET /jobs`) and the owner read (`GET /jobs/{id}`) stay video-only while the SSE route still serves both kinds | `apps/api/migrations/versions/0004_image_jobs.py`, `apps/api/app/models/{job,asset,job_image}.py`, `apps/api/app/repositories/{jobs,image_jobs}.py`, `apps/api/app/services/{job_views,share_views,generation_runs}.py`, `apps/api/tests/test_image_job_data.py` | `docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards` → 142 passed (9 new), mypy clean (32 files), contract byte-identical, 0 violations | 2026-09-13 23:10 |
