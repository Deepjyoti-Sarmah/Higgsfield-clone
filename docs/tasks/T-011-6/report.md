# Report T-011-6

**Agent:** sonnet-5@claude-code · **Role:** implementer (API/worker) · **Result:** DONE

## Files changed
- `apps/api/app/domain/sequence_rules.py`: added `MIN_TRIMMED_SECONDS = 1.0`.
- `apps/api/app/schemas/sequence_jobs.py`: `SequenceClipIn` gains `trim_start_ms` (default 0, `ge=0`) and
  `trim_end_ms` (optional, `ge=1`), with a `model_validator` enforcing `trim_end_ms > trim_start_ms`.
  `SequenceClipResponse` echoes both.
- `apps/api/app/models/job_sequence_clip.py`: `trim_start_ms` (INTEGER NOT NULL DEFAULT 0),
  `trim_end_ms` (INTEGER NULL), check constraint `ck_job_sequence_clip_trim`.
- `apps/api/migrations/versions/0009_sequence_trim.py`: new migration, `down_revision = "0008"`,
  adds the two columns and the check constraint; downgrade reverses it.
- `apps/api/app/repositories/sequence_jobs.py`: `insert_sequence_clips` takes
  `(source_id, transition, trim_start_ms, trim_end_ms)` tuples.
- `apps/api/app/repositories/stitch_inputs.py`: `StitchClipInput` carries `trim_start_ms`/`trim_end_ms`
  through to the worker.
- `apps/api/app/services/sequence_job_creation.py`: passes the new fields into `insert_sequence_clips`.
- `apps/api/app/services/sequence_job_views.py`: echoes the trims on `SequenceClipResponse`.
- `apps/api/app/services/stitch_runs.py`: builds a `trims` list and forwards it to `stitch_clips`.
- `apps/api/app/adapters/stitch_filtergraph.py`: `build_stitch_command` takes an optional
  `trims: list[tuple[int, int | None]] | None = None` (defaults to old behaviour so the existing,
  out-of-scope `tests/test_stitch_filtergraph.py` still passes unchanged); each input gets a
  `trim=start=S[:end=E],setpts=PTS-STARTPTS` prefix before `NORMALISE_CHAIN` when trims are given.
  `MIN_CLIP_SECONDS` replaced by the shared `MIN_TRIMMED_SECONDS`.
- `apps/api/app/adapters/ffmpeg_stitcher.py`: `stitch_clips` takes the same optional `trims` param
  (old callers/tests unaffected), computes trimmed length per clip clamped to the probed duration.
- `apps/api/tests/test_sequence_trim.py` (new, 5 tests): pure filtergraph trim-prefix + offset test, a
  below-minimum-after-trim `ValueError` test, a real-ffmpeg trimmed-crossfade duration test, a
  `trim_start_ms >= trim_end_ms` -> 422 test, and a create->read round trip that echoes the trims.
- `packages/contracts/openapi.json`, `apps/web/src/api/generated/schema.d.ts`: regenerated.
- `apps/web/src/features/sequence/sequenceDraftView.ts`: `SequenceClipPayload` gains
  `trim_start_ms: number` and `trim_end_ms: number | null`; `toPayloadClips` fills them with
  `0` / `null` (trim isn't editable yet; T-011-7 adds the UI). Mechanical, approved by the
  coordinator to unblock `npm run typecheck` (recorded on `scripts/task show T-011-6`).
- `apps/web/src/api/sequenceJobs.test.ts`: `CLIPS` fixture literals gain
  `trim_start_ms: 0, trim_end_ms: null`. Same approval, mechanical, no behaviour change.

## Reused
- Existing `NORMALISE_CHAIN`, `_fold_segment`, `probe_duration_seconds`, `run_ffmpeg`, and the
  `test_stitch_stitcher.py` / `test_sequence_jobs_api.py` helper patterns (`build_sequence_body`,
  `create_succeeded_clip`) - the new test file imports the latter two rather than duplicating them.

## Verify: see `verify.log` (written by `scripts/task verify`); paste only the RESULT line and anything notable
```
uv --directory apps/api run alembic upgrade head / downgrade 0008 / upgrade head  -> ok
uv --directory apps/api run ruff check .   -> All checks passed!
uv --directory apps/api run mypy           -> Success: no issues found in 60 source files
uv --directory apps/api run pytest -q      -> 282 passed, 3 warnings
scripts/export-openapi                     -> wrote packages/contracts/openapi.json
npm --prefix apps/web run gen:api          -> ok
npm --prefix apps/web run typecheck        -> ok (after the two mechanical consumer fixes above)
RESULT: PASS
```

ffprobe of the trimmed crossfade output (two 3s testsrc clips, both trimmed to 0.5s-2.5s,
`cut` then `crossfade`, matching AC-6), showing the expected 3.5s total:
```
StitchResult(duration_ms=3500)
[STREAM] width=1280 height=720 r_frame_rate=24/1 duration=3.500000 nb_frames=84
[FORMAT] format_name=mov,mp4,m4a,3gp,3g2,mj2 duration=3.500000 probe_score=100
```
(`tests/test_sequence_trim.py::test_trimmed_crossfade_output_duration` asserts the same thing via
`stitch_clips` and passes as part of the 282.)

## Standards check
```
check-standards: ok (0 violations)
```

## Acceptance checks (spec 011 AC-6)
- Clip carries an in/out trim: yes - `SequenceClipIn.trim_start_ms` / `trim_end_ms`, persisted on
  `job_sequence_clip`, echoed on `SequenceClipResponse`.
- `0 <= start < end` validated: yes - pydantic `ge`/`model_validator` (422 on violation) and a DB
  check constraint as a second line of defence.
- Stitcher cuts to the trim before normalising/transitions: yes - `trim=...,setpts=PTS-STARTPTS`
  is prepended to `NORMALISE_CHAIN` per input.
- Offsets/total use trimmed length, `end_ms` clamped to probed duration: yes -
  `_trimmed_seconds` in `ffmpeg_stitcher.py`.
- Trimmed clip under `MIN_TRIMMED_SECONDS` (1.0s) -> `ValueError`: yes, same rule as before,
  now named for trims and shared from `sequence_rules`.

## Open issues / guesses / things skipped
- None outstanding. The web-typecheck blocker (consumers requiring `trim_start_ms`/`trim_end_ms`
  literals) was raised as a QUESTION mid-task, approved by the coordinator, and resolved with the
  two mechanical edits listed above.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Sequence clip trim (API + ffmpeg stitcher) | `apps/api/app/adapters/stitch_filtergraph.py`, `apps/api/migrations/versions/0009_sequence_trim.py` | `scripts/task verify T-011-6` | 2026-09-26 |
