# Brief T-008-2: Web data — `api/credits.ts` (`useCreditsPage`) + regenerate the typed client

You are the **implementer** for this one task (a small model is fine). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/008-credits/spec.md` (AC-2, AC-3, AC-4, AC-5, AC-7, AC-8)
- Design: `docs/specs/008-credits/design.md` §§ **API contract**, **Flow**, **Component tree** (Props), **Files**
- Contract: `packages/contracts/openapi.json` → `POST /api/v1/credits/topup` returns `TopUpResponse {amount: int, balance: int}`; `GET /api/v1/credits` returns `CreditsResponse {balance: int}`
- Patterns: `apps/web/src/api/library.ts` (the shared-hook shape: module-level fetch, `isMounted`/`requestId` race guards, no loading flash), `apps/web/src/api/guestSession.ts` (`GuestSessionSource`, `useGuestSessionRunner`, `RunWithGuestSession`), `apps/web/src/api/client.ts`

## Goal
The Credits page's single data owner: read the balance and perform the fake top-up, with the auto-guest + one-401-retry behaviour the rest of the app uses.

## Allowed files (touch nothing else)
- `apps/web/src/api/credits.ts` (new)
- `apps/web/src/api/generated/schema.d.ts` (regenerate — see below)
- `docs/tasks/T-008-2/report.md`

## Do this first
`TopUpResponse` is **not** in `apps/web/src/api/generated/schema.d.ts` yet: T-008-0 regenerated `packages/contracts/openapi.json` only. Run
```
npm --prefix apps/web run gen:api
```
before writing any code, and say in the report that you ran it and what it added (expect the `public`/`credits` diff to be additive only, no pre-existing shape changed). Then derive the type from the generated schema — **never** hand-write an API shape.

## What to build (`api/credits.ts`)
Exports, exactly these names:
- `export type TopUpResult = components["schemas"]["TopUpResponse"]`
- `export const TOP_UP_CREDITS = 100` — the display constant for the button label. The server is the source of truth; the *confirmation* uses the response's `amount`/`balance`, so a drift can never lie.
- `export type TopUpStatus = "idle" | "pending" | "done" | "error"`
- `export type BalanceStatus = "loading" | "known" | "error"`
- `export type CreditsPageState = { balanceStatus: BalanceStatus; balance: number | null; topUpStatus: TopUpStatus; grantedAmount: number | null; reload: () => void; topUp: () => void }`
- `export function useCreditsPage(session: GuestSessionSource): CreditsPageState`

Behaviour:
- `useGuestSessionRunner(session)` for both requests, so a signed-out visitor gets a guest session automatically and a `401` is retried **exactly once** after it is ensured (AC-2). This hook must import **no** `features/**` module and no create-video code.
- Mount → `apiClient.GET("/api/v1/credits")`. `200` with data → `balanceStatus: "known"`, `balance: data.balance`. Non-200, `session-failed`, or a throw → `"error"` (AC-7). Mirror `api/library.ts`: `isMountedRef` + `requestIdRef` guards, and a `hasBalanceRef` so a `reload()` after a known balance does **not** flash `"loading"` (AC-6).
- `reload()` re-reads the balance; it is the Retry callback and its identity must be stable (`useCallback`) so the effect does not loop.
- `topUp()`:
  - if `topUpStatus === "pending"`, do nothing (no double submit);
  - set `topUpStatus: "pending"`;
  - `apiClient.POST("/api/v1/credits/topup")` through the same runner;
  - `200` with data → `balance: data.balance`, `grantedAmount: data.amount`, `topUpStatus: "done"` (AC-4); keep `balanceStatus: "known"`;
  - anything else or a throw → `topUpStatus: "error"`, and the last known `balance` **stays** (AC-5);
  - pressing again after `"done"` must work (only `"pending"` blocks), so the user can top up twice.
- A `requestIdRef`/mounted guard applies to the top-up too, so a response landing after unmount is dropped.
- Keep the file ≤ 200 lines and every function ≤ 40 lines (eslint enforces both); complexity ≤ 8.

## Acceptance checks
- [ ] `api/credits.ts` exports `TopUpResult`, `TOP_UP_CREDITS`, `TopUpStatus`, `BalanceStatus`, `CreditsPageState`, `useCreditsPage`
- [ ] imports are only `react`, `./client`, `./generated/schema`, `./guestSession` — no `features/**`
- [ ] a signed-out session reads the balance only after the guest session is ensured; a `401` is retried once
- [ ] `200` on POST updates `balance` to the response's `balance` and records `grantedAmount` from `amount`; a failure leaves the last known balance and sets `"error"`
- [ ] `npm run test` still passes (there is no new unit test — the hook has no DOM-free pure helper; say so in the report)

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```
(`npm run typecheck` is `tsc -b` since T-000-6 and is a real gate; `tsc -b` inside `build` is the second one.)

## Out of scope
- Every `.tsx` component (T-008-3) and `App.tsx` (T-008-4).
- `features/create-video/useCredits.ts` — do **not** touch or import it; feature isolation forbids it and consolidating them is a P1 cleanup.
- The API, the contract, `ui/**`. If a string or field is missing, report it instead of inventing one.

## Report
Write `docs/tasks/T-008-2/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
