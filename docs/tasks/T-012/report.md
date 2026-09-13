# Report T-012

**Agent / model / tool:** implementer · opencode / Muse Spark (user-approved paid run)
**Result:** BLOCKED (needs 2 human clicks + 1 token; zero code questions remain)

## Files changed
- `apps/gpu/ltx_spike.py`: `gpu="H100"` → `gpu="A10G"`; `.to("cuda")` → `pipeline.enable_sequential_cpu_offload()` (safe on 24GB); audio-`None` guard around `encode_video`; docstring line-length fix (ruff E501)
- `docs/tasks/T-012/brief.md`, `docs/tasks/T-012/report.md` (this file)

## Reused
- Modal `r2` secret (name only); public picsum seed image as the input frame

## Verify output (full paste, no summarising)
`modal run apps/gpu/ltx_spike.py --image "https://picsum.photos/seed/higgsfield/960/544" --prompt "slow dolly in"` (background PID 2080068, full log at `/tmp/opencode/t012-spike.log`, 1686 lines — not committed):
```
✓ Created objects.
httpx.HTTPStatusError: Client error '401 Unauthorized' for url
'https://huggingface.co/Lightricks/LTX-2.5-Diffusers/resolve/426936f8b22dc28e4def61e515478b0b7e4a53cc/model_index.json'
huggingface_hub.errors.GatedRepoError: 401 Client Error.
Cannot access gated repo for url https://huggingface.co/Lightricks/LTX-2.5-Diffusers/resolve/…/model_index.json.
Access to model Lightricks/LTX-2.5-Diffusers is restricted. You must have access to it and be authenticated to access it. Please log in.
Stopping app - uncaught exception raised locally
```
Public metadata probe: `GET https://huggingface.co/api/models/Lightricks/LTX-2.5-Diffusers`
→ `gated: auto`, 66 files. "auto" = click-through license acceptance, then any read token works.

## Standards check
```
uv --directory apps/api run ruff check apps/gpu/ltx_spike.py
All checks passed!
scripts/check-standards → ok (0 violations)
```

## Cost
- GPU ran only for the failed download attempt (~1–2 min on A10G ≈ **$0.02–0.03 estimated**; exact figure in the Modal dashboard, which I did not open).
- The ~7 min wall time was the local image build (torch 2.8 + diffusers-from-git, CPU, free) plus weight-download attempt (nothing downloaded — the 401 hit `model_index.json` first).
- Weights Volume `ltx-weights` created but empty; no R2 object written; no `r2` secret values touched.

## What this proved
- The Modal path works: auth OK, `r2` secret resolves, image builds, A10G container starts, the current diffusers API imports fine (`LTX2Pipeline`, `DISTILLED_SIGMA_VALUES`, `encode_video`) — **no code adaptation was needed**.
- The single blocker is Hugging Face gating, which no code change can pass.

## To unblock (human, ~3 min)
1. Open https://huggingface.co/Lightricks/LTX-2.5-Diffusers while logged in and accept the license terms.
2. Create a read token at https://huggingface.co/settings/tokens (fine-grained, read-only).
3. Run locally (do NOT paste the token into chat): `modal secret create huggingface HF_TOKEN=<token>` — then tell me and I will wire `modal.Secret.from_name("huggingface")` into the function and re-run the same command.

## Open issues / guesses / things skipped
- Did not try alternative model IDs — the brief names LTX-2.5 and the repo is one click from accessible; switching models is a fallback, not a fix.
- Sequential CPU offload is the slowest offload mode; if generation proves slow after unblocking, `enable_model_cpu_offload()` is the next knob (still on A10G).
- Not marked reviewed — a different model must review.

## Proposed STATUS.md line
| Modal LTX-2.5 spike BLOCKED on Hugging Face gating (not on code or GPU): `Lightricks/LTX-2.5-Diffusers` is `gated:auto`, container 401s on `model_index.json`; A10G path builds and starts fine | `apps/gpu/ltx_spike.py`, `/tmp/opencode/t012-spike.log` (1686 lines, local only) | `modal run apps/gpu/ltx_spike.py --image <picsum url> --prompt "slow dolly in"` → `GatedRepoError: 401` (full trace in `docs/tasks/T-012/report.md`) | 2026-09-13 20:30 |
