# Brief T-008-3: Web UI — the Credits page, balance card, top-up card and copy

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/008-credits/spec.md` (AC-1, AC-3 … AC-9)
- Design: `docs/specs/008-credits/design.md` §§ **Component tree** (Props), **Copy**, **Accessibility**, **Files**
- Provided by T-008-2: `apps/web/src/api/credits.ts` (`useCreditsPage`, `CreditsPageState`, `TOP_UP_CREDITS`, `TopUpStatus`, `BalanceStatus`)
- Existing patterns: `apps/web/src/features/library/{LibraryStates,LibraryPage}.tsx` (states + one hook per page), `apps/web/src/features/explore/PresetGalleryStates.tsx` (skeleton), `apps/web/src/ui/{Button,ButtonLink,EmptyState}.tsx`, `apps/web/src/features/session/useSession.ts` (`SessionContextValue`, read via `useOutletContext`)

## Goal
`/credits` (once T-008-4 routes it) shows the balance with loading/error states and a "Add 100 credits" button whose pending/done/error states are all text.

## Allowed files (touch nothing else)
- `apps/web/src/features/credits/creditsCopy.ts` (new)
- `apps/web/src/features/credits/CreditsBalanceCard.tsx` (new)
- `apps/web/src/features/credits/CreditsTopUpCard.tsx` (new)
- `apps/web/src/features/credits/CreditsPage.tsx` (new)
- `docs/tasks/T-008-3/report.md`

## What to build
Follow the design's **Props** table exactly. One component per file; **zero user-visible string literals** in the `.tsx` files (everything comes from `creditsCopy`). No component fetches: `CreditsPage` calls `useCreditsPage(session)` **once** and passes state down.

- **`creditsCopy.ts`** — one exported object plus the template helpers, byte-exact from design § Copy (pure ASCII, plain apostrophes):
  - `page.title` "Credits" · `page.subtitle` "Your balance and how to top it up."
  - `balance.label` "Balance" · `balance.value(balance)` → `` `${balance} credits` ``
  - `states.loading.srText` "Loading your credits"
  - `states.error` title "We couldn't load your credits." · body "Check your connection and try again." · action "Retry"
  - `topup.title` "Add credits" · `topup.description` "This is a demo top-up. No payment is taken."
  - `topup.action(amount)` → `` `Add ${amount} credits` `` · `topup.pending` "Adding credits..."
  - `topup.done(amount, balance)` → `` `Added ${amount} credits. New balance: ${balance}.` ``
  - `topup.error` "We couldn't add credits." · `topup.retry` "Try again"
- **`CreditsBalanceCard.tsx`** — props `{ status: "loading" | "error" | "known"; balance: number | null; onRetry: () => void }`:
  - `loading` → an `aria-busy="true"` region containing `states.loading.srText` behind `sr-only` plus a skeleton line that matches the known layout (so the swap does not shift the page);
  - `error` → `ui/EmptyState` (title/body) with a `ui/Button` "Retry" calling `onRetry`;
  - `known` → the `balance.label` and `balance.value(balance)` as visible text (never colour-only).
- **`CreditsTopUpCard.tsx`** — props `{ status: "idle" | "pending" | "done" | "error"; amount: number | null; balance: number | null; onTopUp: () => void }`:
  - an `h2` `topup.title`, the `topup.description` line, and a `ui/Button` labelled `topup.action(TOP_UP_CREDITS)`; when `status === "pending"` pass `isLoading` so the button disables and cannot double-submit;
  - `pending` → `topup.pending` in a `role="status"` (polite) region;
  - `done` → `topup.done(amount ?? TOP_UP_CREDITS, balance ?? 0)` in the same `role="status"` region;
  - `error` → `topup.error` in a `role="alert"` region plus a "Try again" `ui/Button` calling `onTopUp` (the error state must be recoverable without a reload).
- **`CreditsPage.tsx`** — `useOutletContext<SessionContextValue>()`, `useCreditsPage(session)` once, then: an `h1` `page.title`, a `page.subtitle` paragraph, `CreditsBalanceCard`, `CreditsTopUpCard`. Pass `balanceStatus`/`balance`/`reload` and `topUpStatus`/`grantedAmount`/`balance`/`topUp` straight through. Exactly one `h1` on the page.

## Acceptance checks
- [ ] AC-3/AC-6: `known` shows the number as text; `loading` is an `aria-busy="true"` region with `srText` + skeleton, never a flash of `0`
- [ ] AC-7: error shows the title/body via `ui/EmptyState` and a Retry `ui/Button` wired to `reload`
- [ ] AC-5/AC-9: pending disables the button and announces `topup.pending`; done announces `topup.done(amount, balance)`; error uses `role="alert"` with a working "Try again"
- [ ] AC-9: the top-up is a real `<button>` (keyboard operable, visible focus ring from `ui/Button`); exactly one `h1`; no state conveyed by colour alone
- [ ] no user-visible string literal in any component; every file ≤ 200 lines, every function ≤ 40 lines, complexity ≤ 8
- [ ] `ui/` primitives are reused, not re-implemented; no other feature is imported

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- `App.tsx` and the `/credits` route (T-008-4) — the page is reachable only after that task.
- Editing T-008-2's `api/credits.ts`, `ui/**`, `styles.css`, or any other feature.
- Credit history, a top-up cap, choosing an amount, payments (P1/CUT — see the spec).

## Report
Write `docs/tasks/T-008-3/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
