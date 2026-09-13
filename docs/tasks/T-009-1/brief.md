# Brief T-009-1: API data — migration `0004`, the image job model, repositories and the video-only filters

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-5, AC-11, AC-12)
- Design: `docs/specs/009-image-create/design.md` §§ **Data** (normative), **API contract**, **Flow 4**
- Existing: `apps/api/app/models/{job,asset,job_step}.py`, `apps/api/app/repositories/{jobs,assets,job_steps}.py`, `apps/api/app/services/job_views.py`, `apps/api/migrations/versions/0002_create_generation_tables.py` (the constraint style to copy), `apps/api/tests/conftest.py`
- Contract: `packages/contracts/openapi.json` — frozen by T-009-0; this task must not change it

## Goal
The database can hold an image job (no preset, no input image, 1–4 outputs) and both P0 video surfaces keep ignoring it.

## Allowed files (touch nothing else)
- `apps/api/migrations/versions/0004_image_jobs.py` (new)
- `apps/api/app/models/job.py`, `apps/api/app/models/asset.py`, `apps/api/app/models/job_image.py` (new)
- `apps/api/app/repositories/jobs.py`, `apps/api/app/repositories/image_jobs.py` (new)
- `apps/api/app/services/job_views.py`
- `apps/api/tests/test_image_job_data.py` (new)
- `docs/tasks/T-009-1/report.md`

## Must do (follow design § Data exactly)
- **Migration `0004_image_jobs`** (additive; the downgrade drops only what it added, and must run on a database that has `0003` applied):
  - `asset`: extend `ck_asset_kind` to `('input_image', 'output_video', 'output_poster', 'output_image')`.
  - `job`: add `kind String(16) NOT NULL server_default 'video'`; add `ck_job_kind` (`kind IN ('video','image')`); make `preset_slug` and `input_asset_id` **nullable**; add `ck_job_inputs_by_kind` — `(kind='video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL) OR (kind='image' AND preset_slug IS NULL AND input_asset_id IS NULL)`; add nullable `aspect_ratio String(8)`, `quality String(16)`, `image_count Integer`; add `ck_job_image_params` — `(kind='image' AND aspect_ratio IS NOT NULL AND quality IS NOT NULL AND image_count BETWEEN 1 AND 4) OR (kind='video' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)`.
  - new table `job_image`: `id` uuid pk `gen_random_uuid()`, `job_id` FK `job.id` `ON DELETE CASCADE` NOT NULL, `position` Integer NOT NULL, `asset_id` FK `asset.id` NOT NULL, `created_at` timestamptz NOT NULL `now()`; `UniqueConstraint("job_id", "position", name="uq_job_image_position")` and `UniqueConstraint("asset_id", name="uq_job_image_asset")`.
  - Keep `ix_job_user_created`, `uq_job_user_idempotency_key`, `uq_job_step_job_kind` and every existing constraint/index untouched.
- **Models** mirror the migration exactly (`Job.kind`/params with the same check names, `Asset` kind check, new `JobImage`). `job.preset_slug`/`input_asset_id` become `Mapped[str | None]`/`Mapped[uuid.UUID | None]`.
- **`repositories/image_jobs.py`** (new; raw SQLAlchemy only, no business rules):
  - `insert_image_job(session, *, user_id, prompt, aspect_ratio, quality, image_count, idempotency_key, credit_cost) -> Job` — writes `kind='image'`, `preset_slug=None`, `input_asset_id=None`, `status='queued'`; `flush()` and return.
  - `insert_job_image(session, *, job_id, position, asset_id) -> JobImage`.
  - `list_job_images(session, job_id) -> list[JobImage]` ordered by `position`.
  - `find_owned_image_job(session, user_id, job_id) -> Job | None` — `kind='image'` and the owner.
- **`repositories/jobs.py`**: add `Job.kind == "video"` to `list_owned_jobs` and to `find_user_job` (so the Library and `GET /jobs/{id}` stay video-only, AC-11). Do **not** change `insert_job`'s signature: it writes a video job and should now also set `kind="video"` explicitly.
- **`services/job_views.py`**: `read_owned_job` returns `None` when the loaded job is not a video job, so `GET /jobs/{id}` answers 404 for an image id instead of failing on a `None` preset.
- **Tests** (`test_image_job_data.py`, ≤200 lines): video jobs still round-trip (the existing `POST /jobs` path from `job_api_helpers`); `insert_image_job` + `insert_job_image` + `find_owned_image_job` work; the new checks reject a video job with a NULL preset, an image job with a preset, `image_count=0/5`, and an image job with NULL params; `GET /api/v1/jobs` and `GET /api/v1/jobs/{id}` do not return an image job (create one directly through the repository); `asset.kind='output_image'` is accepted.

## Acceptance checks
- [ ] `alembic upgrade head` on a `0003` database applies cleanly; a second run is a no-op; `alembic downgrade -1` then `upgrade head` round-trips
- [ ] the fresh-migration test in `tests/test_migrations.py` still passes
- [ ] the Library/read filters are proven by a test (an image job is absent from `GET /jobs` and 404s on `GET /jobs/{id}`)
- [ ] `scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json` → byte-identical (no schema changed)
- [ ] ruff, mypy (strict on the touched services) and the full suite are green

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && scripts/check-standards
```
Stop any running `app.worker` first (it races the shared dev DB — `docs/STATUS.md` BROKEN). `tests/test_lease_reaper.py::test_first_expiry_requeues_then_second_fails_and_refunds` is a known pre-existing flake; if it fails, re-run it alone and say so.

## Out of scope
- The image services/routes (T-009-4), the worker branch (T-009-5), the adapters (T-009-3), any web file.
- Changing `GET /jobs`'s response schema or the Library contract; changing `POST /jobs`'s behaviour for video jobs.

## Report
Write `docs/tasks/T-009-1/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
