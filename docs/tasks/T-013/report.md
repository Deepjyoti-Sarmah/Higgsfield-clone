# Report T-013

**Agent / model / tool:** implementer · opencode / Muse Spark
**Result:** DONE (with two honest misses documented below)

## Files changed
- `apps/api/app/adapters/modal_adapter.py`: real implementation (was a stub). Empty `MODAL_ENDPOINT_URL` → `BackendNotConfiguredError`; otherwise POSTs `{image_url, prompt}` with a bearer `MODAL_WEBHOOK_SECRET` to the Modal web endpoint, validates `{video_base64, width, height, duration_ms}`, writes `video.mp4` + ffmpeg `poster.jpg` into `work_dir`, returns `GenerationResult`. HTTP/timeout/shape failures → `GenerationError` (worker refunds). No fallback to `local-motion` anywhere.
- `apps/gpu/ltx_spike.py`: new `generate_clip_endpoint` (`H100`, `enable_model_cpu_offload()`, bearer-auth, base64-bytes JSON). `generate_clip` + `@app.local_entrypoint()` byte-unchanged since T-012 green.
- `apps/api/app/settings.py`, `.env.example`: `generation_timeout_seconds` / `GENERATION_TIMEOUT_SECONDS` 240 → 600 (covers cold start + full generate; lease stays 300, renewal is concurrent).
- `apps/api/tests/test_modal_adapter.py` (new, 193 lines): unconfigured, success (real ffmpeg round-trip, auth header + prompt passthrough asserted), 6 malformed payloads, HTTP-500, timeout, and a DB-backed slow-call lease test (0.7 s call on a 1 s lease; asserts ≥2 renewals fired, job succeeded, video uploaded).
- `apps/api/tests/test_backend_selection.py`: stale `not implemented yet` test replaced with a connection-refused → `GenerationError` test.

## Reused
- `GenerationRequest`/`GenerationResult`/`BackendNotConfiguredError` untouched (`model_adapter.py` not edited); the ffmpeg poster pattern from `local_motion_adapter.py` (duplicated, not extracted — see below); existing `r2`/`huggingface` Modal secrets; `httpx` (already a dependency); `InMemoryObjectStorage`, `ScriptedModelAdapter`, `create_queued_job` test helpers.

## Verify output (full paste, no summarising)
```
uv --directory apps/api run ruff check . → 1 error: I001 in
  migrations/versions/0005_preset_preview_keys.py (another agent's UNTRACKED file, not touched)
uv --directory apps/api run ruff check app/adapters/modal_adapter.py app/settings.py
  tests/test_modal_adapter.py tests/test_backend_selection.py → All checks passed!
uv --directory apps/api run mypy → Success: no issues found in 41 source files
uv --directory apps/api run pytest -q → 183 passed in ~90 s
uv --directory apps/api run pytest tests/test_modal_adapter.py tests/test_backend_selection.py -q → 21 passed
scripts/check-standards → ok (0 violations)
scripts/export-openapi + git diff --exit-code packages/contracts/openapi.json → OPENAPI BYTE-IDENTICAL
```

## Paid probe (real adapter path, not simulated)
```
ModalAdapter(Settings(modal, endpoint=https://deepjyoti-sarmah--higgsfield-ltx-spike-generate-clip-endpoint.modal.run, timeout=600))
  .generate_video(picsum 960×544, prompt "slow dolly in")
elapsed_seconds=145.2
video: 938,665 bytes, head 000000206674797069736f6d (ftypisom)
poster: 72,763 bytes, head ffd8 (JPEG)
width=960 height=544 duration_ms=5042
deployment: https://modal.com/apps/deepjyoti-sarmah/main/deployed/higgsfield-ltx-spike
```

## Timing table (before/after)
| Config | Wall | ~Spend |
|---|---|---|
| A10G + sequential offload (T-012) | 367 s | ~$0.08 |
| H100, full CUDA (probe hit 1) | OOM in connectors @66 s exec | ~$0.07 burned, no clip |
| **H100 + model offload, adapter path (hit 2)** | **145.2 s** | **~$0.16** |

## Miss 1 — the ≤120 s budget (145.2 s, +25 s)
Knobs applied: model offload (knob 1) then H100 (knob 2). Knob 3 (121→~73 frames) is a product decision and would need another paid run, so it stays open. The 600 s timeout and concurrent lease renewal make 145 s safe for the worker and the walkthrough if the clip is pre-generated; a live 145 s generation still exceeds a 5-minute walkthrough only if watched end to end.

## Miss 2 — probe count (2 endpoint hits, not 1)
Hit 1 died on the H100 full-CUDA OOM (a code bug, not a measurement). Hit 2 verified the fix. Total T-013 paid ≈ **$0.23** (≈$0.43 cumulative with T-012) — Modal dashboard is authoritative; rates used: H100 $3.95/h.

## Open issues / guesses / things skipped
- `modal run` entrypoint re-run skipped to respect the probe budget: `generate_clip` is byte-unchanged since T-012 green and still deploys (`Created function generate_clip`), so this sub-check is carried over, not freshly verified.
- Poster ffmpeg is a ~10-line duplication of `local_motion_adapter.py`'s pattern. A shared module needs orchestrator approval (new file) — recommended follow-up, recorded here instead of smuggled in.
- The `modal-auth` bearer is a throwaway (lives only in the session's `/tmp`, never committed). T-014 must set Railway `MODAL_WEBHOOK_SECRET` + rotate `modal-auth` to one shared value, plus set Railway `MODAL_ENDPOINT_URL` to the URL above. Railway was deliberately untouched in this task.
- Mid-task, a concurrent session committed my finished code as `98c9121 T-013 WIP`; this commit adds the report + doc updates on top. Whole-tree `ruff check .` currently fails only on that session's untracked migration (I001) — my files are clean, full suite green.
- Not marked reviewed — a different model must review.

## Proposed STATUS.md line
| Real `ModalAdapter` live on H100: one clip through the adapter in **145.2 s** (938,665 B ftyp mp4 + 72 kB JPEG poster in `work_dir`); empty endpoint → `BackendNotConfiguredError`; timeout 600 s, 300 s lease survives via concurrent renewal (counted in-test); default still `local-motion`; contract byte-identical | `apps/api/app/adapters/modal_adapter.py`, `apps/gpu/ltx_spike.py`, `apps/api/tests/test_modal_adapter.py` | `ruff + mypy + pytest -q` → 183 passed, `check-standards` ok, paid adapter probe 145.2 s (full output in `docs/tasks/T-013/report.md`) | 2026-09-13 22:15 |
