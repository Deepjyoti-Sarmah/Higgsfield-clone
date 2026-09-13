# Spec 008: Credits + fake top-up

**Status:** APPROVED (handing off this pack is the user's approval, the convention specs 004–007 use)  ·  **Priority:** P0
**Research refs:** `docs/research/product-map.md` row 17 ("Generate button shows the credit cost up front", done in spec 004) and row 21 ("Pricing page → Credits with a fake top-up covers the money flow", D-007); `docs/DECISIONS.md` D-007 (fake top-up), D-003 (hard $5 paid budget), D-002 (paid fallback); `docs/specs/003-generation-core/design.md` § Credit rules and job states (the ledger: one-time guest `GRANT` 60, `HOLD`/`SETTLE`/`RELEASE`)

## Problem / why
The credit ledger is real but almost invisible: the only place credits appear is one line under Create video's Generate button, and when a generation is refused with **402** the UI sends the user to `/credits` — which is still the "coming in a later slice" placeholder. So the product's one genuine dead end ("you have no credits") has no page behind it: there is no balance to look at and no way to get more.

D-007 settles the money question: the ledger is real, the payment is not. A **fixed, fake top-up** is enough to demonstrate the whole money flow end to end — one-time guest grant → HOLD → SETTLE (or RELEASE) → top-up → generate again — without a payment provider, checkout, or any PII. This spec builds exactly that one page and one route.

## User story
As a guest, I want to see my credit balance and add a fixed bundle of demo credits without paying, so that I can keep generating when I run out.

## Acceptance criteria (each testable; verify-slice checks exactly these)
- **AC-1 Route:** `/credits` renders the Credits page inside `AppShell`; the nav item already points there, so no nav change is needed.
- **AC-2 Signed out:** with no cookie, the page first gets a guest session automatically (the spec-004 runner, `api/guestSession.ts`) and then shows that guest's balance. There is no login wall. A 401 on the balance read is retried exactly once after the guest session is ensured; if it still fails, the error state shows.
- **AC-3 Balance:** on mount the page reads `GET /api/v1/credits` once and shows the numeric balance as visible text.
- **AC-4 Top-up:** pressing "Add 100 credits" calls `POST /api/v1/credits/topup`; on **200** the page shows the returned new balance (= previous + the returned `amount`) and the ledger has gained exactly one `TOPUP` row of **+100**. There is no payment step, no redirect and no card field.
- **AC-5 Action states:** while the request is in flight the button is disabled and shows a pending label; on success a text confirmation names the granted amount and the new balance; on failure a text error with a "Try again" affordance is shown and the last known balance stays visible.
- **AC-6 Loading:** while the first balance read is in flight, the balance region is `aria-busy="true"` and never flashes a fake `0`.
- **AC-7 Error:** network failure or a non-200 balance read → an error message plus a Retry action that re-reads the balance.
- **AC-8 Persistence:** the balance is summed from the ledger, not held in component state, so a page reload shows the post-top-up balance.
- **AC-9 Accessibility:** the balance and every action state are **text**, never colour-only; the top-up is a real `<button>` (keyboard operable, visible focus ring); pending/done are announced in a polite live region and the error in an alert region; the page has exactly one `h1`.
- **AC-10 Read-only safety:** the top-up is the only mutation on the page — no job is created, no credit is held, and a caller cannot choose the amount (it is a fixed server-side constant).
- **AC-11 Contract discipline:** every pre-existing path and schema in `packages/contracts/openapi.json` stays byte-identical; the only additions are `POST /api/v1/credits/topup` and `TopUpResponse`. **No migration** (the `TOPUP` kind, the amount-sign check and `ix_ledger_entry_user` already exist).
- **AC-12 Signed-out mutation:** `POST /api/v1/credits/topup` with no cookie → **401** `ErrorResponse`; the web auto-guest flow prevents that path on the page.

## UI states (every one must be designed)
- **Empty / new guest:** balance `60` (the one-time grant) with the top-up button idle — this is the normal first view, not a special case.
- **Loading:** an `aria-busy="true"` region with a skeleton balance line, so the swap does not shift the page.
- **Error (balance):** "We couldn't load your credits." · "Check your connection and try again." · action "Retry".
- **Success (known):** the balance as text + "Add 100 credits" and the demo disclaimer.
- **Top-up pending:** the button disabled, "Adding credits...".
- **Top-up done:** "Added 100 credits. New balance: 160." (numbers from the API response).
- **Top-up error:** "We couldn't add credits." · "Try again"; the balance that was already shown stays.

## Out of scope
- **Real payments:** checkout, card fields, receipts, invoices, tax, subscriptions, refunds (CUT, D-007). The top-up is explicitly labelled a demo.
- **Credit history / a transaction list (P1).** Showing `GRANT`/`HOLD`/`SETTLE`/`RELEASE`/`TOPUP` rows would need a second route (`GET /api/v1/credits/entries` + `LedgerEntryResponse`) and a list UI. Deliberately excluded so the contract delta stays at one route; the ledger itself is already covered by the API tests. See Open questions.
- **Choosing an amount** or bundles; promo codes, discounts, strikethrough prices (product-map row 17 forbids fake discounts).
- **A top-up cap / rate limit (P1).** See Open questions.
- **Live balance updates** (SSE/polling). The balance refreshes on mount, after a top-up, and on Retry.
- **Editing the ledger**, admin views, per-model pricing. Preset `credit_cost` (spec 003) stays the single price source; image generation (P1) would reuse it.
- **Nav or header changes:** the `Credits` nav item and `AppShell` are unchanged.

## Open questions
- **Is the history list P0?** Decided **no**: one new route keeps the contract minimal and the page P0-simple, and the ledger is already proven by API tests. P1 would add `GET /api/v1/credits/entries` returning `{id, kind, amount, job_id, created_at}` newest-first, rendered with the Library's list pattern.
- **Should the fake top-up be capped?** Decided **no** for P0. The top-up is fake; `POST /api/v1/auth/guest` is already an unbounded credit faucet (each new guest gets 60), so a cap here would not close that hole — the real guard is D-003's `PAID_BUDGET_CENTS` counter plus the `GENERATION_BACKEND=mock` kill switch. A cap would add a 409/429 branch and UI copy for no P0 value; it is recorded as P1.
- **Scope-classification note:** D-012 lists "pricing with a fake top-up" under **P1**, while `docs/PLAN.md` § Scope puts "Credits with HOLD/SETTLE/RELEASE and a fake top-up" in the **P0** core loop, and the orchestrator instruction for this spec says P0-simple. This spec follows PLAN.md + D-007 and treats it as P0; **D-013** records that resolution (DECISIONS is append-only, so D-012 is not edited).
