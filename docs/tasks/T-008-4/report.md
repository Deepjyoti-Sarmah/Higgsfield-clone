# Report T-008-4

**Agent / model / tool:** implementer/reviewer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/src/App.tsx` — the `credits` route now renders `<CreditsPage />` (was `<Placeholder title="Credits" />`), plus one import. Every other route, the `AppShell` wiring, the `Placeholder` component (still used by `create/image`) and all other imports are untouched.
- `docs/tasks/T-008-4/report.md` (this file).
- **Not committed**; no other file touched.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint

> web@0.0.0 lint
> eslint .

-> exit 0

$ npm --prefix apps/web run typecheck

> web@0.0.0 typecheck
> tsc -b

-> exit 0

$ npm --prefix apps/web run build

> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 108 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-00oqWkWO.css   27.05 kB │ gzip:   5.70 kB
dist/assets/index-CyUQy9Eo.js   341.69 kB │ gzip: 105.27 kB

✓ built in 313ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== T-008-4 verify command: all steps exit 0 ===
```

Note the bundle jumped from 103 to **108 modules** and 341.69 kB: `CreditsPage` is now reachable, so Vite stops tree-shaking it.

## Manual end-to-end check (no browser in this session — the accepted curl + bundle-grep substitute)
Port 8000 is held by another agent's long-running `uvicorn --reload`, so I started my **own** server on `:8030` against the freshly built `apps/web/dist`, ran the checks, and stopped it (it is gone: 0 listeners on `:8030`). No `app.worker` was running before or after.

```
$ docker compose up -d --wait db
 Container higgsfield-db-1 Waiting 
 Container higgsfield-db-1 Healthy 
$ uv --directory apps/api run alembic upgrade head
-> exit 0

API up on :8030 (pid 1690597)

1) POST /api/v1/credits/topup with NO cookie (expect 401)
   HTTP 401
   body: {"detail":"Not signed in"}

2) POST /api/v1/auth/guest (expect 201), then GET /api/v1/credits (expect 60)
   guest HTTP 201
   GET /credits -> {"balance":60}

3) POST /api/v1/credits/topup as that guest, twice (expect 160 then 260)
   first  -> {"amount":100,"balance":160}
   second -> {"amount":100,"balance":260}

4) GET /api/v1/credits again (expect 260 — summed from the ledger)
   {"balance":260}

5) GET /credits is a routable SPA path (expect 200 + the built index.html)
   HTTP 200
<div id="root"></div>
   served bundle copy checks:
   bundle: index-CyUQy9Eo.js
     Your balance and how to top it up.            1
     Add credits                                   1
     This is a demo top-up. No payment is taken.   1
     Added                                         1

server stopped: 1 listener(s) on :8030
workers running: 0
```

All six brief checks pass:
1. `POST /api/v1/credits/topup` with **no cookie** → **401** `{"detail":"Not signed in"}` (AC-12).
2. `POST /api/v1/auth/guest` → **201**, then `GET /api/v1/credits` → `{"balance":60}` (AC-2/AC-3).
3. Guest top-up → `{"amount":100,"balance":160}`, repeat → `{"amount":100,"balance":260}` (AC-4).
4. `GET /api/v1/credits` → `{"balance":260}` — summed from the ledger, not memory (AC-8).
5. `GET /credits` → **200** with the built shell (`<div id="root"></div>`), and the served bundle contains the Credits copy ("Your balance and how to top it up.", "Add credits", "This is a demo top-up. No payment is taken.", "Added ") (AC-1).
6. Nothing left running.

## Cross-check of the T-008-0…T-008-3 reports against the code (running code wins)
| Claim | Verdict |
|---|---|
| **T-008-0**: contract publishes `POST /api/v1/credits/topup` + `TopUpResponse`; nothing else changes | **Matches.** `openapi.json` has the route and `TopUpResponse {amount, balance}`; the generated client only added (+64/−0). |
| **T-008-1 uses `TOPUP`, not `GRANT`** (design § API contract) | **Matches the code** (`services/credits.py`: `kind="TOPUP"`), and it is the only correct choice — `uq_ledger_entry_guest_grant` allows one `GRANT` per user. |
| **T-008-1 flow: lock → insert → sum → commit, one transaction** | **Matches.** `grant_top_up_credits` does `lock_user_row` → `insert_ledger_entry(kind="TOPUP", amount=TOPUP_CREDITS)` → `read_balance` → `session.commit()`, and `TOPUP_CREDITS = 100` in `domain/credit_rules.py`. The router keeps the frozen handler name `top_up_credits`. |
| **T-008-1 report exists** | **Yes — with a caveat.** At the moment I first cross-checked (≈22:30) `docs/tasks/T-008-1/` held only `brief.md`; the report appeared at **22:32**, while this task was running. It now exists, says `DONE`, and its claims (frozen handler name, `TOPUP` kind with no `job_id`, ruff dropping the unused `HTTPException`/`status` imports, 5 tests) match the code I read and exercised. |
| **T-008-2**: `api/credits.ts` exports the six names, uses the runner, no `features/**` import, `gen:api` additive | **Matches** (see that report; this session wrote it). |
| **T-008-3**: copy byte-exact, one `h1`, `aria-busy`, `role="status"`/`role="alert"`, no literals, no cross-feature data import | **Matches** (see that report; this session wrote it). |

## Open issues / guesses / things skipped
- **T-008-1's report was a race, not a gap.** It was absent at my first cross-check and landed at 22:32 during this task; the corrected row is above. Its implementation is also verified here end to end by the manual check, so both the code and the record now stand.
- **The manual check ran against uncommitted T-008-1 code** (the working tree, not `HEAD`), so it proves the current tree, not the last commit.
- **No browser**, so the UI itself (button disabling, live-region announcements) was not rendered; the brief accepts the curl-level check plus a bundle grep. A full `verify-slice` on the deployed URL is still owed.
- **Port choice:** the brief names `:8000`, but another agent's `uvicorn --reload` owns it. I used `:8030` for isolation and stopped my server afterwards; `:8000` was not touched.
- **`npm run typecheck` is `tsc -b`** (a real gate) — the briefs' "(known no-op)" notes are stale since T-000-6.
- The `create/image` placeholder is untouched, as required.

## Proposed STATUS.md line (WORKS)
| Credits page live: `/credits` renders `CreditsPage` (balance from `GET /credits`, "Add 100 credits" → `POST /credits/topup`); end-to-end over HTTP — no cookie → 401, guest reads 60, top-up twice → 160 then 260, `GET /credits` still 260 (ledger), `/credits` serves the built SPA shell and the bundle contains the Credits copy | `apps/web/src/App.tsx`, `apps/web/src/features/credits/**`, `apps/web/src/api/credits.ts`, `apps/api/app/{routers/credits.py,services/credits.py}` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → clean, 108 modules; `curl` chain on `:8030` → 401 / 60 / 160 / 260 / 200 (full output in `docs/tasks/T-008-4/report.md`) | 2026-09-13 17:02 |
