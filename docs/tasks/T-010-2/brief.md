# Brief T-010-2: Data for sequences (migration 0007, models, sequence_rules, guest cap)

**Role:** implementer · **Suggested model:** medium · **Depends on:** nothing · **Wave:** W1

## Start here (any harness)
1. `scripts/task claim T-010-2 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md`, and `docs/specs/010-reel-and-still/design.md` § "Data".
3. Read `apps/api/migrations/versions/0004_image_jobs.py`. It's the exact pattern: an additive migration that rewrote the same check constraints for the image kind. Also read `models/job.py`, `models/asset.py` and `models/job_image.py`.
4. Questions: `scripts/task say T-010-2 QUESTION "…"`.

## Goal
The database and ORM can store a sequence job (kind `sequence`, its ordered clips with transitions, an optional audio asset, and its output duration). All the shared sequence constants live in one domain module. The per-IP guest cap is 30.

## Allowed files (touch nothing else)
- `apps/api/migrations/versions/0007_sequences.py` (new; `revision = "0007"`, `down_revision = "0006"`)
- `apps/api/app/models/job.py`, `models/asset.py`, `models/job_sequence_clip.py` (new), `models/__init__.py`
- `apps/api/app/domain/sequence_rules.py` (new), `apps/api/app/domain/credit_rules.py`
- `apps/api/tests/test_sequence_data.py` (new)
- `docs/tasks/T-010-2/report.md`

## The change
1. **Migration `0007_sequences`**, exactly as in design.md § Data:
   - Drop and recreate `ck_job_kind`, `ck_job_inputs_by_kind` and `ck_job_image_params` with the sequence branch.
   - Add `job.audio_asset_id` (FK `asset.id`, nullable) and `job.duration_ms` (int, nullable), each with its check.
   - Recreate `ck_asset_kind` with `'input_audio'`.
   - Create `job_sequence_clip` with its checks, PK and `ix_job_sequence_clip_source_job`.
   - `downgrade()` restores every 0006 constraint verbatim and drops the new column and table.
2. **Models:**
   - `models/job.py`: update the three check-constraint strings (keep the module-level constant style) and add `audio_asset_id` and `duration_ms` with their named checks.
   - `models/asset.py`: add `input_audio` to the kind check.
   - `models/job_sequence_clip.py`: `JobSequenceClip`, mirroring `JobImage`'s style.
   - Export it from `models/__init__.py` if the other models are exported there.
3. **`domain/sequence_rules.py`:** the constants listed in design.md, with one short *why* comment on `STITCH_BACKEND` (it keeps sequences out of paid-spend accounting). Also `SEQUENCE_TRANSITIONS` as a `tuple[str, ...]` and a `Literal` alias `SequenceTransition`, if that helps mypy.
4. **`domain/credit_rules.py`:** `GUEST_PER_IP_DAILY = 30`. Change nothing else.
5. **`tests/test_sequence_data.py`:**
   - A sequence job row with 2 clip rows inserts.
   - A sequence job with `preset_slug` set is rejected (IntegrityError).
   - A video job with `audio_asset_id` set is rejected.
   - `transition_in='wipe'` is rejected; `position=6` is rejected.
   - `duration_ms=0` is rejected.
   - An `input_audio` asset inserts.
   - Deleting a sequence job cascades its clips.

   Reuse the existing DB fixtures and the cleanup style (STATUS mentions the known `test_migrations.py` downgrade interplay; clean up your rows).

## Acceptance checks
- [ ] `alembic upgrade head` then `downgrade 0006` then `upgrade head` all succeed on the dev DB
- [ ] Existing video and image rows still satisfy every constraint (no data change)
- [ ] All the constants exist with the exact names and values in design.md
- [ ] The existing test suite is still green, including `test_migrations.py`
- [ ] ruff, mypy, pytest and check-standards pass

## Verify command
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run alembic downgrade 0006 && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
```
**Shared dev DB:** if another worktree is running pytest at the same time, results can race (STATUS BROKEN). Re-run once before reporting a failure.

## Out of scope
- Repositories, services, routes, the worker (T-010-3, T-010-6), schemas (T-010-1).

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-2`
2. `scripts/task submit T-010-2 --as <you> [--transcript <file>]`
