# Report T-010-2

**Agent:** muse-spark@opencode · **Role:** implementer · **Result:** PARTIAL

## Files changed
- `apps/api/migrations/versions/0007_sequences.py` (new, `revision = "0007"`, `down_revision = "0006"`): 0004-patterned upgrade/downgrade — recreated `ck_job_kind`/`ck_job_inputs_by_kind`/`ck_job_image_params` with the sequence branch, added `audio_asset_id` (FK `asset.id`) + `duration_ms` with `ck_job_audio_sequence_only`/`ck_job_duration_positive`, recreated `ck_asset_kind` with `input_audio`, created `job_sequence_clip` (PK `(job_id, position)`, `ix_job_sequence_clip_source_job`); downgrade restores the 0006 strings verbatim
- `apps/api/app/models/job.py`: the three check strings gained the sequence branch (module-constant style kept), new `JOB_AUDIO_CHECK`/`JOB_DURATION_CHECK` constants + named constraints, `audio_asset_id`/`duration_ms` columns
- `apps/api/app/models/asset.py`: kind check gains `input_audio`
- `apps/api/app/models/job_sequence_clip.py` (new): `JobSequenceClip` in `JobImage` style (composite PK, CASCADE on `job_id`, position/transition checks, source index)
- `apps/api/app/domain/sequence_rules.py` (new): all design constants verbatim plus typed `SEQUENCE_TRANSITIONS`/`SequenceTransition` and the `STITCH_BACKEND` why-comment
- `apps/api/app/domain/credit_rules.py`: `GUEST_PER_IP_DAILY` 5 → 30, nothing else
- `apps/api/tests/test_sequence_data.py` (new, 192 lines, 8 tests): insert with 2 clips, preset/audio/transition/position/duration rejections, `input_audio` insert, delete-cascades-clips; ledger-style user-row cleanup
- `models/__init__.py`: untouched (empty — no models are exported there)

## Reused
- `0004_image_jobs.py` as the migration pattern; `JobImage` as the model style; `test_ledger_repository.py` user-row cleanup pattern; `insert_asset`-equivalent inline ORM inserts

## Verify output (brief's command, full signal)
```
docker compose up -d --wait db → Healthy
alembic upgrade head → ok; downgrade 0006 → ok; upgrade head → ok
ruff check . → All checks passed!
mypy → Success: no issues found in 47 source files
pytest -q → 1 failed, 236 passed
  FAILED tests/test_guardrails.py::test_sixth_guest_from_one_ip_is_rate_limited
    (creates 5 guests, expects the 6th → 429; with cap 30 the 6th → 201.
    That file is outside Allowed files — not fixed. Owner: loop 30, expect the 31st blocked.)
check-standards → 1 pre-existing violation (below)
```
Separately: `pytest tests/test_sequence_data.py tests/test_migrations.py` → 9 passed; constants assertion script → ok.

## Standards check
```
apps/api/tests/test_share_api.py: 204 lines (max 200)
check-standards: FAIL (1 violations)
```
That file is pre-existing (204 lines on HEAD, untouched by this task — `git diff --name-only` confirms). All files touched here pass.

## Acceptance checks (yes/no + evidence)
- [x] yes — `upgrade head` → `downgrade 0006` → `upgrade head` all succeed in the verify run above
- [x] yes — no data change (additive checks/columns only); video/image library/job/share tests all pass in the suite run
- [x] yes — assertion script checks every design name/value incl. `GUEST_PER_IP_DAILY == 30` → `constants ok`
- [ ] no — 236 passed, 1 failed: `test_guardrails.py` pins the old cap of 5 (file out of scope, reported above)
- [x] yes for ruff/mypy/my tests/check-standards-on-my-files; suite-wide pytest and repo-wide check-standards are red only on the two pre-existing/out-of-scope items above

## Open issues / guesses / things skipped
- PARTIAL solely for the guardrails test + pre-existing share length violation; every in-scope item is done. `models/__init__.py` export skipped deliberately (file is empty).
- No commit made; no packages installed.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Sequence data layer (T-010-2 PARTIAL: guardrails test pins old cap 5) | `migrations/versions/0007_sequences.py`, `models/job_sequence_clip.py`, `domain/sequence_rules.py` | verify chain: alembic up/down/up ok, ruff+mypy clean, `test_sequence_data.py` 8 passed | 2026-09-25 |

## Orchestrator follow-up (Claude Opus 5.5, 2026-09-25)
- Blocker 1 fixed: `tests/test_guardrails.py` now reads `GUEST_PER_IP_DAILY` instead of pinning 5 (test renamed `test_guest_past_the_daily_ip_cap_is_rate_limited`).
- Blocker 2 fixed: the orchestrator's T-010-1 follow-up had pushed `tests/test_share_api.py` to 204 lines; `PUBLIC_KEYS` is now written on 4 lines. `check-standards` is clean.
