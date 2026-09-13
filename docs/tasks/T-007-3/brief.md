# Brief T-007-3: Web data + copy for the share page

You are the **implementer** for this one task (a small model is fine). Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/007-share/spec.md` (AC-2, AC-4, AC-6, AC-9)
- Design: `docs/specs/007-share/design.md` §§ **API contract**, **Flow**, **Copy**
- Contract: `packages/contracts/openapi.json`, path `GET /api/v1/public/jobs/{job_id}` → `PublicJobResponse` (`id`, `status`, `preset_slug`, `preset_name`, `poster_url`, `video_url`, `created_at`)
- Patterns: `apps/web/src/api/presets.ts` and `apps/web/src/api/library.ts` (the shared-hook shape: `isMounted`/`requestId` race guards, no loading flash), `apps/web/src/api/client.ts`, `apps/web/src/features/explore/exploreCopy.ts` (the copy-object style)

## Goal
The share page's data hook and every string it renders, so T-007-4 invents neither.

## Allowed files (touch nothing else)
- `apps/web/src/api/share.ts` (new)
- `apps/web/src/features/share/shareCopy.ts` (new)
- `docs/tasks/T-007-3/report.md`

## What to build

### `api/share.ts`
- `export type PublicJob = components["schemas"]["PublicJobResponse"]` — from the generated schema, never hand-written. (If the type is missing from `apps/web/src/api/generated/schema.d.ts`, run `npm --prefix apps/web run gen:api` first; say so in the report.)
- `export type PublicJobState = { status: "loading" | "ready" | "notFound" | "error"; job: PublicJob | null; reload: () => void }`
- `export function usePublicJob(jobId: string | undefined): PublicJobState`
  - `jobId` undefined → `"notFound"` immediately, no request.
  - Fetch `apiClient.GET("/api/v1/public/jobs/{job_id}", { params: { path: { job_id: jobId } } })`.
  - `response.status === 404` → `"notFound"`; `200` with `data` → `"ready"` with `job`; anything else or a throw → `"error"`.
  - **No session, no guest bootstrap** (AC-9): this hook must not call `useGuestSessionRunner`, `startGuestSession`, credits, or any create-video code. The share page works for a stranger with no cookie.
  - `reload()` re-fetches (used by the error "Retry" and the not-ready "Refresh").
  - Mirror `api/presets.ts` for the mounted/requestId race guards and the "do not flash loading once we have data" rule.
  - Import **no** `features/**` module.

### `features/share/shareCopy.ts`
One exported object plus the small template function, byte-exact from design.md § Copy (plain ASCII apostrophes):
- `page.attribution` "Made with Higgsfield" · `page.cta` "Make your own" · `page.ctaHref` "/" · `page.documentTitle(name)` → `` `${name} · Higgsfield` ``
- `states.loading.srText` "Loading this video"
- `states.error` title "We couldn't load this video." · body "Check your connection and try again." · action "Retry"
- `states.notFound` title "This video doesn't exist or was removed." · body "Check the link, or make your own." · action "Make your own"
- `states.notReady` title "Still generating." · body "This video isn't ready yet. Check back in a moment." · action "Refresh"
- `states.failed` title "This video didn't finish." · body "Something went wrong while it was being generated." · action "Make your own"
- `result.download` "Download"

## Acceptance checks
- [ ] `api/share.ts` exports `PublicJob`, `PublicJobState`, `usePublicJob`; it imports no `features/**` and no session/credits code
- [ ] a `404` maps to `"notFound"` (not `"error"`), and a thrown request maps to `"error"`
- [ ] `shareCopy` contains every design § Copy string byte-exact; the file is pure ASCII
- [ ] `npm run test` still passes

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```
(`npm run typecheck` is a known no-op in this repo; `tsc -b` inside `build` is the real gate — say so in the report.)

## Out of scope
- Every `.tsx` component (T-007-4) and `App.tsx` (T-007-5).
- The API, the contract, `features/library/**`, `features/explore/**`, `ui/**`. If a string or field is missing, report it instead of inventing one.

## Report
Write `docs/tasks/T-007-3/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
