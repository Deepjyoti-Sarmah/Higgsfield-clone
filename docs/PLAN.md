# PLAN: live board

The frozen, approved plan is in `docs/BUILD-PLAN.md`. This file is the live version: update it whenever a status changes.

**Clock start:** 2026-09-12T23:37:19Z (assignment prompt). All times are UTC.

## Role assignments (change these freely; see the roles in AGENTS.md)
| Role | Currently filled by |
|---|---|
| Orchestrator | Claude Opus 5 (Claude Code, main session) |
| Implementer | TBD per task: any coding model |
| Reviewer | a different model from the task's implementer |
| Scout | any cheap/fast model |

## Milestones
| M | What | Box | Status | Exit criterion |
|---|---|---|---|---|
| M0 | Scaffolding: docs, playbooks, templates, capture for subagents + other tools, standards check | 1h | DONE (non-Claude canary answer pending, see STATUS) | Claude subagent + non-Claude agent both logged in `.agent-logs/` |
| M1 | Research: screenshots → `docs/research/flows/*` → `product-map.md` | 1.5h | DONE: scope approved (D-012); 7 flows still to capture | user approves scope |
| M2 | Walking skeleton LIVE (Railway + Neon + R2, guest auth, health) + Modal LTX spike: spec `docs/specs/002-walking-skeleton/` | 3h | CODE DONE locally; deploy + Modal are user placeholders | public URL opens signed out; one clip in R2 |
| M3 | P0 slices (specs 003+) | 10h | CODE COMPLETE: specs 003–008 all tasks done + committed; live `verify-slice` pending deploy | each verified live via `verify-slice` |
| M4 | P1 slices | — | TODO | each verified live |
| M5 | Ship: signed-out pass, README, public repo, walkthrough | 2h | TODO | checklist below all ticked |

## Task board
| Id | Task | Status | Owner model | Where |
|---|---|---|---|---|
| T-000-1 | AGENTS.md, CLAUDE.md, docs skeleton | DONE | Claude Opus 5 | `AGENTS.md`, `docs/` |
| T-000-2 | Templates + playbooks + `.claude/skills` wrappers | DONE | Claude Opus 5 | `docs/templates/`, `docs/playbooks/` |
| T-000-3 | Capture: SubagentStop + PreToolUse(Agent) hooks | DONE | Claude Opus 5 | `.claude/hooks/capture.py` |
| T-000-4 | `scripts/agent-run` wrapper for non-Claude agents | DONE (wrapper); real non-Claude answer pending (Codex quota) | Claude Opus 5 | `scripts/agent-run`, `docs/tasks/T-000-4/` |
| T-000-5 | `scripts/check-standards` | DONE | Claude Opus 5 | `scripts/check-standards` |
| T-001-1 | Flow docs: explore, image-create, video-create (16 screenshots) | DONE | Claude Opus 5 | `docs/research/flows/` |
| T-001-2 | Product map with verdicts | DONE (approved) | Claude Opus 5 | `docs/research/product-map.md` |
| T-002-1 | API skeleton (health, guest session, worker heartbeat, openapi) | DONE | Claude Opus 5 | `docs/specs/002-walking-skeleton/tasks.md` |
| T-002-2 | Web shell (nav, guest button, generated client) | DONE (implemented by Claude Sonnet 5, reviewed by Claude Opus 5) | Claude Sonnet 5 | `apps/web/`, `docs/tasks/T-002-2/report.md` |
| T-002-3 | Dockerfile + entrypoint + railway.json | DONE (image runs as api and worker locally) | Claude Opus 5 | `Dockerfile`, `apps/api/entrypoint.sh`, `railway.json` |
| T-002-4 | Deploy Railway + Neon | PLACEHOLDER: the user deploys, following `docs/runbooks/deploy.md` | user | same |
| T-002-5 | Modal LTX spike | PLACEHOLDER: the user sets Modal + R2 credentials; code in `apps/gpu/ltx_spike.py` | user | same |
| T-002-7 | Fix `<button>` nested in `<Link>` on HomePage | DONE | deepseek-flash | `apps/web/src/features/home/HomePage.tsx`, `docs/tasks/T-002-7/report.md` |
| T-003-0 | Design spec 003 + publish contract (writes the T-003-k briefs) | DONE (review by a different model pending) | Claude Opus 5 | `docs/specs/003-generation-core/{design,tasks}.md`, `docs/tasks/T-003-0/report.md` |
| T-003-1 | Contract + migrations: settings, models, migrations 0002/0003, domain rules, Protocols, S3 adapter, test fixtures | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/api/app/{models,domain,adapters}/`, `apps/api/migrations/versions/000{2,3}_*.py`, `apps/api/tests/conftest.py`, `docs/tasks/T-003-1/report.md` |
| T-003-2 | Repositories incl. claim/lease/reaper SQL | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/api/app/repositories/`, `apps/api/tests/test_{job_step,ledger}_repository.py`, `docs/tasks/T-003-2/report.md` |
| T-003-6 | Backends: local-motion ffmpeg, mock, modal/openrouter placeholders, selection, ffmpeg in image | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/api/app/adapters/`, `apps/api/tests/test_{local_motion_adapter,backend_selection}.py`, `docs/tasks/T-003-6/report.md` |
| T-003-3 | Presets, uploads, credits endpoints + guest grant | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/api/app/services/{presets,uploads,credits,guest_accounts}.py`, `apps/api/app/routers/{presets,uploads,credits}.py`, `docs/tasks/T-003-3/report.md` |
| T-003-4 | Jobs API: create, read, SSE events | DONE (deepseek-flash via DSH; `read_job_status` mypy cast fixed by the orchestrator) | deepseek-flash | `apps/api/app/services/{job_creation,job_views,job_event_broker,job_event_stream}.py`, `apps/api/app/routers/jobs.py`, `docs/tasks/T-003-4/report.md` |
| T-003-5 | Worker: claim loop, lease, completion, reaper | DONE (deepseek-flash via DSH; closed a design gap: a queued step whose job is already terminal is failed instead of re-claimed forever) | deepseek-flash | `apps/api/app/worker.py`, `apps/api/app/services/{step_claiming,generation_runs,step_completion,lease_reaper}.py`, `docs/tasks/T-003-5/report.md` |
| T-003-7 | End-to-end smoke (reviewer, different model) | DONE (deepseek-flash via DSH — SAME model as T-003-4/T-003-5, so self-review; independent re-run still required) | deepseek-flash | `scripts/smoke-generation`, `docs/tasks/T-003-7/report.md` |
| T-004-0 | Design spec 004 (writes the T-004-k briefs) | DONE (design by Claude Opus 5, tasks/briefs by deepseek-flash; review by a different model pending) | Claude Opus 5 + deepseek-flash | `docs/specs/004-create-video/{design,tasks}.md`, `docs/tasks/T-004-0/report.md` |
| T-004-1 | Web: shared types, copy, pure helpers, `ui/` primitives, vitest runner | DONE (deepseek-flash via DSH; regenerated the stale `api/generated/schema.d.ts`) | deepseek-flash | `apps/web/src/features/create-video/*.ts`, `apps/web/src/ui/*`, `apps/web/package.json`, `docs/tasks/T-004-1/report.md` |
| T-004-2 | Web: data hooks (guest, presets, selection, credits, history, upload) | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/web/src/features/create-video/{useGuestSessionRunner,usePresets,usePresetSelection,useCredits,sessionHistoryStore,useSessionHistory,putFileWithProgress,useImageUpload}.ts`, `docs/tasks/T-004-2/report.md` |
| T-004-4 | Web: panel components (drop zone, presets, prompt, generate) | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/web/src/features/create-video/{CreateVideoPanel,ImageDropZone,ImageThumbnail,PresetPicker,PresetCategoryChips,PresetCard,PromptField,GenerateSection}.tsx`, `apps/web/src/features/create-video/useClipboardImagePaste.ts`, `docs/tasks/T-004-4/report.md` |
| T-004-3 | Web: job hooks (idempotent create, SSE watcher + poll fallback) | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/web/src/features/create-video/{useCreateJob,jobStatusWatcher,useJobEvents,useElapsedSeconds,useActiveJob}.ts`, `docs/tasks/T-004-3/report.md` |
| T-004-5 | Web: page assembly, canvas views, `App.tsx` routes | DONE (deepseek-flash via DSH; browser-level verify-slice still to run) | deepseek-flash | `apps/web/src/features/create-video/*`, `apps/web/src/App.tsx`, `docs/tasks/T-004-5/report.md` |
| S-005..009 | Library · Explore · Share page `/v/{id}` · Credits + fake top-up · Create image | Explore designed as spec 006 (code-complete); Library designed as spec 005 (T-005-1..5 done); Share designed as spec 007 (T-007-1..5 done); Credits designed as spec 008 (code-complete); Image create designed as spec 009 (contract published, T-009-1..7 ready) | — | — |
| T-006-0 | Design spec 006 Explore: spec + design + tasks + 4 briefs (no contract change) | DONE | deepseek-flash | `docs/specs/006-explore/`, `docs/tasks/T-006-0/report.md` |
| T-006-1 | Web: shared preset hook (`api/presets.ts`), Explore copy/data, pure helpers + tests | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-006-1/report.md` |
| T-006-2 | Web: Explore hero + tool cards | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-006-2/report.md` |
| T-006-3 | Web: effect gallery cards, per-category sections, states | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-006-3/report.md` |
| T-006-4 | Web: assemble `ExplorePage`, route `/`, retire `HomePage` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-006-4/report.md` |
| T-005-0 | Design spec 005 Library + publish `GET /api/v1/jobs` (schema + 501 stub + openapi) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/specs/005-library/`, `docs/tasks/T-005-0/report.md` |
| T-005-1 | API: `GET /api/v1/jobs` list (repository + view builder + router + tests) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-005-1/report.md` |
| T-005-2 | Web data: move the guest runner to `api/guestSession.ts`, add `api/library.ts` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-005-2/report.md` |
| T-005-3 | Web copy + `formatCreatedAt` helper (+ test) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-005-3/report.md` |
| T-005-4 | Web UI: Library page, list, items, states, result panel, `?job=` selection | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-005-4/report.md` |
| T-005-5 | Assembly: route `/library` to `LibraryPage` + manual check | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-005-5/report.md` |
| T-007-0 | Design spec 007 Share page + publish `GET /api/v1/public/jobs/{job_id}` (schema + 501 stub + openapi) and the `/v/{job_id}` OG HTML plan | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/specs/007-share/`, `docs/tasks/T-007-0/report.md` |
| T-007-1 | API: public read `GET /api/v1/public/jobs/{job_id}` (view builder + router + tests) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-007-1/report.md` |
| T-007-3 | Web data + copy: `api/share.ts` (`usePublicJob`), `features/share/shareCopy.ts` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-007-3/report.md` |
| T-007-2 | API: serve `/v/{job_id}` HTML with OG meta tags (no JS) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-007-2/report.md` |
| T-007-4 | Web UI: `SharePage`, `ShareResult`, `ShareStates` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-007-4/report.md` |
| T-007-5 | Assembly + no-JS public check: route `/v/:jobId` to `SharePage` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-007-5/report.md` |
| T-008-0 | Design spec 008 Credits + publish `POST /api/v1/credits/topup` (`TopUpResponse` + 501 stub + openapi; D-013: P0, writes `TOPUP`) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/specs/008-credits/`, `docs/tasks/T-008-0/report.md` |
| T-008-1 | API: implement `POST /api/v1/credits/topup` (`TOPUP_CREDITS`, service lock→insert→sum, router body, tests) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-008-1/report.md` |
| T-008-2 | Web data: `api/credits.ts` (`useCreditsPage`) + regenerate the typed client | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-008-2/report.md` |
| T-008-3 | Web UI: `creditsCopy`, `CreditsBalanceCard`, `CreditsTopUpCard`, `CreditsPage` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-008-3/report.md` |
| T-008-4 | Assembly + manual check: route `/credits` to `CreditsPage` and prove the signed-out top-up | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-008-4/report.md` |
| T-009-0 | Design spec 009 Create image + publish the contract (`image_rules`, the image schemas, the 3 × 501 stubs, openapi; D-014: placeholder backend, real model P2) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/specs/009-image-create/`, `docs/tasks/T-009-0/report.md` |
| T-009-1 | API data: migration `0004`, `job.kind`/params/`output_image`/`job_image`, image repositories, video-only Library/read filters | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-1/report.md` |
| T-009-2 | Web shared data: watcher → `api/` (generic), shared balance, `api/imageOptions.ts`, `api/imageJobs.ts`, regenerate the client | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-2/report.md` |
| T-009-3 | API image backend: `ImageModelAdapter` port, PNG placeholder, placeholder/unconfigured adapters, `select_image_adapter` | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-3/report.md` |
| T-009-4 | API image surface: create service (one transaction + HOLD), owner read, public options, router bodies + tests | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-4/report.md` |
| T-009-5 | API worker image step: dispatch in `worker.py`, image run, image success completion (SETTLE + `output_image` + `job_image`) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-5/report.md` |
| T-009-6 | Web UI: `imageCreateCopy`, settings/cost helpers, page, composer, settings row, stage, result grid, failure view | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-6/report.md` |
| T-009-7 | Assembly + slice check: route `/create/image` to `CreateImagePage` and prove the flow end to end | DONE (deepseek-flash via DSH; found the image-job SSE 404 bug, see T-009-8) | deepseek-flash | `docs/tasks/T-009-7/report.md` |
| T-009-8 | Bug fix: SSE route authorises ownership-only so image jobs stream (openapi unchanged) | DONE (deepseek-flash via DSH) | deepseek-flash | `docs/tasks/T-009-8/report.md` |
| T-001-3 | Capture the missing flows (sign-up, generating/result, history, assets, pricing, share, signed-out explore) | PARTIAL (deepseek-flash via DSH): the supplied `reference-images/` set is a byte-identical duplicate of screenshots `01`–`16`, so 0/7 gaps are covered; still WAITING on real screenshots | deepseek-flash | `docs/tasks/T-001-3/report.md`, `docs/research/product-map.md` § Not yet observed |

## Scope (locked by D-012; the source of truth is `docs/research/product-map.md`)
- **P0, the core loop:**
  1. Public explore gallery of motion presets (signed out).
  2. One-click guest session.
  3. Upload an image, pick a preset, generate a video.
  4. Live progress over SSE.
  5. "My generations" library.
  6. `/v/{id}` share page with OG tags.
  7. Credits with HOLD/SETTLE/RELEASE and a fake top-up.
- **P1:** text→image, image face swap, Google OAuth, retry/failure polish, mobile layout.
- **P2:** community feed, moderation gate, model picker, video face swap.
- **CUT:** real payments, transcoding pipeline, teams, lipsync, self-managed GPU servers.

## Pre-hand-in checklist
- [ ] Live link opens in a signed-out browser — blocked on R2 + Railway deploy
- [x] `.agent-logs/` present (35 tracked files) and committed incrementally (`git log -- .agent-logs` → 36 commits); 17 late DSH tasks have no transcript (accepted gap, STATUS § BROKEN)
- [ ] Repo public — blocked on `gh auth login`
- [ ] README has labelled links (Live, Repo) — labels and honesty done; both URLs TBD until deploy + `gh auth login`
- [ ] Walkthrough ≤ 5 min, camera on
