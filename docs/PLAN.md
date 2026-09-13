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
| M3 | P0 slices (specs 003+) | 10h | TODO | each verified live via `verify-slice` |
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
| T-003-5 | Worker: claim loop, lease, completion, reaper | TODO (wave 3, after T-003-2 + T-003-6) | — | `docs/tasks/T-003-5/brief.md` |
| T-003-7 | End-to-end smoke (reviewer, different model) | TODO (wave 4) | — | `docs/tasks/T-003-7/brief.md` |
| T-004-0 | Design spec 004 (writes the T-004-k briefs) | DONE (design by Claude Opus 5, tasks/briefs by deepseek-flash; review by a different model pending) | Claude Opus 5 + deepseek-flash | `docs/specs/004-create-video/{design,tasks}.md`, `docs/tasks/T-004-0/report.md` |
| T-004-1 | Web: shared types, copy, pure helpers, `ui/` primitives, vitest runner | DONE (deepseek-flash via DSH; regenerated the stale `api/generated/schema.d.ts`) | deepseek-flash | `apps/web/src/features/create-video/*.ts`, `apps/web/src/ui/*`, `apps/web/package.json`, `docs/tasks/T-004-1/report.md` |
| T-004-2 | Web: data hooks (guest, presets, selection, credits, history, upload) | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/web/src/features/create-video/{useGuestSessionRunner,usePresets,usePresetSelection,useCredits,sessionHistoryStore,useSessionHistory,putFileWithProgress,useImageUpload}.ts`, `docs/tasks/T-004-2/report.md` |
| T-004-4 | Web: panel components (drop zone, presets, prompt, generate) | DONE (deepseek-flash via DSH) | deepseek-flash | `apps/web/src/features/create-video/{CreateVideoPanel,ImageDropZone,ImageThumbnail,PresetPicker,PresetCategoryChips,PresetCard,PromptField,GenerateSection}.tsx`, `apps/web/src/features/create-video/useClipboardImagePaste.ts`, `docs/tasks/T-004-4/report.md` |
| T-004-3 | Web: job hooks (idempotent create, SSE watcher + poll fallback) | TODO (wave 2, after T-004-1 + T-004-2) | — | `docs/tasks/T-004-3/brief.md` |
| T-004-5 | Web: page assembly, canvas views, `App.tsx` routes | TODO (wave 3, after T-004-2/3/4) | — | `docs/tasks/T-004-5/brief.md` |
| S-005..008 | Library · Explore · Share page `/v/{id}` · Credits + fake top-up | TODO (after 004) | — | — |
| T-001-3 | Capture the missing flows (sign-up, generating/result, history, assets, pricing, share, signed-out explore) | WAITING on user screenshots | user | `docs/research/product-map.md` § Not yet observed |

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
- [ ] Live link opens in a signed-out browser
- [ ] Repo public, `.agent-logs/` present, committed incrementally (`git log -- .agent-logs`)
- [ ] README has labelled links (Live, Repo)
- [ ] Walkthrough ≤ 5 min, camera on
