# Report T-008-2

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/src/api/credits.ts` (new) — the Credits page's single data owner.
- `apps/web/src/api/generated/schema.d.ts` (regenerated with `npm --prefix apps/web run gen:api`).
- `docs/tasks/T-008-2/report.md` (this file).
- **Not committed**; no other file touched (no `features/**`, no `ui/**`, no API).

## `gen:api` first (as instructed)
`TopUpResponse` was indeed absent from the generated client. Before running it the file was clean vs `HEAD`; after it the diff is **+64 insertions, 0 deletions** and purely additive:

- `paths["/api/v1/credits/topup"]` (post → `top_up_credits_api_v1_credits_topup_post`)
- `components["schemas"]["TopUpResponse"] { amount: number; balance: number }`
- `operations["top_up_credits_api_v1_credits_topup_post"]` (200 → `TopUpResponse`, 401 → `ErrorResponse`, 422)

No pre-existing path, schema or operation changed.

## What was built
`api/credits.ts` exports exactly the required names: `TopUpResult` (= `components["schemas"]["TopUpResponse"]`, never hand-written), `TOP_UP_CREDITS = 100`, `TopUpStatus`, `BalanceStatus`, `CreditsPageState`, `useCreditsPage(session)`.

- Imports are only `react`, `./client`, `./generated/schema`, `./guestSession` — **no `features/**`** and no create-video code.
- Both requests go through `useGuestSessionRunner(session)`, so a signed-out visitor gets a guest session first and a `401` is retried exactly once (AC-2).
- Mount reads `GET /api/v1/credits`; `200 {balance}` → `known` + the number, anything else / `session-failed` / a throw → `error` (AC-3, AC-7).
- The hook mirrors `api/library.ts`: `isMountedRef` + `requestIdRef` race guards and a `hasBalanceRef` so a `reload()` after a known balance does **not** flash `loading` (AC-6). `reload` is `useCallback`-stable so the effect cannot loop.
- `topUp()` refuses re-entry while `pending` (an `isPendingRef`), sets `pending`, POSTs through the same runner, and on `200` stores the response's `balance`, records `grantedAmount` from `amount`, keeps `balanceStatus: "known"` and sets `done` (AC-4). Anything else leaves the last known balance untouched and sets `error` (AC-5). Pressing again after `done` works — only `pending` blocks.
- The top-up has its own mounted/request-id guard, so a response landing after unmount is dropped.

To stay inside `max-lines-per-function: 40` the state is split into two internal hooks in the same file (`useBalanceState`, `useTopUpState`) that `useCreditsPage` composes; the public surface is exactly the required one.

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

$ npm --prefix apps/web run test

> web@0.0.0 test
> vitest run


 RUN  v5.0.0 /home/deepjyoti/Documents/Assigment/Higgsfield/apps/web

 ✓ src/features/explore/groupPresetsByCategory.test.ts (6 tests) 18ms
 ✓ src/features/create-video/elapsedTime.test.ts (3 tests) 12ms
 ✓ src/features/create-video/sessionHistoryStore.test.ts (10 tests) 33ms
 ✓ src/features/create-video/canvasPhase.test.ts (17 tests) 28ms
 ✓ src/features/explore/recreateHref.test.ts (4 tests) 12ms
 ✓ src/features/create-video/imageFileRules.test.ts (4 tests) 13ms
 ✓ src/features/library/formatCreatedAt.test.ts (4 tests) 14ms
 ✓ src/features/create-video/jobStatusWatcher.test.ts (9 tests) 60ms

 Test Files  8 passed (8)
      Tests  57 passed (57)
   Start at  22:30:35
   Duration  677ms (transform 59%, import 24%, tests 11%, worker 5%)

-> exit 0

$ npm --prefix apps/web run build

> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 103 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-Cajc0ZMs.css   26.85 kB │ gzip:   5.67 kB
dist/assets/index--wlTazLa.js   337.38 kB │ gzip: 104.39 kB

✓ built in 332ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== T-008-2 verify command: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **No new unit test, deliberately.** The hook has no DOM-free pure helper — its logic is a fetch/status machine that needs a React renderer. Vitest runs in the **Node** environment in this repo (no jsdom), exactly as spec 004's T-004-2 recorded for the other data hooks. `npm run test` still passes (57 tests, 8 files) and the behaviour is covered by T-008-4's HTTP-level check plus `verify-slice` later.
- **`npm run typecheck` is a real gate**, not the no-op the T-008-3/T-008-4 briefs still mention: T-000-6 changed the script to `tsc -b`. It type-checks `api/credits.ts` because `tsconfig.app.json` has `include: ["src"]`.
- **`TOP_UP_CREDITS = 100` is a deliberate client duplicate** of the server's bundle size (the button needs a label before any response exists). The confirmation uses the response's `amount`/`balance`, so a drift can never lie — design 008 § Risks.
- **`features/create-video/useCredits.ts` was left alone** — feature isolation forbids importing it and consolidating the two is a P1 cleanup (design 008 § Reused/Risks).
- **`POST /api/v1/credits/topup` still returns 501 in the API** at the time of writing: T-008-1 (the service + router body) has not landed in this tree yet, so this hook is correct against the frozen contract but cannot complete a real top-up until T-008-1 does. Flagged for T-008-4's manual check.

## Proposed STATUS.md line (WORKS)
| Credits web data: `api/credits.ts` (`useCreditsPage`) reads `GET /credits` and posts `POST /credits/topup` through the shared guest-session runner (auto-guest + one 401 retry); `known`/`loading`/`error` balance with no loading flash after data, `idle`/`pending`/`done`/`error` top-up that keeps the last known balance on failure; typed client regenerated (`+TopUpResponse`, +64/−0) | `apps/web/src/api/credits.ts`, `apps/web/src/api/generated/schema.d.ts` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` → lint/tsc clean, 57 tests, 103 modules built, 0 violations (full output in `docs/tasks/T-008-2/report.md`) | 2026-09-13 17:00 |
