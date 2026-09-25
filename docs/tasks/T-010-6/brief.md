# Brief T-010-6: Worker `stitch_video` step (normalise, transitions, music, poster)

**Role:** implementer · **Suggested model:** medium/strong (worker and lease path) · **Depends on:** T-010-2 merged · **Wave:** W2

## Start here (any harness)
1. `scripts/task claim T-010-6 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md`, and `docs/specs/010-reel-and-still/design.md` § "Flow → Render" (the filtergraph recipe is there).
3. **Read the pattern you are mirroring:**
   - `services/image_generation_runs.py`: its lease handling (`generate_with_lease`), its failure path and its logging are the model.
   - `services/generation_runs.py` `complete_run`: the upload keys.
   - `services/step_completion.py`, `repositories/jobs.py` `transition_job_status`, `worker.py` `run_claimed_step_for_kind`.
   - `adapters/local_motion_adapter.py`: how ffmpeg is run today.
4. Questions: `scripts/task say T-010-6 QUESTION "…"`.

## Goal
A claimed `stitch_video` step turns a sequence job's clips (plus optional music) into one 1280×720, 24 fps H.264 mp4 with a poster. It uses the existing lease, success (SETTLE) and failure (RELEASE) paths, and records `generated_by="ffmpeg"` and `duration_ms`.

## Allowed files (touch nothing else)
- `apps/api/app/adapters/ffmpeg_process.py` (new)
- `apps/api/app/adapters/stitch_filtergraph.py` (new)
- `apps/api/app/adapters/ffmpeg_stitcher.py` (new)
- `apps/api/app/repositories/stitch_inputs.py` (new)
- `apps/api/app/services/stitch_runs.py` (new)
- `apps/api/app/services/step_completion.py`: add an optional `duration_ms: int | None = None` to `complete_step_success`, passed through; nothing else
- `apps/api/app/repositories/jobs.py`: add an optional `duration_ms` to `transition_job_status`'s optional fields; nothing else
- `apps/api/app/worker.py`: dispatch `STITCH_STEP_KIND` to `run_stitch_step`
- `apps/api/tests/test_stitch_filtergraph.py`, `test_stitch_stitcher.py`, `test_stitch_runs.py` (new)
- `docs/tasks/T-010-6/report.md`

**Do not** modify `local_motion_adapter.py` or `modal_adapter.py`. Migrating them onto `ffmpeg_process` is a logged follow-up.

## The change
1. **`adapters/ffmpeg_process.py`:**
   - `async run_ffmpeg(args: list[str]) -> None` runs `ffmpeg -y -hide_banner -loglevel error …` via `asyncio.create_subprocess_exec`. On a non-zero exit it raises `GenerationError` (from `adapters/model_adapter.py`) with user message "Render failed. Your credit was refunded." and the stderr tail as the internal detail.
   - `async probe_duration_seconds(path) -> float` uses `ffprobe -v error -show_entries format=duration -of csv=p=0`.
2. **`adapters/stitch_filtergraph.py`:** pure, with no I/O: `build_stitch_command(clip_paths, clip_seconds, transitions, audio_path, output_path) -> tuple[list[str], float]`, following design.md exactly.
   - The normalise chain applies to every input.
   - The left fold: `cut` → concat; `crossfade` → `xfade=transition=fade`; `fade_black` → `xfade=transition=fadeblack`. Each xfade is 0.5 s at offset = accumulated length − 0.5.
   - Audio: `apad,atrim=0:T,afade=t=out:st=T-1:d=1`, then AAC. With no audio, `-an`.
   - Output: `libx264 -crf 23 -preset veryfast -pix_fmt yuv420p -movflags +faststart`.
   - Return the argv (without the leading `ffmpeg`) and the total length in seconds.
   - Reject a clip shorter than 1.0 s with `ValueError`.
   - Take all numbers from `domain/sequence_rules.py`.
3. **`adapters/ffmpeg_stitcher.py`:** `async stitch_clips(clip_paths, transitions, audio_path, work_dir) -> StitchResult(video_path, poster_path, duration_ms)`. It probes each clip, builds and runs the command, then extracts the poster (`-ss min(1.0, T/2) -frames:v 1 poster.jpg`).
4. **`repositories/stitch_inputs.py`:** `load_stitch_inputs(session, job_id) -> StitchInputs | None`. It returns `user_id`, the clips ordered by position (each with its source job's output-video `storage_key`), the transitions, and `audio_storage_key | None`. It returns `None` if the job is missing, not a sequence, or any source video asset is missing.
5. **`services/stitch_runs.py`:** `run_stitch_step(session_maker, *, storage, claimed, worker_id, settings)`.
   - Mirror `run_image_step`: set the log context, run in a temp dir, and race the stitch against `renew_lease_until_lost`.
   - Download the clips and audio, then stitch.
   - Upload to `users/{uid}/jobs/{job}/video.mp4` and `poster.jpg` (`video/mp4`, `image/jpeg`).
   - Then `complete_step_success(..., backend=STITCH_BACKEND, duration_ms=...)`.
   - On `GenerationError` or any other exception, call `complete_step_failure` with the user-safe message.
   - Missing inputs → log and return, as the image path does.
6. **`worker.py`:** in `run_claimed_step_for_kind`, `if claimed.kind == STITCH_STEP_KIND: await run_stitch_step(...); return`. Keep the file ≤ 200 lines.
7. **Tests:**
   - **`test_stitch_filtergraph.py`** (pure): 2 clips with a cut; 3 clips with crossfade + fade_black (check the offsets and the total `5+5+5−0.5−0.5`); audio present versus absent (`-an`); a clip under 1 s raises.
   - **`test_stitch_stitcher.py`** (real ffmpeg): generate inputs with lavfi `testsrc`, one 2 s clip at 960×544 and one 2 s at 720×1280, plus a 1 s and a 10 s `sine` audio file.
     - With crossfade: output 1280×720, 24 fps, duration ≈ 3.5 s (±0.15).
     - Short audio: an audio stream is present and the duration equals the video's.
     - No audio: no audio stream.
     - The poster file exists.
     - Skip with a clear reason if `ffmpeg` isn't on PATH.
   - **`test_stitch_runs.py`:** follow the existing image-run test pattern. It must cover:
     - a success writes the output assets, `succeeded`, `SETTLE`, `generated_by="ffmpeg"` and `duration_ms`;
     - an ffmpeg failure writes `failed`, a `RELEASE` of 1 and the user-safe message;
     - a lost lease writes nothing.

## Acceptance checks
- [ ] No change to the behaviour of video or image steps (their tests stay green)
- [ ] The filtergraph matches design.md; the numbers come from `sequence_rules`
- [ ] Every new file ≤ 200 lines; functions ~40 lines at most
- [ ] ruff, mypy, pytest and check-standards pass

## Verify command
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
```

## Out of scope
- Sequence create/read routes (T-010-3), the contract, web.

## Finish
Write `report.md`. Include the `ffprobe` output of one stitched test file. Then:
1. `scripts/task verify T-010-6`
2. `scripts/task submit T-010-6 --as <you> [--transcript <file>]`
