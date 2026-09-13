# STANDARDS: code rules (enforced; reviewers reject violations even when tests pass)

## Size and shape
- **≤ 200 lines per file**, tests included. Split files by responsibility, never by cutting at line 200.
- Functions stay around 40 lines at most, do one job, and nest at most 3 levels deep. Use early returns.
- Web: one component per file. API: one router / service / repository per resource.

## Naming over comments
- Names say what the code does:
  - Functions are verb + noun: `hold_credits`, `claim_next_step`, `useJobEvents`, `renderPresetCard`.
  - Booleans start with `is_` / `has_` / `can_`.
  - Banned names: `utils`, `helpers`, `manager`, `data`, `handle`, `process`, `misc`, `common`.
- Comments explain **why**, never **what**. **3 lines at most**, with no banner blocks and no docstrings that repeat the name.
- If code needs a long comment to be understood, rewrite the code.

## Structure (only the patterns that earn their place)
### API (`apps/api`)
```
routers/       thin HTTP: parse -> call service -> return schema
services/      use cases and transaction boundaries (never import FastAPI)
repositories/  SQLAlchemy queries (never contain business rules)
adapters/      external systems: ModelAdapter (modal | openrouter | mock), ObjectStorage (r2 | local)
schemas/       Pydantic request/response models (the contract)
domain/        job/step state machine (allowed transitions in ONE place), credit rules
```
- Routers never touch the DB directly.
- Dependencies are injected with FastAPI `Depends`. No module-level singletons except settings.
- Ports & adapters **only at real boundaries** (models, storage). Everything else is concrete code.
- **Strategy** picks the generation backend and the fallback. The **state machine** owns job status.

### Web (`apps/web`)
```
features/<feature>/   explore, create, library, share, credits: pages + feature components + hooks
ui/                   shared primitives: Button, Card, Modal, Uploader, ProgressBar, EmptyState
api/                  client generated from packages/contracts/openapi.json (no hand-written fetch)
```
- Hooks own the data (`useJob`, `useCredits`); components only render.
- Features never import another feature's internals. Anything shared moves to `ui/` or `api/`.

## Reuse without over-encapsulation
- **Rule of two:** extract a shared function or component the second time something repeats, not before.
- No interface with a single implementation, no wrapper that only forwards calls, no base class "for the future".
- Composition over inheritance.
- Before writing something new, search `ui/`, `services/`, `repositories/` and `adapters/`. List what you reused in `report.md`.

## Enforcement
| Check | Tool |
|---|---|
| file ≤ 200 lines, comment block ≤ 3 lines | `scripts/check-standards` |
| Python naming, complexity ≤ 8, statements | `ruff` (`N`, `C90`, `PLR0915`) |
| Python types on services/adapters | `mypy --strict` |
| API layer rules | `import-linter` contracts |
| TS size/complexity/naming/feature isolation | `eslint`: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `@typescript-eslint/naming-convention`, `no-restricted-imports` |
| TS types | `tsc --noEmit` |

## Spec tie-in
Every `design.md` lists each file it creates with a one-line responsibility. A file with no stated responsibility shouldn't exist.
