# Brief T-011-6: Clip trim in sequences (API + stitcher)

**Role:** implementer (API/worker) · **Depends on:** T-011-4 merged (both regenerate `openapi.json`) · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md`.

## Goal
Spec 011 AC-6, the backend. Each sequence clip can carry an in and out trim. The stitcher cuts to it before normalising and applying transitions.

## Allowed files
- New: `apps/api/migrations/versions/0009_sequence_trim.py`, `apps/api/tests/test_sequence_trim.py`
- Edit: `app/schemas/sequence_jobs.py`, `app/models/job_sequence_clip.py`, `app/repositories/{sequence_jobs,stitch_inputs}.py`, `app/services/{sequence_job_creation,sequence_job_views,stitch_runs}.py`, `app/adapters/{stitch_filtergraph,ffmpeg_stitcher}.py`, `app/domain/sequence_rules.py`, `packages/contracts/openapi.json`, `apps/web/src/api/generated/schema.d.ts` (both regenerated)
- `docs/tasks/T-011-6/*`

## The change
1. **Contract:**
   - `SequenceClipIn` gains `trim_start_ms: int = 0` and `trim_end_ms: int | None = None` (None means to the end), validated so that 0 ≤ start < end.
   - `SequenceClipResponse` echoes both.
2. **Data (`0009`):** `job_sequence_clip.trim_start_ms INTEGER NOT NULL DEFAULT 0` and `trim_end_ms INTEGER NULL`, with a check `trim_end_ms IS NULL OR trim_end_ms > trim_start_ms`. The downgrade reverses it.
3. **Stitch:**
   - Each input gets `trim=start=S:end=E,setpts=PTS-STARTPTS` before the normalise chain.
   - Clip seconds for the xfade offsets = the trimmed length, where E is clamped to the probed duration.
   - A trimmed clip under 1.0 s → `ValueError` (the existing rule).
   - `MIN_TRIMMED_SECONDS = 1.0` goes in `sequence_rules`.
4. **Tests:**
   - pure filtergraph with trims (the offsets and total use the trimmed lengths);
   - real ffmpeg: two 3 s testsrc clips trimmed to 0.5–2.5 s with a crossfade → ≈ 3.5 s;
   - the API rejects start ≥ end (422);
   - a round trip through create → read echoes the trims.

## Verify command
```
docker compose up -d --wait db minio && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run alembic downgrade 0008 && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && npm --prefix apps/web run gen:api && npm --prefix apps/web run typecheck
```
