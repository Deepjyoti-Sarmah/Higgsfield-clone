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
| T-002-7 | Fix `<button>` nested in `<Link>` on HomePage | READY FOR HANDOFF (small model) | — | `docs/tasks/T-002-7/brief.md` |
| T-003-0 | Design spec 003 + publish contract (writes the T-003-k briefs) | READY FOR HANDOFF (strongest model) | — | `docs/tasks/T-003-0/brief.md` |
| T-004-0 | Design spec 004 (writes the T-004-k briefs) | READY FOR HANDOFF after T-003-0 | — | `docs/tasks/T-004-0/brief.md` |
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
