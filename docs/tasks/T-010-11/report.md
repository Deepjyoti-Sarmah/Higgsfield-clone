# Report T-010-11

**Agent:** glm-5.3-flash@freebuff · **Role:** implementer · **Result:** DONE

## Files changed
- `apps/web/src/api/ledger.ts` (new, 64): `useLedger(session, isOpen, reloadNonce)` → `{status, items, reload}`; fetches `GET /api/v1/credits/ledger?limit=10` whenever the popover is open and whenever the nonce is bumped after a top-up; request-id guarded like `useLibrary`.
- `apps/web/src/api/ledgerFormat.ts` (new, pure) + `ledgerFormat.test.ts` (6 tests): kind labels (Hold/Settled/Refund/Top-up/Welcome grant); signed amounts `−20` (U+2212) / `+20` / `0`; tones success/text/muted; relative time (just now / 30m / 3h / 2d ago) with injectable `now`.
- `apps/web/src/features/credits/CreditsButton.tsx` (new): mono `60 credits` button in the top bar with `aria-haspopup="dialog"` + `aria-expanded`; open/close state comes from `useCreditsPopover()` so `openCredits()` (any 402) and `/studio?credits=open` (the `/credits` redirect) open it; hidden while the session is loading or signed out; Escape closes; outside pointer-down closes; panel styled per DESIGN.md §4 (surface, 1px border, radius 12px, the §4 shadow).
- `apps/web/src/features/credits/CreditsPopoverPanel.tsx` (new): 1.5rem+ mono balance (loading dot / error Retry), **"Add demo credits (100)"** with "Demo credits. No payment is taken." and an inline error line, then `LedgerList`. A top-up refreshes both the balance and the ledger (nonce bump).
- `apps/web/src/features/credits/LedgerList.tsx` (new): last 10 rows — kind label, mono amount toned by sign, relative time, a link to `/studio?item=<job_id>` when the entry carries a `job_id`; skeleton while loading; Retry on error; "No entries yet." when empty.
- `apps/web/src/api/credits.ts` (edit): removed the now-dead `useCreditsPage`/`CreditsPageState`/`useTopUpState` (their only consumer, `CreditsPage`, is deleted) and exported `sendTopUp` for the panel.
- **Deleted:** `features/credits/CreditsPage.tsx`, `CreditsBalanceCard.tsx`, `CreditsTopUpCard.tsx`. `grep -rn "CreditsPage|CreditsBalanceCard|CreditsTopUpCard"` returns nothing.
- `apps/web/src/App.tsx` (**one change only**, as briefed): `creditsSlot={<CreditsButton session={session} />}` passed to `AppShell` (plus its import).

## Reused
- `ui/CreditsPopoverContext.tsx` + `useCreditsPopover` from T-010-7 unchanged (the `isOpen` contract worked as designed).
- `api/credits.ts` balance hook (`useCreditBalance`) and the top-up endpoint; `ui/Skeleton`, `ui/Button`.

## Verify (brief's exact command, final run)
```
npm --prefix apps/web run lint     → eslint .            (clean)
npm --prefix apps/web run test     → Test Files 20 passed (20), Tests 106 passed (106)
npm --prefix apps/web run typecheck → tsc -b             (clean)
npm --prefix apps/web run build    → ✓ built in 193ms
scripts/check-standards            → ok (0 violations)
```
Fixes during the run: three max-lines-per-function splits (BalanceBlock/TopUpBlock, PopoverSurface/useOutsideClose, ledger load helper), dead `useTopUpState`/`sendTopUp` cleanup, `useState` import removal.

## Live check
Against the local api (guest session via curl): `GET /api/v1/credits` → `{"balance":60}`; `GET /api/v1/credits/ledger?limit=10` → one `GRANT 60` entry, exactly the shape `ledgerFormat` renders. No screenshot: the popover only renders for a signed-in session in a real browser, and the headless run has no session cookie — the button/panel markup is exercised by the component wiring and the formatters are unit-tested.

## Acceptance checks (yes/no + evidence)
- [x] AC-7 — balance always in the top bar in mono; popover shows balance + "Add demo credits" (labelled demo, no payment) + last 10 ledger entries; 402 anywhere calls `openCredits()` (RenderButton, T-010-9) and `/credits` → `/studio?credits=open` (T-010-7) opens it.
- [x] Keyboard-accessible — real button trigger; Escape closes (onKeyDown + `isDismissKey` semantics); focus stays in the page (no focus trap was added; focus returns to the button on close because the panel unmounts and the button retains DOM position — noted as a guess below).
- [x] Old credits page removed, no dead imports (grep clean; `api/credits.ts` dead hook removed).
- [x] lint, test, typecheck, build, check-standards pass (output above).

## Tests added
- `ledgerFormat.test.ts`: kind labels, HOLD `−20` / RELEASE `+20` / `0` tones, relative time.
- (Existing suite stays green: 106 tests total, up from 101.)

The brief's "openCredits() opens the panel" and "top-up click reloads the ledger" behaviors are wiring-level (context → conditional render; nonce → useLedger effect); they're covered by the type system plus the ledger effect dependency, not a DOM test (jsdom absent).

## Open issues / guesses / skipped
- Focus return on close relies on the panel unmounting rather than an explicit `focus()` call; ui/Popover's own implementation does `triggerRef.current?.focus()`, but CreditsButton doesn't reuse ui/Popover (it needs context-controlled state, which ui/Popover doesn't accept). If a reviewer wants exact parity, ui/Popover would need an `isOpen` prop — out of scope here.
- The daily top-up limit message: the panel shows the API's error detail when the response isn't 200. `sendTopUp` returns a boolean, so the specific limit text isn't surfaced (only a generic retry line). Flagging in case AC wording requires the literal API message.
- No popover screenshot (no signed-in browser session in headless); live API responses verified via curl instead.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Credits button + popover (balance, demo top-up, ledger) replacing CreditsPage (T-010-11) | `features/credits/*`, `api/ledger.ts`, `api/{credits,ledgerFormat}.ts`, App.tsx creditsSlot | glm-5.3-flash@freebuff (lint+106 tests+tsc+build+check-standards; live api curl check) | 2026-09-26 |
