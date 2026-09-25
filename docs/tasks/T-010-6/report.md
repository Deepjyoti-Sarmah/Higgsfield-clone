# Report T-010-6

**Agent:** Buffy@freebuff (z-ai/glm-5.3-flash) · **Role:** implementer · **Result:** DONE

## Files changed
- `apps/api/app/adapters/ffmpeg_process.py` (new): `run_ffmpeg` (asyncio subprocess, `GenerationError` with user-safe message "Render failed. Your credit was refunded." and the stderr tail as internal detail) and `probe_duration_seconds` via `ffprobe -show_entries format=duration -of csv=p=0`
- `apps/api/app/adapters/stitch_filtergraph.py` (new, pure): `build_stitch_command` — scale/pad/fps normalise chain per input, left fold (`cut`→concat, `crossfade`→`xfade=transition=fade`, `fade_black`→`fadeblack`, each 0.5 s at offset = accumulated − 0.5), audio `apad,atrim=0:T,afade=t=out:st=T-1:d=1` then AAC (or `-an`), output `libx264 -crf 23 -preset veryfast -pix_fmt yuv420p -movflags +faststart`; rejects clips < 1.0 s with `ValueError`; all numbers from `domain/sequence_rules.py`
- `apps/api/app/adapters/ffmpeg_stitcher.py` (new): `stitch_clips` probes each clip, builds/runs the command, extracts the poster at `-ss min(1.0, T/2) -frames:v 1`
- `apps/api/app/repositories/stitch_inputs.py` (new): `load_stitch_inputs` → user_id, clips in position order with source output-video `storage_key`, transitions, `audio_storage_key | None`; `None` when the job is missing/not a sequence/any source video asset is missing
- `apps/api/app/services/stitch_runs.py` (new): `run_stitch_step` mirroring `run_image_step` — temp dir, downloads, `stitch_clips`, uploads `users/{uid}/jobs/{job}/video.mp4` + `poster.jpg` (`video/mp4`, `image/jpeg`), `complete_step_success(..., backend=STITCH_BACKEND, duration_ms=...)`; `complete_step_failure` with the user-safe message on any exception; missing inputs → log and return; races `renew_lease_until_lost`
- `apps/api/app/services/step_completion.py`: added optional `duration_ms: int | None = None` to `complete_step_success`, passed through
- `apps/api/app/repositories/jobs.py`: added optional `duration_ms` field to `transition_job_status`
- `apps/api/app/worker.py`: dispatches `STITCH_STEP_KIND` to `run_stitch_step` in `run_claimed_step_for_kind` (file stays ≤ 200 lines)
- `apps/api/tests/test_stitch_filtergraph.py`, `test_stitch_stitcher.py`, `test_stitch_runs.py` (new, 200 lines)
- `apps/api/tests/test_stitch_runs.py` additionally got a missing `_drain_queued_steps` helper (F821) and was compacted from 207 to 200 lines to satisfy check-standards

## Reused
Lease/renew/failure paths of `run_image_step`; `complete_step_success`/`complete_step_failure`; `transition_job_status`; `GenerationError`; `STITCH_STEP_KIND` and all numeric constants from `domain/sequence_rules.py`. `local_motion_adapter.py` and `modal_adapter.py` untouched (migration logged as follow-up, per brief).

## Verify output (brief's command)
```
db Healthy; alembic upgrade head ok
ruff check . → All checks passed!
mypy → Success: no issues found in 53 source files
pytest -q → 2 failed, 254 passed
  FAILED tests/test_contract_010.py::test_create_returns_501 - assert 404 == 501
  FAILED tests/test_contract_010.py::test_read_returns_501 - assert 404 == 501
  (T-010-1's stub-behavior file, outside Allowed files — not fixed. The T-010-3
  implementation replaced the 501 stubs, so these now 404 by design. Owner of
  that file should expect 404 / 202 / 200.)
scripts/check-standards → ok (0 violations)
```

## ffprobe of one stitched test file
Input: two 2 s lavfi `testsrc` clips (960×544 and 720×1280) joined with `crossfade`, 10 s sine audio:
```
stitch_clips(...) → video_path=/tmp/stitchwork/video.mp4 poster_path=/tmp/stitchwork/poster.jpg duration_ms=3500
ffprobe /tmp/stitchwork/video.mp4:
codec_name=h264
width=1280
height=720
r_frame_rate=24/1
codec_name=aac
r_frame_rate=0/0
duration=3.500000
```
1280×720, 24 fps H.264, AAC audio, total 2+2−0.5 = 3.5 s as designed.

## Acceptance checks (yes/no + evidence)
- [x] yes — image/video step code paths untouched; full suite green except the two T-010-1 stub tests noted above (254 passed, including all image-step tests)
- [x] yes — filtergraph matches design.md; every number (0.5 s xfade, 1.0 s min clip, 1280×720, 24 fps, crf 23, fade timings) comes from `domain/sequence_rules.py`
- [x] yes — every new file ≤ 200 lines (stitch_runs 149, stitch_filtergraph 122, ffmpeg_stitcher 45, ffmpeg_process 60, stitch_inputs 74, test_stitch_runs exactly 200); functions ~40 lines at most
- [x] yes — ruff, mypy, check-standards pass; pytest passes except the out-of-scope T-010-1 stub tests

## Open issues / guesses / things skipped
- The two `test_contract_010.py` failures are pre-existing T-010-3 fallout outside my Allowed files; reported, not fixed.
- `stitch_clips` expects `work_dir` as a `Path` (a `str` raises `TypeError`); tests and `stitch_runs` pass a `Path`. Noted in case another caller appears.
- No commit, no new dependencies. Did not run `scripts/task verify`/`submit` per the handoff instructions (not merged yet).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Worker `stitch_video` step: ffmpeg stitch → 1280×720/24fps mp4 + poster, SETTLE/RELEASE, duration_ms (T-010-6) | `adapters/ffmpeg_{process,stitcher}.py`, `adapters/stitch_filtergraph.py`, `repositories/stitch_inputs.py`, `services/stitch_runs.py`, `worker.py` | ruff+mypy clean, 3 stitch test files green (filtergraph/stitcher/runs), check-standards 0 violations, ffprobe verified | 2026-09-25 |
