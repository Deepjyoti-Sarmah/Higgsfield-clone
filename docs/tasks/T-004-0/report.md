# Report T-004-0

**Agent / model / tool:** designer · deepseek-flash · DeepSeek Harness (DSH) subagent (completion pass; the design itself was authored earlier in Claude Opus)
**Result:** DONE

## Files changed
- `docs/specs/004-create-video/tasks.md` (new): 5 tasks `T-004-1` … `T-004-5` + the completed `T-004-0` design row, each with its exact Files list, a copy-pasteable verify command, depends-on and suggested role, plus the wave ordering `T-004-1 → (T-004-2 ∥ T-004-4) → T-004-3 → T-004-5`.
- `docs/tasks/T-004-1/brief.md` (new): shared types / copy / pure helpers / `ui/` primitives / vitest runner.
- `docs/tasks/T-004-2/brief.md` (new): data hooks (guest runner, presets, URL selection, credits, session history, image upload).
- `docs/tasks/T-004-3/brief.md` (new): job hooks (idempotent create, SSE watcher + 5 s poll fallback, events, elapsed, active job).
- `docs/tasks/T-004-4/brief.md` (new): panel components (drop zone, thumbnail, preset picker, prompt, generate).
- `docs/tasks/T-004-5/brief.md` (new): page assembly, canvas views, `/v/:jobId` route, `App.tsx`.
- `docs/tasks/T-004-0/report.md` (new): this report.

`docs/specs/004-create-video/spec.md` and `docs/specs/004-create-video/design.md` were **not** modified (no contradiction with `openapi.json` was found — see open issues).

## Reused
- `docs/specs/004-create-video/design.md`: its **AC → design → task map** and **Files** table are the sole source for the task split; the four `ui/` primitives (`buttonStyles`, `ButtonLink`, `ProgressBar`, `Toast`) are exactly the ones the design justifies under the rule of two.
- `docs/specs/004-create-video/spec.md` AC-1 … AC-9 (task numbering only; no rewrite).
- `docs/templates/{tasks.md,delegation-brief.md,report.md}` for structure; `docs/tasks/T-003-3/brief.md` + `docs/specs/003-generation-core/tasks.md` for the house style of briefs and the `**Waves:**` line.
- `packages/contracts/openapi.json` (read-only) to confirm every path and schema the design names: `GET /api/v1/presets`, `POST /api/v1/auth/guest`, `GET /api/v1/credits`, `POST /api/v1/uploads`, `POST /api/v1/uploads/{asset_id}/complete`, `POST /api/v1/jobs`, `GET /api/v1/jobs/{job_id}`, `GET /api/v1/jobs/{job_id}/events`, and schemas `PresetResponse`, `AssetResponse`, `JobResponse`, `JobStatusEvent`, `InsufficientCreditsResponse`, `JobCreateRequest`, `UploadCreateRequest`.
- `docs/specs/003-generation-core/design.md` § API contract (top-level 402 body, idempotent create, SSE first frame / close-after-terminal / reaper re-queue) to keep the T-004-3 acceptance checks aligned.
- Existing web patterns linked from every brief: `apps/web/src/ui/Button.tsx`, `apps/web/src/api/client.ts`, `apps/web/src/features/session/useSession.ts`, `apps/web/src/styles.css`, `apps/web/eslint.config.js`, `apps/web/src/App.tsx`.
- `docs/templates/delegation-brief.md` and `docs/templates/report.md`.

## Verify output (full paste, no summarising)
Command:
```
python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))"
ls docs/tasks | grep T-004
scripts/check-standards
```
Output (all three commands, in order):
```
/api/health
/api/v1/auth/guest
/api/v1/credits
/api/v1/jobs
/api/v1/jobs/{job_id}
/api/v1/jobs/{job_id}/events
/api/v1/me
/api/v1/presets
/api/v1/uploads
/api/v1/uploads/{asset_id}/complete
T-004-0
T-004-1
T-004-2
T-004-3
T-004-4
T-004-5
check-standards: ok (0 violations)
```
Exit status: `0` for all three (the combined run printed `[exit: 0]` after `scripts/check-standards`).

Additional structural check run by hand (not part of the verify command): every brief's **Allowed files** list was compared against design.md's **Files** table and against the other briefs. Result: `T-004-1`=19, `T-004-2`=10, `T-004-3`=7, `T-004-4`=10, `T-004-5`=15 files (including each task's own `report.md`); no extras, no omissions, **no file appears in two tasks**.

## Standards check
```
check-standards: ok (0 violations)
```
`scripts/check-standards` skips `docs/**`, so the docs written here do not affect it; the repository is clean.

## Open issues / guesses / things skipped
- **Authorship / review status (stated plainly):** `docs/specs/004-create-video/design.md` was authored by **Claude Opus** in an earlier run that hit its account session limit before writing `tasks.md`, the T-004-k briefs, or a report. This completion pass ran on **deepseek-flash via DSH**, using only `design.md` + `spec.md` + `openapi.json` as the source. The design for spec 004 has **not been reviewed by a different model**, so per `AGENTS.md` ("Don't mark your own work reviewed") it should be treated as unreviewed until a separate model reviews it.
- **No contract contradiction:** every path and schema the design references exists in `packages/contracts/openapi.json`; the design's claimed `vitest@^5` peer range was re-checked (`npm view vitest@^5 peerDependencies` → `vite: '^6.4.0 || ^7.0.0 || ^8.0.0'`, satisfied by the installed `vite@^8.3.0`). `design.md` and `spec.md` were therefore left byte-identical.
- **Cross-task type dependency (design nuance, not a contradiction):** `useActiveJob.ts` (T-004-3) consumes `CreditsControls` (exported by `useCredits.ts`, T-004-2) and `SessionHistory` (exported by `useSessionHistory.ts`, T-004-2). These two control types are declared in the design's hook sections, not in the § Shared types block that T-004-1 owns. `tasks.md` records this as `T-004-3 Depends on: T-004-2`, and the T-004-3 brief tells the implementer to import those exact types. No file overlap is introduced. If the orchestrator prefers full parallelism, the alternative is to have T-004-1 also declare those two types in `createVideoTypes.ts` and to drop the T-004-2 dependency; that would be an edit to `design.md`, which this task was told not to make.
- **Wave ordering is inferred, not literal in `design.md`:** the design does not print an explicit wave line. The ordering `T-004-1 → (T-004-2 ∥ T-004-4) → T-004-3 → T-004-5` was derived from the import graph and the AC → task map, and is stated in `tasks.md`.
- **Unit tests only in T-004-1/2/3:** the design's **Test strategy** table assigns `canvasPhase.test.ts`, `imageFileRules.test.ts`, `elapsedTime.test.ts` to T-004-1, `sessionHistoryStore.test.ts` to T-004-2 and `jobStatusWatcher.test.ts` to T-004-3. Following the verify convention, only those three briefs include `npm --prefix apps/web run test`; T-004-4/5 use lint + typecheck + build + check-standards. T-004-5 additionally carries an explicit **manual flow check** that must be reported as **SKIPPED** while the T-003-3/4/5 routes still return 501.
- **"No two tasks share a file" excludes each task's own report:** `docs/tasks/T-004-k/report.md` is in that task's Allowed files (as in the T-003 briefs); the 60 implementation files are pairwise disjoint.
- **Not done, by instruction:** no `docs/PLAN.md` / `docs/STATUS.md` / `docs/WORKLOG.md` edits, no `apps/**` code, no commit. The orchestrator handles docs sync and commits.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Spec 004 (Create video) design + task split + 5 briefs; 61 files assigned, no overlaps | `docs/specs/004-create-video/{design,tasks}.md`, `docs/tasks/T-004-{1..5}/brief.md` | `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks \| grep T-004 && scripts/check-standards` (ok, 0 violations) | 2026-09-13 |
