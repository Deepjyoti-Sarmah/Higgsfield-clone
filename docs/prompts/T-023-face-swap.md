# Brief T-023: face swap on the Modal GPU path

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Depends on: `docs/prompts/T-013-modal-adapter.md` (reuse its call shape and secrets)
- Reference implementation: `pixovid/infra/facefusion/server.py` (FastAPI wrapper around
  FaceFusion's `headless-run` CLI) and `pixovid/apps/backend/src/lib/facefusion.ts`
- Their max-likeness config (env-tunable) is documented in `pixovid/AGENTS.md` § infra/facefusion
- Port you must satisfy unchanged for images: `apps/api/app/adapters/image_model_adapter.py`
- Placeholder currently wired: `apps/api/app/adapters/placeholder_image_adapter.py`

## Goal
Add a real **face-swap** backend: given a base image and a face image, return one swapped image.
Prefer a Modal GPU function (same pattern as T-013) over a long-lived CPU service, because the
Modal path already exists. If a Modal function is not feasible, a self-hosted FaceFusion HTTP
service is the fallback — decide in `report.md` and justify it.

## Decisions to copy from pixovid
- **Wrapper, not a fork**: their FaceFusion 3.6.1 has no REST API, so they wrap `headless-run`
  in a tiny `POST /swap` + `GET /health`. Do the same if you use FaceFusion.
- **Model downloads**: pre-download the lite scope into a volume on first boot, gated by a
  marker file, so restarts are instant. Cache in the Modal Volume the same way T-012 caches weights.
- **Max-likeness config is env-tunable** (swapper model, pixel boost, enhancer on/off + blend,
  mask blur). Defaults should favour likeness; document the knobs in `.env.example`.
- **Diffusion-edit alternative**: pixovid can also do the swap through a diffusion image-edit
  model with a reference image, which honors a text `context` prompt. Mention it as the P2
  option; the P1 default is the deterministic swapper.

## Higgsfield-specific adaptation
- Face swap is a **new action**, so it needs a contract-first step: new schema + a 501 stub,
  then the adapter, then the UI. Charge it through the existing HOLD/SETTLE ledger.
- Reuse the guest session + upload flow; input is two uploaded images (base + face).
- Never run swap in pytest; use a fake adapter like `apps/api/tests/fakes/scripted_model_adapter.py`.

## Allowed files (touch nothing else)
- `apps/gpu/face_swap.py` (new Modal app) or `infra/facefusion/` if using the service
- `apps/api/app/adapters/{face_swap_adapter,backend_selection}.py`
- `apps/api/app/schemas/`, `apps/api/app/routers/`, `apps/api/app/services/` (new files only)
- `packages/contracts/openapi.json`, `apps/api/tests/` (new)
- `apps/web/src/features/face-swap/`, `apps/web/src/api/`, `apps/web/src/App.tsx`
- `.env.example`, `docs/specs/` (one new spec folder), `docs/tasks/T-023/{brief,report}.md`
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md`, `.agent-logs/*T-023*`

## Acceptance checks
- [ ] Unconfigured backend fails cleanly with `BackendNotConfiguredError` and refunds.
- [ ] A real probe (image A + face B → image C) returns a valid image and a real elapsed time.
- [ ] The contract diff is additive only; 501 stub answers before implementation.
- [ ] Swap is charged once (HOLD → SETTLE), refunded on failure (RELEASE).
- [ ] No secrets committed; model weights cached, not re-downloaded every call.
- [ ] `scripts/check-standards` passes; no file > 200 lines.

## Verify command (paste its full output in report.md)
```
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy
uv --directory apps/api run pytest -q tests/ -k "face_swap or face_swap_contract"
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```
plus one clearly-labelled paid/manual probe with the output image's dimensions pasted in.

## Out of scope
- Video face swap (P2 per `docs/research/product-map.md`), real payments, model picker.
- Changing the video `ModelAdapter` (T-013) beyond sharing the Modal call helper.

## Report
Write `docs/tasks/T-023/report.md` using `docs/templates/report.md`. ONE plain commit.
Do not mark your own work reviewed.
