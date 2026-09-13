# Brief T-005-2: Web data — move the guest-session runner, add `useLibrary`

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/005-library/spec.md` (AC-2, AC-3, AC-9)
- Design: `docs/specs/005-library/design.md` sections **API contract**, **Flow**, **Files**
- Contract: `packages/contracts/openapi.json`, path `GET /api/v1/jobs` → `LibraryItemResponse[]` under `items`
- Patterns: `apps/web/src/api/presets.ts` (the shared-hook precedent from T-006-1 — read it), `apps/web/src/features/create-video/useGuestSessionRunner.ts` (the hook you move), `apps/web/src/api/client.ts`

## Goal
Two things: (1) the guest-session runner becomes shared, because the Library is its second consumer and STANDARDS forbids importing another feature's internals; (2) `api/library.ts` owns the Library's data — types plus `useLibrary`, which lists the owner's generations and gets a guest session when the visitor is signed out.

## Allowed files (touch nothing else)
- `apps/web/src/api/guestSession.ts` (new — the moved runner)
- `apps/web/src/features/create-video/useGuestSessionRunner.ts` (delete)
- `apps/web/src/features/create-video/createVideoTypes.ts` (edit: **re-export only** for the two moved types)
- `apps/web/src/features/create-video/CreateVideoPage.tsx` (edit: the runner import path only)
- `apps/web/src/api/library.ts` (new)
- `apps/web/src/api/generated/schema.d.ts` (regenerate with `npm --prefix apps/web run gen:api` — the new `LibraryItemResponse` type must exist)
- `docs/tasks/T-005-2/report.md`

## What to build

### 1. `api/guestSession.ts` — the runner, moved
Move `useGuestSessionRunner` **behaviourally unchanged** (same shared in-flight `ensureGuest` promise, same one 401 retry, same status/start refs). Two adjustments are required to keep the layering right:
- The runner only needs the session's `status` and `startGuestSession`. Declare a minimal local type instead of importing the feature's `SessionContextValue`, e.g.
  `export type GuestSessionSource = { status: "loading" | "signed-out" | "signed-in"; startGuestSession: () => Promise<boolean> }`.
  `SessionContextValue` is structurally assignable to it, so the existing call site keeps compiling.
- Move `GuestSessionOutcome<T>` and `RunWithGuestSession` from `createVideoTypes.ts` into this module, and make `createVideoTypes.ts` **re-export** them (`export type { GuestSessionOutcome, RunWithGuestSession } from "../../api/guestSession"`) so `useImageUpload.ts`, `useCreateJob.ts` and `useActiveJob.ts` compile unchanged. This is exactly what T-006-1 did for `Preset`/`PresetsState`.
- Delete `features/create-video/useGuestSessionRunner.ts` (no forwarding wrapper) and point `CreateVideoPage.tsx` at `../../api/guestSession`.

### 2. `api/library.ts` — the Library's data
- `export type LibraryItem = components["schemas"]["LibraryItemResponse"]`
- `export type LibraryState = { status: "loading" | "ready" | "error"; items: LibraryItem[]; reloadLibrary: () => void }`
- `export function useLibrary(session: GuestSessionSource): LibraryState` — takes the session as a parameter so `api/` never imports a feature. Mirror `api/presets.ts`: `isMounted`/`requestId` race guards, no loading flash once items exist, `reloadLibrary` for Retry.
- Fetch with `useGuestSessionRunner(session)` so the 401 → guest → one-retry behaviour is the spec-004 one, not a new one:
  `apiClient.GET("/api/v1/jobs", { params: { query: { limit: 50 } } })`. `outcome !== "done"`, a non-200 or a throw → `null` → `status: "error"`; otherwise `data.items` → `"ready"`.
- No hand-written API shape: `LibraryItem` must come from the generated schema.

## Acceptance checks
- [ ] `api/guestSession.ts` exports `GuestSessionSource`, `GuestSessionOutcome`, `RunWithGuestSession`, `useGuestSessionRunner`; behaviour is identical to the deleted hook (same shared in-flight promise, same single 401 retry)
- [ ] `createVideoTypes.ts` no longer **defines** those two types but re-exports them; every other type in that file is unchanged
- [ ] `features/create-video/useGuestSessionRunner.ts` is deleted; `CreateVideoPage.tsx` imports the runner from `../../api/guestSession`; no forwarding wrapper is left behind
- [ ] `api/library.ts` exports `LibraryItem`, `LibraryState`, `useLibrary(session)`; it imports **no** `features/**` module
- [ ] `npm run test` still passes (the runner had no direct tests; this proves the create-video suite still compiles and runs)

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Any `.tsx` component (T-005-4), `libraryCopy.ts`/`formatCreatedAt.ts` (T-005-3), `App.tsx` (T-005-5).
- Changing the runner's behaviour, the guest endpoint, or any other create-video file beyond the two listed.
- Contract/API changes: the route and schemas are frozen by T-005-0. If something is missing, stop and report it.

## Report
Write `docs/tasks/T-005-2/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
