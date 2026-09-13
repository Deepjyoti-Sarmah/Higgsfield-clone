# Report T-000-7

**Agent / model / tool:** implementer/scout · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE (S1a and S1b)

## Files changed
- `README.md` (updated — S1a).
- `docs/tasks/T-000-7/report.md` (this file, new — both sub-tasks).
- **Not committed**; `docs/PLAN.md` was not touched (out of scope), so its checklist boxes are left for the orchestrator.

---

# S1a — README + repo hygiene

## What changed in `README.md`
1. **Labelled links.** The header table now leads with explicit labels and does **not** invent a URL:
   `**Live:** TBD until deploy (no public URL yet — docs/runbooks/deploy.md)` and
   `**Repo:** TBD (public GitHub URL — gh auth login is still broken, see docs/STATUS.md)`.
   `Status:` and `Plan:` keep their labels.
2. **A 4-line what-it-is.** Who lands, what they do, what comes back, and what the stack is
   (SPA + FastAPI on one origin, ledger in Postgres, presigned S3/R2, worker calling the model adapter).
3. **Local run commands from `docs/runbooks/local-dev.md`** — the runbook's exact First-run block
   (`cp .env.example .env.local`, `scripts/install-hooks`, `docker compose up -d --wait db minio`,
   `docker compose run --rm minio-init`, `uv --directory apps/api sync`, `alembic upgrade head`,
   `npm --prefix apps/web install`), then the two dev servers with their ports, the Vite proxy note,
   the `GENERATION_BACKEND=mock` rule and the pre-commit check list (now including `scripts/check-links`).
   A link to the full runbook covers troubleshooting and the clean-slate reset.
4. **Repo map taken from `AGENTS.md` § Repo map** (same one-liners), with the two files the README
   already documented kept underneath (`Dockerfile`, `docker-compose.yml`, `railway.json`) and
   `check-links`/`install-hooks` added to the `scripts/` line.
5. Kept: the architecture diagram + link to `docs/architecture/architecture.md`, and "How agents work".

Length: **113 lines** (budget 150). Every referenced path exists (checked below).

## Verify output (full paste)
```
$ scripts/check-links
check-links: ok (0 broken)
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0
```

Path existence check (all `OK`, run before writing this report): `docs/architecture/architecture.md`,
`docs/runbooks/local-dev.md`, `docs/STATUS.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `.env.example`,
`scripts/{install-hooks,check-standards,check-links,export-openapi}`, `apps/web/vite.config.ts`,
`docs/templates/handoff-prompt.md`, `docs/templates/handoff-prompt-small.md`, `docs/templates/report.md`,
`docs/playbooks/`, `apps/gpu/`, `Dockerfile`, `docker-compose.yml`, `railway.json`, `.agent-logs/`.

## `docs/PLAN.md` § Pre-hand-in checklist (status, not edited)
| Item | Status |
|---|---|
| Live link opens in a signed-out browser | **Not done** — no deploy yet (user placeholder) |
| Repo public, `.agent-logs/` present, committed incrementally | `.agent-logs/` **yes** (see S1b); public repo **not yet** (`gh auth login` broken) |
| README has labelled links (Live, Repo) | **Done** (this task) — both labelled, both honestly TBD |
| Walkthrough ≤ 5 min, camera on | Not done (human) |

---

# S1b — `.agent-logs/` presence check (scout)

## Required commands (full paste)
```
$ git log --oneline -- .agent-logs | head
0af7074 T-008-0: design spec 008 Credits + fake top-up and publish the top-up contract
776fc65 T-007-0: design spec 007 Share page and publish GET /api/v1/public/jobs/{job_id}
947940b T-005-0: design spec 005 Library and publish GET /api/v1/jobs
0d38295 T-002-5: R2 config blocked (no Account ID/bucket); Modal spike not run, no GPU credits spent
b54102d T-002-4: wire Neon (hosted Postgres) and verify the Modal CLI; R2 blocks the spike
82ecbd4 Independent review of spec 003/004 work: smoke 9/9 pass, flaky reaper test logged
12ff123 T-006-0: design spec 006 Explore (hero, tool cards, preset gallery, Recreate)
557d435 T-001-3: audit reference-images (duplicate of screenshots 01-16; 0/7 gaps covered)
e552d40 T-004-5: create-video page assembly (spec 004 complete)
1d88e28 T-003-7: end-to-end smoke of the generation core (spec 003 complete)

$ git log --oneline -- .agent-logs | wc -l
36

$ ls .agent-logs | wc -l          # visible entries (hides .gitkeep)
34
$ git ls-files .agent-logs | wc -l  # tracked, incl. .gitkeep
35
$ git check-ignore .agent-logs   # must print nothing
(nothing above = not ignored)

$ ls -d .agent-logs
.agent-logs

--- log-file breakdown ---
total files 35 = task-named 22 + claude-session 9 + other 3 + .gitkeep
   other: 2026-09-13_02-43-01_deepseek-harness_nonblock-tasks.md
   other: 2026-09-13_02-45-15_deepseek-harness_tailwind-convention.md
   other: 2026-09-13_07-58-58_deepseek-harness_README-CI-hooks.md
```

## Counts
- **Present:** yes. **Tracked:** 35 files. **Ignored:** no (`git check-ignore` prints nothing).
- `ls .agent-logs | wc -l` → **34**; the 35th tracked file is the hidden `.gitkeep`, which plain `ls` does not show.
- **35 log files** = 22 named after a task + 9 Claude Code session logs (UUID names, auto-captured) + 3
  DSH logs that carry no task id + `.gitkeep`.
- **Committed incrementally: yes** — **36 commits** touch `.agent-logs/`, from the very first
  `1dcf015 Add agent capture hooks` to the latest `0af7074 T-008-0` (the head of the list above is the
  most recent, and the list is one commit per task/wave, not one dump at the end).

## Tasks whose transcript is missing
Cross-referencing `docs/tasks/*/report.md` (43 finished tasks) against `.agent-logs/`:

| Coverage | Count | Detail |
|---|---|---|
| Dedicated log file named after the task | **21** | T-000-4, T-001-3, T-002-4, T-002-5, T-003-1…T-003-7, T-004-0…T-004-5, T-005-0, T-006-0, T-007-0, T-008-0 |
| No dedicated file, but inside a Claude Code session log | **5** | T-002-2, T-002-7, T-003-0, T-006-1, T-006-4 |
| **No transcript at all** (only incidental mentions in other logs) | **17** | **T-000-6, T-005-1, T-005-2, T-005-3, T-005-4, T-005-5, T-006-2, T-006-3, T-007-1, T-007-2, T-007-3, T-007-4, T-007-5, T-008-1, T-008-2, T-008-3, T-008-4** |

The cause is the one S1b predicted: these were **delegated DSH subagent runs, which cannot be wrapped by
`scripts/agent-run` and have no auto-capture hook**, so the transcript is owed to the orchestrator. Ten of the
17 say so in their own report, e.g.:

- `T-005-4`: "No `.agent-logs/` entry … the orchestrator owns capture/commit."
- `T-006-1` / `T-006-2`: "my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md the orchestrator must export this session's transcript into `.agent-logs/` at commit time."
- `T-007-2`/`T-007-3`/`T-007-5`: same note ("the orchestrator owns capture and the commit").
- `T-003-0`, `T-005-5`: same.

The other seven (T-000-6, T-005-1, T-005-2, T-005-3, T-007-1, T-007-4, T-008-1…T-008-4) are in the same
position but their reports do not spell it out — they were run under "the orchestrator handles docs sync and
the commit" briefs.

Note that the three "other" DSH logs (`nonblock-tasks`, `tailwind-convention`, `README-CI-hooks`) do capture
earlier ad-hoc work but carry no task id, so they do not count as a task transcript above.

## Open issues / guesses / things skipped
- **S1a:** the README's Live/Repo rows are deliberately TBD — no URL was invented. Fill them in when the
  Railway deploy and the public repo exist (`docs/runbooks/deploy.md`, pre-hand-in checklist).
- **S1b scope:** this was a read-only audit; nothing was exported and nothing committed. Exporting 17 DSH
  transcripts is not something this session can reconstruct after the fact — only the running session can
  write its own log, so the orchestrator must do it per-task at commit time (or accept the gap and say so in
  `docs/STATUS.md`).
- `.agent-logs/` is committed incrementally (36 commits) which satisfies the checklist's "committed
  incrementally (`git log -- .agent-logs`)" half; the "repo public" half is still blocked on `gh auth login`.

## Proposed STATUS.md line (WORKS)
| README updated for hand-in: labelled `Live:` (TBD until deploy) and `Repo:` (TBD) links, a 4-line what-it-is, the `local-dev.md` run commands and the `AGENTS.md` repo map; 113 lines, all referenced paths exist. `.agent-logs/` audit: present, tracked (35 files), not ignored, 36 incremental commits; 21/43 tasks have a dedicated transcript and **17 have none** (DSH subagents cannot self-wrap) | `README.md`, `docs/tasks/T-000-7/report.md` | `scripts/check-links && scripts/check-standards` → 0 broken links, 0 violations; `git log --oneline -- .agent-logs \| wc -l` → 36; `ls .agent-logs \| wc -l` → 34 (full output in `docs/tasks/T-000-7/report.md`) | 2026-09-13 17:12 |
