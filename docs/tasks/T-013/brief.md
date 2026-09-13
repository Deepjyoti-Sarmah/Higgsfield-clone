# Brief T-013: real `ModalAdapter` — AI video that is fast enough to demo

**Role:** implementer (strong model) · Supersedes `docs/prompts/T-013-modal-adapter.md` (kept for reference; this file is the task packet)

## Context links
- Green spike + measured numbers: `apps/gpu/ltx_spike.py`, `docs/tasks/T-012/report.md`
- Port you must satisfy **unchanged**: `apps/api/app/adapters/model_adapter.py`
- Current stub: `apps/api/app/adapters/modal_adapter.py`
- Worker path that calls the port: `apps/api/app/services/generation_runs.py`
- Working reference for the same shape: `apps/api/app/adapters/local_motion_adapter.py`
- Design: `docs/specs/003-generation-core/design.md` § Modal backend

## Goal
`GENERATION_BACKEND=modal` produces a real LTX-2.5 clip from the user's photo, in **under ~2 minutes**, written into `work_dir` as `video_path` + `poster_path` so the worker uploads it exactly like `local-motion` does. No contract change.

## Facts from the spike (verified — do not re-litigate)
- GPU function: `generate_clip(image_url, prompt) -> {r2_key, load_seconds, generate_seconds}`.
- Measured: **27.5 s load + 339.8 s generate** on **A10G with `enable_sequential_cpu_offload()`**.
- It needs a **publicly reachable image URL**. The worker already passes `GenerationRequest.input_image_url` (presigned). Use it — do not re-upload.
- `GenerationResult` needs **both** `video_path` and `poster_path`; poster = frame 1.

## The four gotchas (all real — I verified them in the code)
1. `generation_timeout_seconds` defaults to **240 s** in `apps/api/app/settings.py` — shorter than one generate. Every live run would be killed mid-flight.
2. `worker_lease_seconds` is **300 s**. The lease must cover the whole call; confirm renewal actually fires during it.
3. Re-uploading the input image is waste — the presigned URL is already public.
4. The spike returns an `r2_key`; the worker expects **local files**. Bring the bytes back into `work_dir` (return them from the GPU function, or fetch the key through the existing `ObjectStorage`).

## Speed budget (the part the earlier draft missed)
A 6-minute generation cannot appear in a ≤5-minute walkthrough. Get one clip to **≤120 s wall clock**, and note it is roughly cost-neutral:

| Config | Time | ~Cost/clip |
|---|---|---|
| A10G + sequential offload (today) | ~367 s | ~$0.08 |
| **Target: H100 / A100-80GB, no offload** | target ≤120 s | ~$0.10 |

Knobs, cheapest first — apply until you hit the budget, and record what each one bought:
1. `enable_model_cpu_offload()` instead of `enable_sequential_cpu_offload()` (the T-012 report names this as the next knob).
2. Bigger GPU so the 22B bf16 model fits without offload — **A100-80GB or H100**, not A100-40GB (44 GB of weights will not fit).
3. Fewer frames / smaller frame: 121 → ~73 frames (3 s) and/or 704×384. **Only if 1 and 2 miss the budget**, and say so in the report — clip length is a product decision.
4. Keep the weights on the existing Modal Volume so the 27.5 s load only happens cold.

## Safety rails
- **`local-motion` stays the default backend.** `modal` is opt-in per environment. The live link must never hang because a GPU is cold.
- Unconfigured (`MODAL_ENDPOINT_URL` unset) must still raise `BackendNotConfiguredError` — the job fails cleanly and the hold is **released**.
- A timeout or GPU error must fail the job and refund, never leave credits held.
- Never silently fall back to `local-motion` and present it as AI output.

## Allowed files
- `apps/api/app/adapters/modal_adapter.py`
- `apps/gpu/ltx_spike.py` (GPU/offload change + a return path for the adapter; keep `@app.local_entrypoint()` working)
- `apps/api/app/settings.py`, `.env.example` (timeout/lease/endpoint fields)
- `apps/api/tests/test_modal_adapter.py` (new), `apps/api/tests/test_backend_selection.py` (only if needed)
- `docs/tasks/T-013/report.md`, `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`

## Must reuse
- `GenerationRequest` / `GenerationResult` / `BackendNotConfiguredError` from `model_adapter.py` — do not edit that file.
- The poster-frame ffmpeg pattern already in `local_motion_adapter.py`. Extract a shared helper only if the rule of two is met (`docs/STANDARDS.md`).
- The existing Modal secrets for R2 + Hugging Face. Never print secret values.

## Acceptance checks
- [ ] One real clip end to end, **wall clock recorded**, target ≤120 s (if you miss it, report the number and what you tried)
- [ ] `video_path` is a real mp4 (`ftyp` probe) and `poster_path` a real image, both in `work_dir`
- [ ] Unset endpoint → `BackendNotConfiguredError`, job fails, credits refunded
- [ ] Timeout raised above the measured generate time; the 300 s lease demonstrably survives a full call
- [ ] `GENERATION_BACKEND` default is still `local-motion`
- [ ] `apps/gpu/ltx_spike.py` still runs manually via its local entrypoint
- [ ] No secrets in code, logs, report or commit; **no paid generation inside pytest**

## Verify command (paste full output in report.md)
```
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy
uv --directory apps/api run pytest -q && scripts/check-standards
```
Then a clearly-labelled **paid** probe (not a test) — one clip, ~$0.10 — recording elapsed seconds and estimated spend:
```
modal run apps/gpu/ltx_spike.py --image <public url> --prompt "slow dolly in"
```
If you cannot run the paid probe, mark the live half **UNVERIFIED** and say why. Do not simulate it.

## Out of scope
- Prompt-conditioning proof (T-014), contract/schema changes, OpenRouter video, keeping a GPU permanently warm.

## Report
`docs/tasks/T-013/report.md` from `docs/templates/report.md`, including the before/after timing table and the actual spend. One commit, plain message, no attribution trailers, including `.agent-logs/`.
