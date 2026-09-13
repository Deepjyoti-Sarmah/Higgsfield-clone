# Report T-012

**Agent / model / tool:** implementer · opencode / Muse Spark (user-approved paid runs)
**Result:** DONE — first real AI clip in R2

## Files changed
- `apps/gpu/ltx_spike.py`: `gpu="H100"` → `gpu="A10G"`; `.to("cuda")` → `enable_sequential_cpu_offload()`; `torchvision==0.23.0` added (Gemma4 processor needs it); `LTX2Pipeline` → `LTX2ImageToVideoPipeline` (the T2V class takes no `image` arg); audio-`None` guard; `huggingface` secret wired in; docstring updated
- `docs/tasks/T-012/brief.md`, `docs/tasks/T-012/report.md` (this file)

## Reused
- Modal secrets `r2` + `huggingface` (names only — values never handled); public picsum seed image as input

## Verify output (full paste, no summarising)
Run 5 (success) — `modal run apps/gpu/ltx_spike.py --image "https://picsum.photos/seed/higgsfield/960/544" --prompt "slow dolly in"`:
```
{'r2_key': 'spikes/f7d0cf44-5a15-41d6-99b2-dd54bbbb8b8e.mp4', 'load_seconds': 27.5, 'generate_seconds': 339.8}
Stopping app - local entrypoint completed.
Runner terminated.
✓ App completed. View run at
https://modal.com/apps/deepjyoti-sarmah/main/ap-fo98E8fzUL3Y6Y5xW4u3im
```
Object probe (public r2.dev URL — no credentials involved):
```
http=206 bytes=65536 type=video/mp4
first 32 bytes: 00 00 00 20 66 74 79 70 69 73 6f 6d ... (`ftypisom ... isomiso2avc1mp41`)
full object: http=200 bytes=800917
```
Real H.264 mp4, 800,917 bytes, served as `video/mp4`.

## The road there (all five runs, honest)
1. `GatedRepoError: 401` — repo is `gated:auto`. Human accepted the license + created the `huggingface` secret.
2. "not in the authorized list" — grant hadn't propagated; user confirmed, re-ran.
3. `ModuleNotFoundError: No module named 'torchvision'` (via `Gemma4Processor` import) — added `torchvision==0.23.0`. Weights (57 files) downloaded to the `ltx-weights` Volume on this run.
4. `TypeError: LTX2Pipeline.__call__() got an unexpected keyword argument 'image'` — `LTX2Pipeline` is text-to-video; the image-to-video class is `LTX2ImageToVideoPipeline` (confirmed against diffusers `main` source + its docstring example).
5. Green: load 27.5 s, generate 339.8 s on A10G with sequential CPU offload, 960×544 @ 121 frames, distilled sigmas, clip in R2.

## Cost
- Success run: 367 s of A10G ≈ **$0.08** at ~$0.80/h.
- All 5 runs together ≈ **$0.20 estimated** (runs 1/2/4 failed in ~1–2 min each; run 3 downloaded weights for ~4–5 min). Exact figures live in the Modal dashboard, which I did not open.
- Well inside the $30 budget; the weights Volume makes repeat runs cheaper (no re-download).

## Standards check
```
uv --directory apps/api run ruff check apps/gpu/ltx_spike.py → All checks passed!
scripts/check-standards → ok (0 violations)
```
No contract change (`openapi.json` untouched).

## Open issues / guesses / things skipped
- A10G rate ($0.80/h) is the public list estimate, not a metered figure — dashboard is authoritative.
- Sequential CPU offload is slow (5.7 min/clip); `enable_model_cpu_offload()` is the next knob if iteration speed matters (still A10G).
- The clip is unreviewed visually (no browser here) — it is byte-verified (ftyp/h264/size), not eyeballed.
- Next: T-013 `ModalAdapter` can now call this exact function shape.
- Not marked reviewed — a different model must review.

## Proposed STATUS.md line
| **Modal LTX-2.5 spike GREEN on A10G**: real AI clip in R2 (`spikes/f7d0cf44-….mp4`, 800,917 B, ftyp `isomiso2avc1`, served 200 as `video/mp4`); load 27.5 s + generate 339.8 s; ~$0.20 total across 5 runs | `apps/gpu/ltx_spike.py` (A10G, `LTX2ImageToVideoPipeline`, sequential offload), Modal app `ap-fo98E8fzUL3Y6Y5xW4u3im` | `modal run apps/gpu/ltx_spike.py --image <picsum url> --prompt "slow dolly in"` → `r2_key` + public-URL byte probe (full output in `docs/tasks/T-012/report.md`) | 2026-09-13 21:30 |
