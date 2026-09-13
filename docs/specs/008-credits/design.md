# Design 008: Credits + fake top-up

**Spec:** `docs/specs/008-credits/spec.md` (APPROVED)
**Backend:** `docs/specs/003-generation-core/design.md` § Credit rules and job states (the ledger, the one-time guest `GRANT` 60, `HOLD`/`SETTLE`/`RELEASE`).
**Contract:** **ONE** new route — `POST /api/v1/credits/topup` — plus the `TopUpResponse` schema. `GET /api/v1/credits` and every other existing path/schema stay byte-identical (AC-11). **No migration:** the `TOPUP` kind, the amount-sign check and `ix_ledger_entry_user` already exist.
**Web patterns:** `docs/specs/005-library/design.md` (a page whose data comes from one `api/` hook + the guest runner), `docs/specs/007-share/design.md` (dedicated response schemas, Files table), `docs/STANDARDS.md` § Styling.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Route | Component tree, Files | T-008-4 |
| AC-2 Signed out | Flow 1–2, `api/guestSession.ts` | T-008-2 |
| AC-3 Balance | API contract, `useCreditsPage` | T-008-1 (api), T-008-2 (hook) |
| AC-4 Top-up | API contract, Flow 3–5 | T-008-1 (api), T-008-2/3 (web) |
| AC-5 Action states | Copy § Top-up, `CreditsTopUpCard` | T-008-2, T-008-3 |
| AC-6 Loading | Copy § States, `CreditsBalanceCard` | T-008-3 |
| AC-7 Error | Copy § States, `useCreditsPage` status | T-008-2, T-008-3 |
| AC-8 Persistence | Data (balance = `SUM(ledger)`) | T-008-1 |
| AC-9 Accessibility | Accessibility | T-008-3 |
| AC-10 Read-only safety | API contract (no body), Flow | T-008-1 |
| AC-11 Contract discipline | API contract, Data | T-008-0, T-008-1 |
| AC-12 Signed-out mutation | API contract (401) | T-008-1 |

## API contract (the only contract change)
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/api/v1/credits/topup` | **no body** | **200** `TopUpResponse {amount: int, balance: int}` — `amount` = credits just granted (`TOPUP_CREDITS` = **100**), `balance` = the caller's new summed balance | **401** `ErrorResponse` signed out · **422** (the optional `session` cookie parameter, identical to `GET /credits`) |

Ownership: `require_current_user`; the row is written for the caller only and the balance is read for the caller only. There is no path/query/body parameter. The contract is `200`/`401`/`422`, and the `422` comes only from the optional `session` cookie that `require_current_user` declares — byte-for-byte the same response set the existing `GET /credits` already has.

### `TopUpResponse` (new; frozen by T-008-0)
| Field | Type | Meaning |
|---|---|---|
| `amount` | int | credits granted by this call (`100`); lets the UI's confirmation be truthful even if the client's display constant ever drifts |
| `balance` | int | the caller's balance **after** the grant, summed inside the same transaction |

**Why no request body.** The bundle size is a server constant, so a caller cannot mint an arbitrary amount (AC-10) and there is nothing to validate. A body would only add a 422 surface and a way to get the number wrong.

**Why `TOPUP`, not `GRANT`.** The ledger's `uq_ledger_entry_guest_grant` is a **partial unique index on `(user_id) WHERE kind = 'GRANT'`** — it allows exactly one welcome grant per user, which every guest already received at account creation (`services/guest_accounts.py`). A second `GRANT` would raise a unique violation, so a top-up must not reuse that kind. `TOPUP` is already:
- in the DB check `ck_ledger_entry_kind` (`GRANT, HOLD, SETTLE, RELEASE, TOPUP`) and in `domain/credit_rules.LedgerKind`;
- covered by `ck_ledger_entry_amount_sign` (`TOPUP` → `amount > 0`);
- covered by `ck_ledger_entry_job_link`, which requires `job_id IS NULL` for `TOPUP` — exactly "free credits that belong to no job";
- unconstrained in count, which is the intended "press it again" behaviour.
It has never been used, so this route is the first writer. **No migration, no model change, no contract change to `GET /credits`.**

**Why not extend `GET /api/v1/credits` (e.g. add `topup_amount` or history)?** That would change an existing schema, which AC-11 forbids. The page therefore carries the display constant `TOP_UP_CREDITS = 100` on the client; the *confirmation* uses the server's `amount`, so the two can drift without ever lying to the user (see Risks).

## Data
**Nothing changes.** Balance is `SUM(ledger_entry.amount) WHERE user_id = :id` (`repositories/ledger.py::sum_user_balance`) — invariant 2: the balance is never stored on the user. `ix_ledger_entry_user (user_id)` already serves the sum. `created_at` is not read in P0, because history is out of scope. No table, column, index or migration.

## Flow
1. `/credits` mounts → `useCreditsPage(session)` reads the session from the outlet context (`SessionContextValue`, the HomePage/Create-video precedent). Signed out → it calls `startGuestSession()` through the moved `api/guestSession.ts` runner, so the page never opens a login wall (AC-2).
2. `apiClient.GET("/api/v1/credits")`; a `401` is retried once after the guest session is ensured; non-200 or a throw → `balanceStatus: "error"` (AC-7); `200 {balance}` → `"known"` (AC-3).
3. Top-up press → `topUpStatus: "pending"`, the button disables (AC-5) → `apiClient.POST("/api/v1/credits/topup")` through the same runner.
4. API: `top_up_credits` (router, the frozen handler name) → `require_current_user` → service `grant_top_up_credits(session, user_id)` (named apart from the handler so the two never collide on import):
   1. `lock_user_row(session, user_id)` — serialises this user's credit writes, so two parallel presses cannot return a stale balance;
   2. `insert_ledger_entry(kind="TOPUP", amount=TOPUP_CREDITS)`;
   3. `read_balance(session, user_id)` (the `SUM` above, same transaction);
   4. `commit` → `TopUpResult(amount, balance)` → `TopUpResponse`.
   One transaction, one row; nothing else is touched.
5. Web: `200` → the hook stores the returned `balance` and `amount`, `topUpStatus: "done"` (AC-4/AC-8); anything else → `"error"` and the last known balance stays on screen (AC-5).
6. Reload re-reads the balance from the ledger, so the top-up survives (AC-8). The page makes no other request and mutates nothing else (AC-10).

## Component tree
```
CreditsPage                    (features/credits/CreditsPage.tsx)
├── title + subtitle           (creditsCopy)
├── CreditsBalanceCard         loading | error | known   (CreditsBalanceCard.tsx)
│   └── ui/EmptyState + ui/Button  (error variant, "Retry")
└── CreditsTopUpCard           idle | pending | done | error   (CreditsTopUpCard.tsx)
    └── ui/Button              ("Add 100 credits")
```
- `CreditsPage` props: none — it calls `useOutletContext<SessionContextValue>()` and `useCreditsPage(session)` once.
- `CreditsBalanceCard` props: `{ status: "loading" | "error" | "known"; balance: number | null; onRetry: () => void }`.
- `CreditsTopUpCard` props: `{ status: "idle" | "pending" | "done" | "error"; amount: number | null; balance: number | null; onTopUp: () => void }`.
- No component fetches. `api/credits.ts` is the single data owner.

## Copy (`creditsCopy.ts`, one object; no inline literals in components)
| Key | Value |
|---|---|
| `page.title` | "Credits" |
| `page.subtitle` | "Your balance and how to top it up." |
| `balance.label` | "Balance" |
| `balance.value(balance)` | `` `${balance} credits` `` |
| `states.loading.srText` | "Loading your credits" |
| `states.error` | title "We couldn't load your credits." · body "Check your connection and try again." · action "Retry" |
| `topup.title` | "Add credits" |
| `topup.description` | "This is a demo top-up. No payment is taken." |
| `topup.action(amount)` | `` `Add ${amount} credits` `` |
| `topup.pending` | "Adding credits..." |
| `topup.done(amount, balance)` | `` `Added ${amount} credits. New balance: ${balance}.` `` |
| `topup.error` | "We couldn't add credits." |
| `topup.retry` | "Try again" |

All copy is pure ASCII (the repo already had to escape one design-mandated middle dot in spec 007; nothing here needs one). The two templates take their numbers as arguments; only the *button label* uses the client constant `TOP_UP_CREDITS`, the confirmation uses the API's `amount`/`balance`.

## Accessibility
- Exactly one `h1` (`page.title`); the balance label is a `<p>`/`<dt>`-level text, and the number is rendered as text inside it — never a colour swatch (AC-9).
- `CreditsBalanceCard`'s loading region carries `aria-busy="true"` plus an `sr-only` `states.loading.srText` (AC-6).
- The top-up is `ui/Button` (a real `<button>` with the shared `focus-visible` ring); `pending` uses `isLoading` + `disabled` so it cannot double-submit (AC-5, AC-9).
- `pending`/`done` render in a `role="status"` (polite) live region; `topup.error` renders in `role="alert"`, matching the create-video pattern (AC-9).
- States are text (`EmptyState` title + body), so nothing is conveyed by colour alone.

## Files (each ≤ 200 lines; one component per file; paths relative to the repo root)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `apps/api/app/schemas/credits.py` | Edit | T-008-0 | `+ TopUpResponse` (`CreditsResponse` untouched) |
| `apps/api/app/routers/credits.py` | Edit | T-008-0 → T-008-1 | T-008-0 adds the 501 stub; T-008-1 replaces the body keeping name/signature/responses |
| `apps/api/app/domain/credit_rules.py` | Edit | T-008-1 | `+ TOPUP_CREDITS = 100` next to `GUEST_GRANT_CREDITS` |
| `apps/api/app/services/credits.py` | Edit | T-008-1 | `+ TopUpResult` + `grant_top_up_credits(session, user_id)` (lock → insert → sum) |
| `apps/api/tests/test_credits_topup_api.py` | New | T-008-1 | 401, +100 per call, the ledger row shape, persistence, `GET /credits` agreement |
| `apps/web/src/api/credits.ts` | New | T-008-2 | `TopUpResult`, `TOP_UP_CREDITS`, `CreditsPageState`, `useCreditsPage(session)` |
| `apps/web/src/api/generated/schema.d.ts` | Edit | T-008-2 | regenerated from `openapi.json` (`+TopUpResponse`, `+the topup operation`) |
| `apps/web/src/features/credits/creditsCopy.ts` | New | T-008-3 | every user-visible Credits string |
| `apps/web/src/features/credits/CreditsBalanceCard.tsx` | New | T-008-3 | balance known / loading / error (+ Retry) |
| `apps/web/src/features/credits/CreditsTopUpCard.tsx` | New | T-008-3 | top-up idle / pending / done / error |
| `apps/web/src/features/credits/CreditsPage.tsx` | New | T-008-3 | wire the hook → title, balance card, top-up card |
| `apps/web/src/App.tsx` | Edit | T-008-4 | the `credits` route → `CreditsPage` (replaces the placeholder) |
| `docs/tasks/T-008-{0..4}/report.md` | New | each | per-task report |

## Reused
- API: `require_current_user`, `get_session`, `lock_user_row` (`repositories/users.py`), `insert_ledger_entry` + `sum_user_balance` (`repositories/ledger.py`), `read_balance` (`services/credits.py`), `ErrorResponse`, `LedgerKind`/the existing `TOPUP` check constraints and partial indexes. No new repository, no migration.
- Web: `apiClient` + `api/generated/schema.d.ts` (never a hand-written API shape), the moved guest-session runner (`api/guestSession.ts`) for the auto-guest + single-401-retry behaviour, `ui/Button`, `ui/EmptyState`, `styles.css` tokens, the eslint limits, `SessionContextValue` from `features/session` (the shared session context every page reads).
- The `api/library.ts` hook shape: module-level fetch returning a typed outcome, `isMountedRef`/`requestIdRef` race guards, and the "do not flash loading once we have data" rule.
- **Not** reused: `features/create-video/useCredits.ts` — STANDARDS forbids a feature importing another feature's internals, and that hook is shaped for the Generate panel (`BalanceView`, `guest-offer`). Consolidating the two into `api/credits.ts` is a P1 cleanup, recorded below.

## Risks
- **Fake money is unbounded.** The button can be pressed forever. Accepted for P0 because the money is fake, because `POST /api/v1/auth/guest` is already an unbounded faucet (60 per new guest), and because the real guard is D-003's `PAID_BUDGET_CENTS` server counter plus the `GENERATION_BACKEND=mock` kill switch. A cap is P1 and is called out as such in the spec's Open questions.
- **Client/server constant drift.** The button label needs `100` before any response exists, so `TOP_UP_CREDITS` is duplicated on the client. Mitigation: the *confirmation* renders the API's `amount` and `balance`, so a drift shows a truthful result; a P1 change could return the bundle size from `GET /credits` (a schema change, hence out of scope here).
- **No history, so the ledger is invisible in the UI.** Deliberate P0 cut; P1 adds `GET /api/v1/credits/entries`.
- **Two hooks named for the same resource.** `useCredits` (create-video, feature-internal) and `useCreditsPage` (shared `api/`, the Credits page) coexist. The distinct name is intentional to avoid a confusing import; P1 retires the create-video one.
- **The 501 stub window.** Between T-008-0 and T-008-1 the route is live but not implemented, so a full `verify-slice` must run after T-008-1. The stub keeps `openapi.json` byte-identical either way, which is the point of freezing it first.
- **Concurrency.** Two parallel top-ups are serialised by `lock_user_row`, and the returned balance is summed inside the same transaction, so neither response can be stale or lose a row.
- **A guest can lose the credits with the cookie.** The balance belongs to the session cookie, so clearing cookies means a new guest with a fresh 60. Same trade-off the rest of the app already makes; real accounts are out of scope.
