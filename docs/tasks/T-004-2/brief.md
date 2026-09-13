# Brief T-004-2: Data hooks — guest runner, presets, selection, credits, session history, image upload

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/004-create-video/spec.md` (AC-2 image input, AC-3 presets + `?preset=`, AC-4 credits, AC-5 zero-friction auth, AC-9 session memory)
- Design: `docs/specs/004-create-video/design.md` sections **Hooks** (`useGuestSessionRunner`, `usePresets`, `usePresetSelection`, `useCredits`, `useImageUpload`, `useSessionHistory`), **Auto-guest flow**, **`?preset=<slug>` deep link**, **Files**
- Contract: `packages/contracts/openapi.json`, paths `GET /api/v1/presets`, `GET /api/v1/credits`, `POST /api/v1/auth/guest`, `POST /api/v1/uploads`, `POST /api/v1/uploads/{asset_id}/complete`; schemas `PresetListResponse`, `CreditsResponse`, `UploadCreateResponse`, `UploadCreateRequest`, `AssetResponse`
- Backend context: `docs/specs/003-generation-core/design.md` § API contract (401 body, upload 404/409/422 rules) and § Storage (presigned URL TTLs, browser CORS for `PUT` + `Content-Type`)
- Existing patterns: `apps/web/src/features/session/useSession.ts` (`SessionContextValue`, `startGuestSession`), `apps/web/src/api/client.ts` (`apiClient`), `apps/web/src/features/home/HomePage.tsx` (`useOutletContext` usage)
- Types you import (do not edit): `apps/web/src/features/create-video/createVideoTypes.ts` and `createVideoCopy.ts` from T-004-1

## Goal
Implement the six data hooks of the create-video feature and the pure session-history store behind them, exactly matching the design's paths, state shapes and error mappings, so the panel and canvas components (T-004-4/5) can be written against fixed signatures. Every authenticated call goes through `useGuestSessionRunner` (AC-5); never call `useSession()` inside this feature.

## Allowed files (touch nothing else)
- `apps/web/src/features/create-video/useGuestSessionRunner.ts`
- `apps/web/src/features/create-video/usePresets.ts`
- `apps/web/src/features/create-video/usePresetSelection.ts`
- `apps/web/src/features/create-video/useCredits.ts`
- `apps/web/src/features/create-video/sessionHistoryStore.ts`
- `apps/web/src/features/create-video/sessionHistoryStore.test.ts`
- `apps/web/src/features/create-video/useSessionHistory.ts`
- `apps/web/src/features/create-video/putFileWithProgress.ts`
- `apps/web/src/features/create-video/useImageUpload.ts`
- `docs/tasks/T-004-2/report.md`

You **export** `CreditsControls` from `useCredits.ts` and `SessionHistory` from `useSessionHistory.ts`; T-004-3 imports those two exact types.

## Must reuse
- `apiClient` from `apps/web/src/api/client.ts` for every call to our API. The only non-client calls are the presigned storage `PUT` (`putFileWithProgress.ts`, `XMLHttpRequest`) — the typed client cannot report upload progress.
- `SessionContextValue` and `startGuestSession` from `features/session/useSession.ts`, read via the `AppShell` outlet context. `useGuestSessionRunner` keeps `session.status` in a ref and shares one in-flight `ensureGuest()` promise.
- Types/copy from T-004-1 (`ImageUploadControls`, `UploadState`, `PresetSelection`, `PresetsState`, `BalanceView`, `HistoryEntry`, `RunWithGuestSession`, `createVideoCopy`).
- `window.sessionStorage` key **`hf.createVideo.history.v1`**, newest first, cap `MAX_HISTORY_ENTRIES = 6`; pure logic in `sessionHistoryStore.ts`, React state in `useSessionHistory.ts`.
- The URL as the single source of truth for the preset (`searchParams`, `replace: true`) — see design § Deep link.

## Acceptance checks
- [ ] `useGuestSessionRunner`: signed-out → one `ensureGuest()` then the request; a 401 → one `ensureGuest()` + one retry; a failed guest → `{ outcome: "session-failed" }`; concurrent callers share one in-flight guest promise; never re-creates a guest from a stale status.
- [ ] `usePresets`: `GET /api/v1/presets` on mount and on `reloadPresets()`; server order kept; throw/non-200 → `status: "error"` with previous presets kept; empty array → `ready` + `[]`; a reload only shows `loading` when there are no presets yet.
- [ ] `usePresetSelection`: `selectedSlug` from `?preset=`; `isUnknownSlug` true once presets are `ready`, the slug is set and unknown; `selectPreset`/`clearPreset` use the functional `setSearchParams(..., { replace: true })` and preserve other params; `categoryFilter` defaults to `"all"`; no errors.
- [ ] `useCredits`: `guest-offer` when signed out; `loading` only on the first load; 200 → `known`; a refresh keeps the last known balance; 401 → `guest-offer` + `balance: null`; other errors → `error` + `balance: null`; `applyKnownBalance(n)` sets `known` with no request.
- [ ] `useImageUpload`: `checkImageFile` rejection keeps the current state; aborts the in-flight upload and revokes the old object URL; `POST /api/v1/uploads` 201 → `putFileWithProgress` (`upload_headers` exactly, `withCredentials = false`, `onprogress` → 0..1) → `POST /api/v1/uploads/{asset_id}/complete`; 409 retries once after 1000 ms; 422 → `rejection: "invalid-file"` (state back to the pre-selection state, `idle` if none); `session-failed` → `error/session`; other/throw → `error/network`; `retryUpload` re-runs the sequence with the error state's file; `clearImage` and unmount abort + revoke.
- [ ] `sessionHistoryStore.test.ts`: newest first, dedupe by `jobId`, cap 6, invalid JSON → `[]`, entries missing `jobId`/`presetName`/`createdAt` or a valid `status` dropped, a storage whose `getItem`/`setItem` throws does not throw.
- [ ] `useSessionHistory` keeps working in memory only when storage throws (no UI error), and `updateJob` patches `status`/`thumbnailUrl`.
- [ ] No new dependency, no file over 200 lines, no function over 40 lines, complexity ≤ 8 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- `useCreateJob`, `jobStatusWatcher`, `useJobEvents`, `useElapsedSeconds`, `useActiveJob` (T-004-3) and every component (T-004-4/5).
- `apps/web/src/App.tsx`, `apps/web/src/ui/**`, `apps/web/src/api/**`, `apps/web/package.json`, `apps/web/vite.config.ts`, `apps/web/tsconfig*.json`.
- Contract/API changes. If a status code or field you need is missing from `openapi.json`, stop and write it in the report's open issues.

## Report
Write `docs/tasks/T-004-2/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
