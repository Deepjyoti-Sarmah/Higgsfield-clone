---
session_id: t-017-flux-image
date: 2026-09-14
author: Deepjyoti-Sarmah
model: deepseek-flash
tool: dsh (run_code/bash)
project: higgsfield-rebuild
total_exchanges: 1
---

# Session Log - 2026-09-14 · T-017 real text→image on Modal

Hand-exported summary from the DSH main session (tool calls omitted; no secrets).

---

[LOG_ENTRY type=PROMPT num=1 session=t-017-flux-image]
model: user

T-017 — real images on our GPU (strong model, after T-033 is committed). It needs
a paid Modal probe of about $0.01–0.05. Same prompt with T-017.

[LOG_ENTRY type=SUMMARY num=1 session=t-017-flux-image]
model: deepseek-flash

- apps/gpu/flux_image.py: FLUX.1-schnell on H100 on the shared ltx-weights volume,
  batched count images, bearer-protected web endpoint and a modal-run entrypoint.
- apps/api/app/adapters/modal_image_adapter.py: ModalImageAdapter + FallbackImageAdapter
  (mutates name to the backend that actually ran); backend_selection now keys image
  selection off IMAGE_GENERATION_BACKEND (default placeholder); image_dimensions.py
  holds the FLUX sizes and 4/8 steps.
- Unit tests: modal image adapter (all aspect ratios, auth/params, malformed, HTTP,
  timeout) and placeholder fallback/selection; openapi byte-identical.
- BLOCKED on the paid probe: Hugging Face GatedRepoError 403 for
  black-forest-labs/FLUX.1-schnell — the license has not been accepted for the
  huggingface Modal secret's account. Timings/cost are UNVERIFIED, not simulated.
