---
session_id: t-017-probe
date: 2026-09-14
author: Deepjyoti-Sarmah
model: deepseek-flash
tool: dsh (run_code/bash) + modal CLI
project: higgsfield-rebuild
total_exchanges: 1
---

# Session Log - 2026-09-14 · T-017 paid FLUX probe (unblocked)

Append-only follow-up to `.agent-logs/2026-09-14_23-45_T-017_deepseek-flash-dsh.md`, which recorded the
probe as blocked on Hugging Face gating. No secrets are recorded.

---

[LOG_ENTRY type=PROMPT num=1 session=t-017-probe]
model: user

done now continue

[LOG_ENTRY type=SUMMARY num=1 session=t-017-probe]
model: deepseek-flash

- Re-ran the brief's paid probe (the FLUX.1-schnell license had been accepted):
  modal run apps/gpu/flux_image.py --prompt "a neon-lit tokyo alley at night" --count 4
- First (cold) run: 23-file weight download, load_seconds=135.0, generate_seconds=26.3 → 4 distinct
  1024x1024 images (~$0.18-0.25 at $3.95/h H100).
- Second (warm, weights cached in the ltx-weights volume): load_seconds=10.2, generate_seconds=25.7,
  WALL_SECONDS=61.68 (~$0.05-0.06).
- Evidence committed: docs/verification/flux/flux-1..4.png. T-017 moved from PARTIAL/BLOCKED to DONE;
  the live IMAGE_GENERATION_BACKEND stays placeholder.
