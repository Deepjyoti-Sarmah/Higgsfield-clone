# Brief T-009-7: Assembly + slice check — route `/create/image` and prove the flow

You are the **reviewer/implementer** for this final task of spec 009. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/009-image-create/spec.md` (AC-1, AC-5, AC-6, AC-7, AC-8, AC-9, AC-11)
- Design: `docs/specs/009-image-create/design.md` §§ **Flow**, **Backend reality**, **Files**
- Existing: `apps/web/src/App.tsx` (the `create/image` route renders `<Placeholder title="Create image" />`), `apps/web/src/features/image-create/CreateImagePage.tsx` (T-009-6)
- Reports to cross-check: `docs/tasks/T-009-{1..6}/report.md`

## Goal
`/create/image` renders the real page, and the whole flow is exercised over HTTP: guest → create → progress → stored images → credits held then settled, with the placeholder backend honestly identified.

## Allowed files (touch nothing else)
- `apps/web/src/App.tsx` (edit: the `create/image` route only)
- `docs/tasks/T-009-7/report.md`

## Acceptance checks
- [ ] `App.tsx`'s `create/image` route renders `CreateImagePage`; every other route, the `AppShell` wiring, the `Placeholder` usage (now only `credits` if it remains) and all other imports stay exactly as they are
- [ ] `tsc -b` inside `npm run build` passes with the new route
- [ ] **Manual slice check** (record it; SKIPPED is acceptable only with a reason): with `docker compose up -d --wait db`, migrations applied, the API on `:8000` and a **worker running with the default `local-motion` backend**, prove with `curl` that
  1. `GET /api/v1/image-options` with **no cookie** → 200 with the five aspect ratios, two qualities, `max_count: 4` and both unit costs;
  2. a fresh guest (`POST /api/v1/auth/guest`, 201) has 60 credits; `POST /api/v1/image-jobs` with `{"prompt":"a cat","aspect_ratio":"16:9","quality":"standard","count":2,"idempotency_key":"t009-slice-1"}` → **202** `{status:"queued", credit_cost:20, image_count:2}` and `GET /credits` → **40** immediately (the HOLD);
  3. the same body + key again → the same `id` and the balance stays 40 (idempotent, one HOLD);
  4. poll `GET /api/v1/image-jobs/{id}` (and/or watch `GET /api/v1/jobs/{id}/events`) until terminal → `succeeded`, `image_urls` has **2** entries, `backend` is `local-motion`, and `GET /credits` is **40** (the SETTLE left the hold spent, not refunded);
  5. each `image_urls` entry downloads as a **real PNG** (`file`/magic bytes + the 16:9 dimensions);
  6. `GET /api/v1/jobs` (the video Library) does **not** list the image job, and `GET /api/v1/jobs/{id}` → **404**, while `GET /api/v1/image-jobs/{id}` → 200 (AC-11);
  7. a second guest with a 60-credit balance posting `quality:"high", count:4` (cost 60) → **202**, then a third `high`/4 → **402** with top-level `balance`/`required`, and no image job is created;
  8. `GET /create/image` is a routable SPA path (200 with the built `index.html`) and the served bundle contains the Create-image copy. If a browser is unavailable, say so — the curl-level check plus a bundle grep is the accepted substitute;
  9. stop the worker you started, and leave no stray process.
- [ ] cross-check the T-009-1…T-009-6 reports against the code: report any mismatch (truth hierarchy: running code wins), and confirm in particular that `services/generation_runs.py` and `services/step_completion.py` are **unchanged** and that the adapter really writes a PNG (not a renamed fixture).
- [ ] `scripts/check-standards` passes; no file over 200 lines, no function over 40 lines

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any change to `features/image-create/**`, `api/**`, `ui/**`, the API, the contract, the migration or the adapters. If something is broken there, **report it** — do not fix it in this task.

## Report
Write `docs/tasks/T-009-7/report.md` using `docs/templates/report.md`. Don't commit; the orchestrator does.
