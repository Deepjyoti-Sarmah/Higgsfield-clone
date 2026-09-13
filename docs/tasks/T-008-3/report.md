# Report T-008-3

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/src/features/credits/creditsCopy.ts` (new) — every user-visible Credits string, byte-exact from design 008 § Copy.
- `apps/web/src/features/credits/CreditsBalanceCard.tsx` (new) — `loading | error | known`.
- `apps/web/src/features/credits/CreditsTopUpCard.tsx` (new) — `idle | pending | done | error`.
- `apps/web/src/features/credits/CreditsPage.tsx` (new) — one `useCreditsPage(session)` call, then straight pass-through.
- `docs/tasks/T-008-3/report.md` (this file).
- **Not committed**; no other file touched (no `App.tsx`, no `api/**`, no `ui/**`, no `styles.css`).

## What was built
- **`creditsCopy.ts`** — one exported object plus the three template helpers (`balanceValue`, `topUpAction`, `topUpDone`); pure ASCII with plain apostrophes, matching the design's Copy table exactly.
- **`CreditsBalanceCard`** (props `{ status, balance, onRetry }`):
  - `loading` → an `aria-busy="true"` card whose only visible text is `balance.label` plus a skeleton block sized to the known value line, with `states.loading.srText` behind `sr-only` — so the swap to `known` does not shift the page and there is never a flash of `0`.
  - `error` → `ui/EmptyState` (title/body) with a `ui/Button` "Retry" wired to `onRetry`.
  - `known` → the label and the number as visible text.
  - A `known` status with a `null` balance falls back to the skeleton rather than printing a fake `0`.
- **`CreditsTopUpCard`** (props `{ status, amount, balance, onTopUp }`): `h2` title, description, a real `ui/Button` labelled `topup.action(TOP_UP_CREDITS)` that passes `isLoading` while pending (so it disables and cannot double-submit); `pending` and `done` render in one `role="status"` polite region; `error` renders in `role="alert"` with a "Try again" `ui/Button` wired to `onTopUp`, so the failure is recoverable without a reload. `done` uses the API's `amount`/`balance` (with the design's `?? TOP_UP_CREDITS` / `?? 0` fallbacks).
- **`CreditsPage`** — `useOutletContext<SessionContextValue>()` + one `useCreditsPage(session)`; one `h1` (`page.title`), the subtitle, then the two cards. No component fetches.

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
✓ 103 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-00oqWkWO.css   27.05 kB │ gzip:   5.70 kB
dist/assets/index-6P6L_S6s.js   337.38 kB │ gzip: 104.39 kB

✓ built in 320ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== T-008-3 verify command: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Self-check against the acceptance criteria
- **Exactly one `h1`** on the page: `grep -c '<h1'` → `CreditsPage.tsx` 1, the two cards 0.
- **No user-visible string literal in any `.tsx`**: every text node is `{creditsCopy...}`. (A naive `grep -E '>[^<>{]*[A-Za-z]'` flags only `=> void` inside the two props *type* declarations, which is code, not rendered copy.)
- **Accessibility:** `aria-busy="true"` ×1 (balance loading), `role="status"` ×2 (top-up pending/done), `role="alert"` ×1 (top-up error); the top-up control is `ui/Button`, a real `<button>` with the shared focus ring; every state is text, never colour-only.
- **Line counts:** `creditsCopy.ts` 41, `CreditsBalanceCard.tsx` 46, `CreditsTopUpCard.tsx` 40, `CreditsPage.tsx` 31 — all far under 200, and every function is under 40 lines (eslint enforces both).
- **Type-checked even though the route is not wired yet:** `tsc -p tsconfig.app.json --noEmit --listFiles` lists `src/features/credits/{creditsCopy.ts,CreditsBalanceCard.tsx,CreditsTopUpCard.tsx,CreditsPage.tsx}`.

## Open issues / guesses / things skipped
- **The page is unreachable until T-008-4** routes `/credits`; Vite therefore tree-shakes it from the bundle (103 modules, unchanged), which is why `tsc -b` — not the bundle — is the proof that it compiles.
- **One `features/**` import, deliberate and type-only:** `import type { SessionContextValue } from "../session/useSession"`. `features/session` is the shared session context that every page reads (`LibraryPage`, `CreateVideoPage`, `HomePage` all do this by the same design 008 § Reused wording). No *data* feature is imported — all credits data comes from `api/credits.ts`, passed down as props.
- **`text-red-400` on the top-up error** is a colour *plus* text (`topup.error`), so nothing is conveyed by colour alone; it reuses the same error style as `ui/GuestButton`/create-video.
- **No new unit test**, for the same reason as T-008-2: the components are DOM-only and vitest runs in the Node environment here (no jsdom). Coverage comes from T-008-4's HTTP check and a later `verify-slice`.
- **`npm run typecheck` is `tsc -b` (a real gate)** — the T-008-3 brief's "(a known no-op)" note is stale since T-000-6.

## Proposed STATUS.md line (WORKS)
| Credits page UI: `/credits` content — one `h1` + subtitle, balance card (`aria-busy` skeleton → number as text, error + Retry), top-up card (real button disabling while pending, `role="status"` pending/done announcements, `role="alert"` error with "Try again"); every string from `creditsCopy`; no component fetches | `apps/web/src/features/credits/{creditsCopy.ts,CreditsBalanceCard,CreditsTopUpCard,CreditsPage}.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → lint/tsc clean, build 103 modules, 0 violations (full output in `docs/tasks/T-008-3/report.md`) | 2026-09-13 17:01 |
