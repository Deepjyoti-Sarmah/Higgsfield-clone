# Brief T-013: real `ModalAdapter` behind the frozen `ModelAdapter` protocol

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spike that already produced a real clip: `apps/gpu/ltx_spike.py`, report in `docs/tasks/T-012/report.md`
- Reference implementation of "provider call → poll → download bytes to disk":
  `pixovid/apps/backend/src/lib/openrouter.ts` (read for shape only; it is TypeScript, do not copy code)
- Port you must satisfy unchanged: `apps/api/app/adapters/model_adapter.py`
- Current stub: `apps/api/app/adapters/modal_adapter.py`
- Worker path that calls the port: `apps/api/app/services/generation_runs.py`
- Design: `docs/specs/003-generation-core/design.md` § Modal backend

## Goal
Replace the `modal` stub with a real adapter that asks `apps/gpu/ltx_spike.py` (deployed once)
for a clip and writes it to the local `work_dir` as `video_path` + `poster_path`, so the worker
uploads it through the existing `ObjectStorage` exactly as `local-motion` does. No contract change.

## Facts the spike establishes (verified, do not re-litigate)
- The GPU function is `generate_clip(image_url, prompt) -> {r2_key, load_seconds, generate_seconds}`.
- One clip is ~**340 s generate + ~28 s load** on A10G; the full call is ~**6 min**.
- The function needs a **publicly reachable image URL** — the worker already passes
  `GenerationRequest.input_image_url` (a presigned storage URL). Use it; do not re-upload.
- The spike uploads to R2 itself. The worker will re-upload what you hand back, so either
  (a) return bytes/a local file from the GPU function and have the adapter download them, or
  (b) return the `r2_key` and fetch it back via storage. (a) is simpler and is preferred.
- `GenerationResult` needs **both** `video_path` and `poster_path`; poster = frame 1 of the mp4.

## Allowed files (touch nothing else)
- `apps/api/app/adapters/modal_adapter.py`
- `apps/gpu/ltx_spike.py` (only to add a bytes/URL return path for the adapter; keep the spike entrypoint)
- `apps/api/app/settings.py` (add the timeout/endpoint fields you need — names only in `.env.example`)
- `.env.example`
- `apps/api/tests/test_modal_adapter.py` (new) and, only if needed, `apps/api/tests/test_backend_selection.py`
- `docs/tasks/T-013/{brief,report}.md`, `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`
- `.agent-logs/*T-013*`

## Must reuse
- `GenerationRequest` / `GenerationResult` from `apps/api/app/adapters/model_adapter.py` — do not edit them.
- `BackendNotConfiguredError` for the unconfigured path (T-014 depends on this exact failure).
- `app.adapters.local_motion_adapter`'s ffmpeg/`ffprobe` helpers pattern for the poster frame;
  extract a small shared helper only if the rule of two is met (STANDARDS).
- The existing `modal` secret for R2/HF; never print secret values.

## Acceptance checks
- [ ] `GENERATION_BACKEND=modal` with `MODAL_ENDPOINT_URL` unset still fails **cleanly** with
      `BackendNotConfiguredError` and refunds (this is load-bearing for T-014).
- [ ] With a configured endpoint, `generate_video` returns a `GenerationResult` whose
      `video_path` is a real mp4 (check `ftyp`) and whose `poster_path` is a real image,
      both inside `work_dir`.
- [ ] Timeout is ≥ the observed 6 min; raise `GENERATION_TIMEOUT_SECONDS` default or add a
      Modal-specific timeout. A 240 s timeout would kill every real run.
- [ ] The worker's 300 s lease must survive a 6 min call — confirm `renew_lease_until_lost`
      covers it; if not, raise `WORKER_LEASE_SECONDS` in `.env.example` only.
- [ ] `apps/gpu/ltx_spike.py` still runs from `@app.local_entrypoint()` for a manual smoke.
- [ ] No secrets in code, logs, report, or commit. No paid generation in pytest.

## Verify command (paste its full output in report.md)
```
cd apps/api && uv run ruff check . && uv run mypy && uv run pytest -q tests/test_modal_adapter.py tests/test_backend_selection.py
```
plus a manual, clearly-labelled paid probe (not a test):
```
GENERATION_BACKEND=modal MODAL_ENDPOINT_URL=<url> uv run python -c "..."   # one clip, ~$0.2
```
Record the real elapsed seconds and estimated spend. If you cannot afford the paid probe,
say so honestly and mark the live half UNVERIFIED in the report — do not fake it.

## Out of scope
- Prompt-conditioning proof on the live URL (T-014), contract changes, new routes or schemas.
- Keeping a GPU warm, H100, `modal deploy` of anything outside `ltx_spike.py`.
- OpenRouter video (separate task).

## Report
Write `docs/tasks/T-013/report.md` using `docs/templates/report.md`. Commit all of the above
in ONE commit with a plain message (no attribution trailers), including the `.agent-logs/` export.
Do not mark your own work reviewed.
