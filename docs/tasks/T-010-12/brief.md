# Brief T-010-12: Docs and smoke (D-015, WALKTHROUGH, README brand, `scripts/smoke-sequence`)

**Role:** implementer · **Suggested model:** small · **Depends on:** T-010-3, T-010-6 and T-010-9 merged · **Wave:** W5

## Start here (any harness)
1. `scripts/task claim T-010-12 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), spec 010 (all of it), `docs/DECISIONS.md` D-014, `docs/WALKTHROUGH.md`, `README.md` and `scripts/smoke-generation`.
3. Questions: `scripts/task say T-010-12 QUESTION "…"`.

## Goal
The docs tell the truth about the product as it now is, and there's a one-command smoke test that proves sequences work against any deployed URL.

## Allowed files (touch nothing else)
- `docs/DECISIONS.md` (append only)
- `docs/WALKTHROUGH.md`
- `README.md`
- `scripts/smoke-sequence` (new, executable, Python 3 standard library, ≤ 200 lines)
- `docs/tasks/T-010-12/report.md`

## The change
1. **D-015** in `docs/DECISIONS.md`, appended in the file's existing format: "Images are real (FLUX.1-schnell on Modal); the placeholder is a labelled fallback. Supersedes D-014."
   - **Why:** cite `apps/gpu/flux_image.py`, `select_image_adapter` → `FallbackImageAdapter`, and the STATUS line that shows `image_backend: modal` live.
   - **Rejected:** keeping D-014's framing.
   - Add one line under D-014 itself: "Superseded by D-015." That's the only edit to an existing entry.
2. **`docs/WALKTHROUGH.md`:** rewrite it as a timed script of 5 minutes or less for the Still → Clip → Sequence demo:
   - Open `/`.
   - In the studio, make a still, then "Animate this", then make a second clip.
   - Build a Sequence with a crossfade and music, render it, and show the credits ledger (HOLD → SETTLE).
   - Share `/v/:id` in a private window.
   - Close with a 60-second "how it was built with agents" part: the `scripts/task` board, `thread.md`, `verify.log` fingerprints, `.agent-logs/`, and the different-model reviews.

   Keep the first-person voice for the user to read aloud. Plain sentences (run `no-ai-slop`).
3. **`README.md`:**
   - The product name and one-paragraph pitch become Reel & Still.
   - Add a "How agents work in this repo" section linking `AGENTS.md`, `docs/playbooks/multi-harness.md` and `docs/tasks/BOARD.md`.
   - Keep the setup and run instructions accurate. Do not remove any env var docs.
   - The only remaining mention of Higgsfield is one "Origin" line: "Started as a Higgsfield rebuild for an assignment; redesigned as its own product in spec 010."
4. **`scripts/smoke-sequence BASE_URL`:**
   1. Create a guest session (cookie jar).
   2. Make 2 clips using the same calls as `scripts/smoke-generation`, which already uploads an image and creates a video job. Reuse its approach, and read that script before writing yours.
   3. Wait for both to succeed via polling.
   4. `POST /api/v1/sequence-jobs` with a `crossfade`.
   5. Poll `GET /api/v1/sequence-jobs/{id}` until it's terminal (a 300 s timeout).
   6. Assert: `succeeded`; a `video_url` whose HEAD returns 200 with `video/mp4`; `duration_ms` > 5000; and the ledger (`GET /credits/ledger`) contains a HOLD −1 and a SETTLE for the job.

   It prints one PASS/FAIL line per check and exits non-zero on any FAIL. It never needs paid generation: it uses whatever backend the target runs.

## Acceptance checks
- [ ] D-015 exists and D-014 points to it
- [ ] The WALKTHROUGH runs to 5 minutes or less when read aloud and matches the real UI labels (Still, Clip, Sequence, "Animate this", "Add to sequence", "Render · 1 credit", "Add demo credits")
- [ ] `scripts/smoke-sequence http://localhost:8000` passes against a local `docker compose up` stack. Paste the output
- [ ] `scripts/check-links` and `scripts/check-standards` pass

## Verify command
```
chmod +x scripts/smoke-sequence && scripts/check-links && scripts/check-standards && grep -q "D-015" docs/DECISIONS.md && python3 scripts/smoke-sequence --help
```

## Out of scope
- App code, deploys (T-010-13 is the orchestrator's).

## Finish
Write `report.md`, including the local smoke run output. Then:
1. `scripts/task verify T-010-12`
2. `scripts/task submit T-010-12 --as <you> [--transcript <file>]`
