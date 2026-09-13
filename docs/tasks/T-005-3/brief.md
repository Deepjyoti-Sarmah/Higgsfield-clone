# Brief T-005-3: Web copy + time helper

You are the **implementer** for this one task (a small model is fine). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/005-library/spec.md` (AC-8, AC-10)
- Design: `docs/specs/005-library/design.md` § **Copy** (normative) and § **`formatCreatedAt`**
- Patterns: `apps/web/src/features/explore/exploreCopy.ts` (the copy-object style), `apps/web/src/features/create-video/elapsedTime.ts` + `elapsedTime.test.ts` (pure helper + Node-only vitest style)

## Goal
Every user-visible Library string in one object, plus a deterministic created-time formatter, so T-005-4 renders strings and never invents them.

## Allowed files (touch nothing else)
- `apps/web/src/features/library/libraryCopy.ts` (new)
- `apps/web/src/features/library/formatCreatedAt.ts` (new)
- `apps/web/src/features/library/formatCreatedAt.test.ts` (new)
- `docs/tasks/T-005-3/report.md`

## What to build

### `libraryCopy.ts`
One exported object (plus the small template functions), matching design.md § Copy **exactly**:
- `page.title` "Library" · `page.subtitle` "Everything you have generated."
- `states.loading` `{ skeletonCount: 4, srText: "Loading your library" }`
- `states.error` title "We couldn't load your library." · body "Check your connection and try again." · action "Retry"
- `states.empty` title "No generations yet." · body "Generate your first video and it will show up here." · action "Create video"
- `item.status`: queued "Queued" · running "Generating" · succeeded "Ready" · failed "Failed"
- `item.failedFallback` "This generation failed and its credits were refunded."
- `item.missing` "This generation is no longer available."
- `item.openLabel(name)` → `` `Open ${name}` ``
- `result.download` "Download" · `result.makeAnother` "Make another" · `result.close` "Close"

Use a plain ASCII apostrophe in "couldn't" (the design's text). No literal may appear in a component later — everything comes from here.

### `formatCreatedAt.ts`
`export function formatCreatedAt(iso: string): string` using
`Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" })`
so `"2026-09-13T19:40:00Z"` renders `"13 Sep 2026, 19:40"`. UTC is deliberate: the unit test must not depend on the machine's timezone. Invalid or empty input returns `""` instead of throwing.

## Acceptance checks
- [ ] `libraryCopy` contains every string in design.md § Copy, byte-exact (including the ASCII apostrophe)
- [ ] `formatCreatedAt` is a pure function with no `Date.now()`; it returns the exact UTC string above for a fixed input, `"13 Sep 2026, 00:05"` for `"2026-09-13T00:05:00Z"`, and `""` for `""` / `"not a date"`
- [ ] the test file uses top-level `test(...)` calls (the eslint `max-lines-per-function: 40` limit applies to callbacks too)
- [ ] `npm run test` passes with the new file

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Every `.tsx` component (T-005-4) and `App.tsx` (T-005-5).
- Editing `exploreCopy.ts` or any other feature's files. If a string is missing, report it instead of inventing one here.

## Report
Write `docs/tasks/T-005-3/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
