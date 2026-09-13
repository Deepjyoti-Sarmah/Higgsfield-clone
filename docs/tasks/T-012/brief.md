# Brief T-012: Modal LTX-2.5 spike on a small GPU (paid, time-boxed)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spike: `apps/gpu/ltx_spike.py` (written for H100, never run — treat as unverified)
- Decision: `docs/DECISIONS.md` D-002 (Modal primary, $30 free-credit budget)
- Handoff: user approved A10G over H100 for this spike (cheaper, fits 24GB)

## Goal
Land one real AI-generated clip in R2 via `modal run`, proving the Modal path works.
Record the real cost and the deployed function reference.

## Allowed files (touch nothing else)
- `apps/gpu/ltx_spike.py` (adapt to the small GPU + whatever the live diffusers API needs)
- `docs/tasks/T-012/brief.md` (this file), `docs/tasks/T-012/report.md`
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md` (append one line)
- `.agent-logs/*T-012*` (own session transcript export)

## Must reuse
- The Modal `r2` secret (name only — never print secret values anywhere)
- A public input image URL (no credential handling; e.g. a picsum seed URL)

## Acceptance checks
- [ ] `modal run apps/gpu/ltx_spike.py --image <public url> --prompt "slow dolly in"` ends with an `r2_key` under `spikes/`
- [ ] The object exists in the bucket and is a real mp4 (verify by header/size, not by eye)
- [ ] Total spend estimated from run duration × A10G rate and recorded honestly
- [ ] No secrets in chat, reports, commits, or logs
- [ ] If the diffusers API has moved (`LTX2Pipeline`, sigma values, audio return), adapt the code rather than abandoning it; if blocked after ~30 min of GPU time, stop and report BLOCKED with the exact error

## Verify command (paste its full output in report.md)
```
modal run apps/gpu/ltx_spike.py --image <public url> --prompt "slow dolly in"
```
plus an object-exists probe of the returned `r2_key` (byte size + `ftyp` header check).

## Out of scope
- `ModalAdapter` (T-013), prompt-conditioning/T-014, worker changes, contract changes
- Image models, H100 runs, keeping a GPU warm, `modal deploy`
- Rotating the R2 key (human dashboard task)

## Report
Write `docs/tasks/T-012/report.md` using `docs/templates/report.md`. Commit all of the
above in ONE commit with a plain message (no attribution trailers), including the
`.agent-logs/` export. Do not mark your own work reviewed.
