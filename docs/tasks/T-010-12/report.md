# Report T-010-12

**Agent:** glm-5.3-flash@freebuff · **Role:** implementer · **Result:** DONE

## Files changed
- `docs/DECISIONS.md` (append-only): **D-015 · 2026-09-26 · "Images are real (FLUX.1-schnell on Modal); the placeholder is a labelled fallback"** — Why cites `apps/gpu/flux_image.py` (persistent Modal endpoint, bearer secret), `select_image_adapter` → `FallbackImageAdapter` in `apps/api/app/adapters/backend_selection.py` (real adapter when `IMAGE_GENERATION_BACKEND=modal`, labelled placeholder otherwise, per AC-11), and the STATUS line showing `image_backend: "modal"` live. **Rejected:** keeping D-014's framing. Under D-014 exactly one line was added: "Superseded by D-015."
- `docs/WALKTHROUGH.md` (rewritten): a timed 5:00 first-person script — start page (0:00), still (0:30), "Animate this" + second clip (1:45), sequence with crossfade + music (3:15), ledger HOLD→SETTLE (4:00), share `/v/:id` (4:30), and the 15 s agents close (4:45): `scripts/task` board, `thread.md`, `verify.log` fingerprints, `.agent-logs/`, different-model reviews. Every label in quotes was grepped from the code first: "Animate this", "Add to sequence" (in StageActions), "Render · 1 credit" (sequenceCopy), "Add demo credits (100)" (CreditsPopoverPanel), "Open the studio", "Make your own", "From your still", "CUT · XFADE · FADE" (the chip labels are CUT/XFADE/FADE). A fallback line covers the local-stack case where backends aren't configured.
- `README.md` (rewritten): Reel & Still name + pitch; "What it does" updated for the studio (three tabs, Animate this, sequences, honest backends); architecture diagram gains `job_sequence_clip` and the FLUX.1-schnell/ffmpeg/fallback adapters; setup and run instructions kept accurate (all env-var docs preserved via `.env.example` reference; nothing removed); new **"How agents work in this repo"** section linking `AGENTS.md`, `docs/playbooks/multi-harness.md` and `docs/tasks/`; exactly one Higgsfield mention, in the closing "Origin" line with the brief's wording.
- `scripts/smoke-sequence` (new, 161 lines, executable, Python 3 stdlib only, `--help` works): guest cookie jar → ffmpeg test image → presigned upload + complete → 2 clip jobs via `POST /api/v1/jobs` (same calls as `scripts/smoke-generation`) → poll to succeeded → `POST /api/v1/sequence-jobs` with `clips[1] = crossfade` → poll `GET /sequence-jobs/{id}` (300 s default, `--timeout` overridable) → checks: succeeded; `video_url` GET 200 (ranged, 206 accepted) with `video/mp4`; `duration_ms > 5000`; ledger contains HOLD −1 and SETTLE for the job. One PASS/FAIL line per check, non-zero exit on any FAIL, never requires paid generation.

## Verify (brief's exact command)
```
chmod +x scripts/smoke-sequence   → ok
scripts/check-links               → ok (0 broken)
scripts/check-standards           → ok (0 violations)
grep -q "D-015" docs/DECISIONS.md → ok (D015_OK)
python3 scripts/smoke-sequence --help → usage text printed (HELP_OK)
wc -l scripts/smoke-sequence      → 161 (≤ 200)
```

## Local smoke run (docker compose db+minio, uvicorn api, worker with GENERATION_BACKEND=local-motion)
```
$ python3 scripts/smoke-sequence http://localhost:8000 --timeout 300
smoke-sequence: base_url=http://localhost:8000
ok 0 guest: f9b35599-df03-4883-9c14-ffcaf1ae58e9
ok 0 upload: asset 9863c5fd-ea91-46bb-a802-4b220a51e49f ready
ok 0 clips succeeded: ['4dc1b90e-c649-49ac-a735-9cf9eecc15ae', '2b6cfd77-5673-4f0d-a7bc-eb827ecb8d3e']
ok 0 sequence accepted: 35aec57f-896e-4f27-90fd-bbc25fae0013 (clips=2, cost=1)
PASS sequence succeeded: status=succeeded
PASS sequence has video_url
PASS video_url GET 200 video/mp4: GET -> 206 'video/mp4'
PASS duration_ms > 5000: duration_ms=9500
PASS ledger has HOLD -1 for the sequence: entries=[{... 'kind': 'HOLD', 'amount': -1, 'job_id': '35aec57f...'}, {... 'kind': 'SETTLE', 'amount': 0, 'job_id': '35aec57f...'}]
PASS ledger has SETTLE for the sequence: kinds=['HOLD', 'SETTLE']
smoke-sequence: PASS (0 failed)
exit=0
```
A first attempt failed one check: `video_url` is a presigned GET-only URL, so `HEAD` returned 403. The check now uses a 1-byte ranged GET (206 accepted) — noted here so the reviewer sees the change from the brief's wording ("HEAD returns 200"): the check is stricter in spirit, since it also verifies the body is actually fetchable.

## no-ai-slop Detect mode (WALKTHROUGH.md)
Ran against the rewrite: no banned words, no em-dash crutches (two used for genuine asides), no "seamless/unleash/effortlessly" family, no binary contrasts, no fake stats. Sentences are short and concrete. Clean.

## Acceptance checks
- [x] D-015 exists and D-014 points to it — `grep -q "D-015" docs/DECISIONS.md` passes; "Superseded by D-015." is the only edit inside D-014.
- [x] WALKTHROUGH ≤ 5:00 and matches real UI labels — timings sum to 5:00; labels grepped from `apps/web/src` before writing (see Files changed).
- [x] `scripts/smoke-sequence http://localhost:8000` passes locally — output pasted above, 6/6 PASS, exit 0.
- [x] `scripts/check-links` and `scripts/check-standards` pass — 0 broken, 0 violations.

## Open issues / guesses / skipped
- The brief's ledger wording said "HOLD −1 and SETTLE"; the live run shows SETTLE amount 0 (the credit stays spent). I asserted presence of HOLD −1 and a SETTLE row for the job, not a SETTLE amount — matching T-010-3's actual behavior (`complete_step_success` writes `SETTLE 0`).
- No BOARD.md exists (`docs/tasks/BOARD.md` absent), so README links the `docs/tasks/` directory itself.
- The deployed-URL smoke was not run against production (that's T-010-13's deploy); the local stack run above stands in.

## Proposed STATUS.md line
| What | What | Where | Verified by | When (UTC) |
|---|---|---|---|---|
| D-015, 5-minute WALKTHROUGH, Reel & Still README, `scripts/smoke-sequence` (T-010-12) | docs + smoke match the running system | `docs/DECISIONS.md`, `docs/WALKTHROUGH.md`, `README.md`, `scripts/smoke-sequence` | glm-5.3-flash@freebuff (check-links 0, check-standards 0, local smoke 6/6 PASS exit 0) | 2026-09-26 |
