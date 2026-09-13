# Higgsfield Clone: Spec-Driven Build Plan (process + product)

## Context
We're rebuilding higgsfield.ai within a 24h window. It's judged on **speed** (how much working product), **product judgement** (what we build first and what we cut) and **UX/UI**. The hand-in is a live public link, a public repo with `.agent-logs/` committed as we go, and a walkthrough of 5 minutes or less.
- **Capture:** the capture setup already passes (`CAPTURE-TEST.md`, `.claude/hooks/capture.py`).
- **Architecture:** the starting point is `architecture-mvp.excalidraw`: React SPA, FastAPI, Postgres as queue and pub/sub, SSE, ModelAdapter.
- **Screenshots:** the user will share screenshots of the real product flows.

Work will span many sessions and several agents on different models, so **the repo holds the state**: what's done, what's left, what's broken, and where the source of truth lives. Nothing depends on chat memory.

**Decisions locked with the user:**
- Generation: self-hosted open-weight models on Modal, with OpenRouter as the paid fallback (no fal.ai).
- OpenRouter budget: a **hard $5**.
- Face swap: **P1**, as an image-only edit via reference image.
- Deploy: **Railway + Neon + R2**.

Defaults I've chosen (tell me if you disagree):
- Credits with a fake "top-up" button, no real payments.
- Agents can be any model in any tool. Roles are defined by capability tier, and the task packet plus the `agent-run` capture wrapper make them interchangeable.

---

## 1. Repo layout for state and truth
```
AGENTS.md                  # entry point for every agent: read order, rules, definition of done, delegation brief
CLAUDE.md                  # "@AGENTS.md" (Claude Code auto-loads it)
docs/
  PLAN.md                  # milestones, clock, ordered task board (id · status · spec link · model)
  STATUS.md                # live truth: WORKS / BROKEN / NOT STARTED, each line -> file path + verify cmd + date
  DECISIONS.md             # append-only ADR-lite: decision · why · rejected alternatives
  WORKLOG.md               # append-only: time · agent/model · task id · files · result · commit sha
  research/
    screenshots/NN-<flow>-<step>.png  # numbered, never renamed (specs link to them)
    flows/<flow>.md        # observed behaviour only: steps, UI states, copy, limits, screenshot refs
    product-map.md         # every surface + P0/P1/P2/CUT verdict with one-line reason
  specs/NNN-<slug>/
    spec.md                # WHAT/WHY: story, acceptance criteria (Given/When/Then), out of scope, screenshot refs
    design.md              # HOW: endpoints, tables, UI states (empty/loading/error/success), files to touch
    tasks.md               # [ ] T-NNN-k · allowed files · verify command · model
  templates/               # spec.md / design.md / tasks.md / delegation-brief.md skeletons
  architecture/            # .excalidraw files moved here + architecture.md (kept current in text)
apps/web/                  # Vite + React + TS SPA (built and served as static files by FastAPI: one origin, no CORS)
apps/api/                  # FastAPI; `api` and `worker` entrypoints share one image
apps/gpu/                  # Modal app: LTX-2.5 distilled + LLaDA-Image Turbo endpoints
packages/contracts/        # openapi.json generated from FastAPI -> TS types for web
```

**Truth hierarchy** (put in AGENTS.md): running code and tests > `openapi.json` > `design.md` > `spec.md` > `PLAN.md` > chat.
- A STATUS line with no path and no verify command is invalid.
- "Done" means the verify command passed and tasks.md, STATUS and WORKLOG were updated in the same commit, and that commit includes `.agent-logs/`.

## 2. Spec-driven loop (per feature, vertical slices)
1. **Research:** screenshots go to `flows/<flow>.md`, observation only.
2. **Spec:** `spec.md` with testable acceptance criteria. **The user approves scope, which is the only human gate.**
3. **Design:** `design.md`. The FastAPI routes and schemas come first, so `openapi.json` exists before UI work starts.
4. **Tasks:** `tasks.md` with one agent run per task, disjoint file sets, and a verify command for each.
5. **Implement:** agents take tasks. Parallel work only when the file sets don't overlap, using worktrees. One commit per task.
6. **Verify:** check the acceptance criteria on the **deployed** URL, signed out. Update STATUS.

A slice = DB + API + UI + deployed. We never build a whole layer ahead of the others.

## 2b. Code standards (`docs/STANDARDS.md`, linked from AGENTS.md, every brief and the reviewer checklist)
These are enforced by tooling wherever possible. A rule nobody checks gets broken by the third agent.

**Size and shape**
- **≤200 lines per file**, tests included. If a file grows past that, split it by responsibility, never by cutting it at line 200.
- Functions stay around 40 lines at most with one job, and nesting goes at most 3 levels deep (use early returns).
- One component per file in web code, and one router/service/repository per resource in the API.

**Naming over comments**
- Names say what the code does:
  - Functions are verb + noun: `hold_credits`, `claim_next_step`, `useJobEvents`, `renderPresetCard`.
  - Booleans start with `is_/has_/can_`.
  - Nothing called `utils`, `helpers`, `manager`, `data`, `handle`, `process`.
- Comments explain *why*, not *what*. A comment is **at most 3 lines**, with no banner blocks and no docstrings that repeat the name. If code needs a 10-line comment, rewrite the code.

**Structure and patterns** (only the ones that earn their place)
- API is layered: `routers/` (thin HTTP: parse, call, return) → `services/` (use cases, transactions) → `repositories/` (SQLAlchemy queries) → `adapters/` (external systems).
- Routers never touch the DB directly, and services never import FastAPI.
- **Ports & adapters only at real boundaries:** `ModelAdapter` (modal / openrouter / mock), `ObjectStorage` (R2 / local). Everything else is concrete code.
- Dependencies are injected with FastAPI `Depends`, so there are no module-level singletons beyond settings.
- **State machine** for job and step status in one module with explicit allowed transitions. **Strategy** for picking a backend and falling back.
- Web is organised by feature (`features/explore`, `features/create`, `features/library`, `features/share`):
  - Shared primitives go in `ui/` (Button, Card, Modal, Uploader, ProgressBar, EmptyState).
  - Data lives in hooks (`useJob`, `useCredits`), and components render.
  - The API client is generated from `openapi.json`, with no hand-written fetch calls.

**Reuse without over-encapsulation**
- **Rule of two:** extract a shared component or function the second time something repeats, not before.
- No interfaces with one implementation, no wrapper that only forwards calls, no base classes "for the future". Composition over inheritance.
- Before writing something new, search `ui/`, `services/` and `repositories/` for an existing piece, and list what was reused in the task report.

**Enforcement** (`scripts/check-standards` runs in pre-commit and in the `task-run` verify step):
- A custom check that fails on any source file over 200 lines or any comment block over 3 lines.
- Python: `ruff` (naming `N`, complexity `C90` max 8, `PLR0915`), `mypy --strict` on `services/` and `adapters/`, and `import-linter` contracts for the layer rules.
- TS: `eslint` with `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `@typescript-eslint/naming-convention`, and `no-restricted-imports` so features can't import each other's internals. `tsc --noEmit`.
- **Spec tie-in:** every `design.md` lists the files it creates with a one-line responsibility each. A file with no stated responsibility shouldn't exist. The reviewer rejects diffs that break STANDARDS even when the tests pass.

## 3. Skills and subagents
**Skills** (`.claude/skills/<name>/SKILL.md`, each one short):
- `research-flow`: screenshots in, `flows/<flow>.md` and the product-map rows out.
- `spec-new`: scaffold `specs/NNN-slug/` from templates plus research refs, and add it to PLAN.md.
- `task-run`: read AGENTS.md, then the spec, design and task. Touch only the allowed files, run the verify command, update tasks, STATUS and WORKLOG, then commit including `.agent-logs/`.
- `verify-slice`: acceptance criteria on the live URL in a signed-out browser (claude-in-chrome), with screenshots in `docs/verification/`.
- `handoff`: end of session. Refresh STATUS, the next 3 tasks and blockers, then commit. This is how context survives between runs.

**Agents are model- and tool-agnostic.** Any model in any tool can take a task: Claude (any tier), GPT or Codex, Gemini, DeepSeek/Qwen through OpenRouter, a local model, and so on. The process never assumes a particular model. Everything an agent needs is in plain files.
- **`AGENTS.md`** is the cross-tool convention, read by Claude Code (via `CLAUDE.md`), Codex, Cursor, Gemini CLI, Aider and others. Skills are plain markdown procedures in `docs/playbooks/`. `.claude/skills/` only holds thin wrappers that point at them.
- **Roles are defined by capability tier, not by model name.** Which model fills each role goes in `docs/PLAN.md` and can change at any time.

| Role | Needs | Scope | Example fills |
|---|---|---|---|
| Orchestrator | strongest reasoning, long context | specs, design, contracts, splitting and merging tasks, risky core: ledger, claim/lease, SSE fan-out, Modal adapter | Claude Opus, GPT-5-class, Gemini Pro |
| Implementer | solid coding | one well-specced task (endpoint, component, page) | Claude Sonnet, Codex, DeepSeek/Qwen coder via OpenRouter |
| Reviewer | strong reasoning, **a different model from the implementer** | diff vs acceptance criteria | any top model other than the one that wrote the code |
| Scout | cheap and fast | cataloguing screenshots, grep, lint, doc sync | Haiku, Gemini Flash, small OpenRouter models |

**The task packet is the whole interface.** The orchestrator writes `docs/tasks/T-NNN-k/brief.md` from `docs/templates/delegation-brief.md`:
Task id · spec/design links · allowed files · contract (openapi path) · acceptance checks + verify cmd · out of scope · required report format.
The agent writes `docs/tasks/T-NNN-k/report.md`: files changed, verify output pasted, open issues, proposed STATUS line. Anyone can pick up any packet without chat history.

**Trust nothing reported.** The orchestrator re-runs the verify command itself, and the reviewer must be a different model, before the task counts as done.

**Capture across tools** (the assignment requires every agent's prompts and responses in `.agent-logs/`):
- **Claude Code sessions and subagents:**
  - The existing hooks cover the main session.
  - Add `SubagentStop` (subagent final output) and `PreToolUse` on `Agent` (the delegation prompt), because sidechains are currently skipped.
- **Every other tool or model:** launch it only through `scripts/agent-run <tool> <task-id>`. The script sends `brief.md` as the prompt, captures stdout as the response, and appends both in the same `[LOG_ENTRY]` format to `.agent-logs/<date>_<tool>-<task-id>.md`. It supports CLIs with a non-interactive mode (`codex exec`, `gemini -p`, `aider --message`) and direct OpenRouter chat calls.
- **Interactive tools that can't be wrapped** (e.g. Cursor chat): export the transcript into `.agent-logs/` before the task is committed. `task-run` refuses to mark done without a log file for that task id.

## 4. Model strategy (no fal.ai; $5 hard cap on OpenRouter)
Everything sits behind ONE `ModelAdapter` Protocol (`submit(step) -> external_id`, then a webhook or poll gives the result). `GENERATION_BACKEND=modal|openrouter|mock`, with automatic fallback modal → openrouter only while budget remains.

| Capability | Primary (≈$0) | Fallback (paid) | Dev/tests |
|---|---|---|---|
| Image→video, text→video | **LTX-2.5 distilled fp8** (open weights, free under $10M ARR) on **Modal** ($30/mo free credits, H100 ≈ $3.95/h, scale-to-zero) | OpenRouter **Seedance 2.0 Mini** $0.034/s (5s ≈ $0.17) | `MockAdapter` (sample mp4s) |
| Text→image | **LLaDA-Image Turbo** (6B, 4 steps) on the same Modal app | OpenRouter **Seedream 4.5** $0.04 | Mock |
| Face swap (P1, images only) | OpenRouter **Nano Banana 2 Lite** multi-image edit, consent checkbox ("this is my face") | none | Mock |

**Budget guards** (the link is public):
- Set a $5 credit limit on the OpenRouter key itself.
- Server-side `PAID_BUDGET_CENTS=500` counter in the ledger. When it's exhausted, the paid fallback is disabled.
- Guests get 1 video + 3 images.
- Global daily generation cap.
- Explore gallery previews are pre-generated once and stored in R2.
- Walkthrough runs on Modal-generated clips.

**Modal realities to plan around:**
- Cold start loads a 22B model (~1–2 min), so keep a warm container only during the demo window.
- Generation is async: Modal calls back `POST /hooks/modal` with the R2 key.
- Spike it FIRST (M2) because it's the biggest risk.
- Verify LLaDA-Image's licence before shipping it; if it's unclear, text→image falls back to OpenRouter.

**Rejected** (goes in DECISIONS.md):
- **InternLumina-U2:** weights and licence "coming soon".
- **OpenVDN:** needs 8×B200.
- **Viggle-Animate:** 33B, 96GB at full precision, MiniMax community licence, too heavy for 24h.
- **InsightFace inswapper:** non-commercial weights.
- **HF ZeroGPU:** 5 min/day, long cold starts, dev only.

## 5. Architecture deltas vs `architecture-mvp.excalidraw`
- **Hosting:** Railway runs `api` (FastAPI, also serving the built SPA and `/v/{id}` OG pages, so one origin with no CORS) and `worker` (same image), plus Neon Postgres and R2. No Cloudflare domain needed.
- **Workers:** one worker pool (a claim loop on `job_step` with lease + reaper). Split pools and media workers (ffmpeg) are cut; provider outputs are served directly, with the poster frame taken from the provider or the first frame generated in the browser.
- **Modal** is a provider behind the ModelAdapter, not part of our own infrastructure.
- **Auth:** guest JWT in an httpOnly cookie for P0; Google OAuth in P1.
- **Kept from "STILL DO NOT CUT":** HOLD/SETTLE/RELEASE ledger, lease + reaper, idempotency key, separate worker process, ModelAdapter, `job_step` table, OG share page, SSE via one LISTEN connection per replica with a 5s poll fallback.

## 6. Product scope (draft; finalised in `product-map.md` after the screenshots)
- **P0, the core loop:**
  1. Public explore page with a gallery of motion presets (signed out).
  2. One-click guest session.
  3. Upload an image, pick a preset, generate a video.
  4. Live progress over SSE.
  5. "My generations" library.
  6. `/v/{id}` share page with OG tags.
  7. Credits with HOLD/SETTLE/RELEASE and a fake top-up.
- **P1:** text→image, image face swap, Google OAuth, retry/failure polish, mobile layout.
- **P2:** community feed, moderation gate, model picker, video face swap.
- **CUT:** real payments, transcoding pipeline, teams, lipsync, self-managed GPU servers.

## 7. Milestones (clock kept in PLAN.md)
| M | What | Box | Exit criterion |
|---|---|---|---|
| M0 | Scaffolding: AGENTS.md, docs skeleton, templates, 5 playbooks (+ thin `.claude/skills` wrappers), role table, `scripts/agent-run`, SubagentStop + PreToolUse capture, move diagrams | 1h | committed; one Claude subagent AND one non-Claude agent (via `agent-run`) both verified logged in `.agent-logs/` |
| M1 | Research: user shares screenshots → `research-flow` per flow → `product-map.md` | 1.5h | scope approved by user |
| M2 | Walking skeleton LIVE + Modal spike: monorepo, Neon, R2, Railway api+worker, guest auth, health page; Modal LTX endpoint generates 1 clip from a curl call | 3h | public URL opens signed out; clip in R2 |
| M3 | P0 slices as specs 001–007, in the order listed above | 10h | each verified live via `verify-slice` |
| M4 | P1 slices as time allows | — | same |
| M5 | Ship: signed-out pass, README with labelled links, repo public, walkthrough script ≤5 min | 2h | pre-hand-in checklist all ticked |

## Verification
- **Per task:** the verify command in tasks.md (pytest for API, ledger, claim/lease; vitest for UI; curl against Railway).
- **Per slice:** `verify-slice` on the live URL in a fresh signed-out browser, with screenshots in `docs/verification/`.
- **Budget:** a test asserting the paid fallback is refused once `PAID_BUDGET_CENTS` is spent. Check the OpenRouter key limit in its dashboard.
- **Pre-hand-in:**
  - The live link opens signed out.
  - The repo is public with `.agent-logs/`.
  - `git log` shows logs committed incrementally.
  - The walkthrough is ≤5 min with the camera on.
