# Brief T-010-11: Credits button and popover (balance, demo top-up, ledger)

**Role:** implementer · **Suggested model:** small/medium · **Depends on:** T-010-4 and T-010-7 merged · **Wave:** W3

## Start here (any harness)
1. `scripts/task claim T-010-11 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Web, **`DESIGN.md`** §4 ("Popover (credits)"), and spec 010 AC-7 and AC-20.
3. Read `features/credits/*`, `api/credits.ts`, `ui/Popover.tsx` (T-010-5), `ui/CreditsPopoverContext.tsx` (T-010-7) and `App.tsx`.
4. Questions: `scripts/task say T-010-11 QUESTION "…"`.

## Goal
The credit balance is always in the top bar. Clicking it (or any 402, or `/credits`) opens a popover with the balance, an "Add demo credits" button, and the last 10 ledger entries. The ledger shows the real hold, settle and refund entries behind every job.

## Allowed files (touch nothing else)
- `apps/web/src/features/credits/*` (replace `CreditsPage` and its cards with `CreditsButton` + `CreditsPopoverPanel` + `LedgerList`)
- `apps/web/src/api/ledger.ts` (new): `useLedger(session, isOpen)` fetches `GET /api/v1/credits/ledger?limit=10` when the popover opens and after a top-up
- `apps/web/src/api/credits.ts` (only if the balance hook needs a `reload` it doesn't already expose)
- `apps/web/src/App.tsx`: **one change only**, passing `creditsSlot={<CreditsButton … />}` to `AppShell`
- tests for the above
- `docs/tasks/T-010-11/report.md`

## The change
1. **`CreditsButton`:**
   - Shows the balance in mono (`120 credits`) in the top bar, as a button with `aria-haspopup="dialog"`.
   - Opens `ui/Popover` controlled by `useCreditsPopover()`. So a 402 anywhere (the composers call `openCredits()`) and `/credits` (T-010-7's redirect) both open it.
   - Hidden while the session is loading or signed out.
2. **`CreditsPopoverPanel`:**
   - The balance at 1.5rem mono.
   - **"Add demo credits"** calls the existing top-up (`api/credits.ts`), with the helper line "Demo credits. No payment is taken." On the daily top-up limit, show the API's message inline.
   - Then **`LedgerList`**, the last 10 entries. Each row has:
     - the kind label: Hold / Settled / Refund / Top-up / Welcome grant;
     - a mono amount, `+` in `success`, `−` in `text`, `0` in `muted`;
     - the relative time;
     - a link to `/studio?item=<job_id>` when the entry has a `job_id`.
   - Loading uses a skeleton; an error gets Retry.
3. **Refresh:** the balance and ledger refresh after a top-up, and whenever the popover opens.
4. **Tests:**
   - The button shows the balance.
   - `openCredits()` from the context opens the panel.
   - A top-up click calls the API and then reloads the ledger.
   - Ledger rows format a HOLD as `−20` and a RELEASE as `+20`, with job links.

## Acceptance checks
- [ ] AC-7 holds; the 402 path opens the popover; `/credits` opens it
- [ ] The popover is keyboard-accessible: focus moves in, Escape closes, focus returns to the button
- [ ] The old credits page is removed, with no dead imports
- [ ] lint, test, typecheck, build and check-standards pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```

## Out of scope
- The backend (the ledger endpoint is T-010-4), real payments.

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-11`
2. `scripts/task submit T-010-11 --as <you> [--transcript <file>]`
