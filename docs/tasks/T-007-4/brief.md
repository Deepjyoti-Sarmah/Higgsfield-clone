# Brief T-007-4: Web UI — the share page

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/007-share/spec.md` (AC-3 … AC-6, AC-10)
- Design: `docs/specs/007-share/design.md` §§ **Component tree**, **Copy**, **Flow**
- Provided by T-007-3: `apps/web/src/api/share.ts` (`PublicJob`, `PublicJobState`, `usePublicJob`), `apps/web/src/features/share/shareCopy.ts`
- Existing patterns: `apps/web/src/ui/{Button,ButtonLink,EmptyState}.tsx`, `apps/web/src/features/library/LibraryStates.tsx` (the states/`EmptyState` style), `apps/web/src/features/create-video/ResultView.tsx` (read for the video markup; do not import or edit it)

## Goal
`/v/{id}` renders, for anyone with no session: the video when it is ready, a "still generating" state while it is not, a generic failure state, and a not-found state — with exactly one `h1`.

## Allowed files (touch nothing else)
- `apps/web/src/features/share/ShareStates.tsx` (new)
- `apps/web/src/features/share/ShareResult.tsx` (new)
- `apps/web/src/features/share/SharePage.tsx` (new)
- `docs/tasks/T-007-4/report.md`

## What to build
Follow the design's **Component tree** exactly.
- **`ShareStates`** — props `{ state: "loading" | "error" | "notFound" | "notReady" | "failed"; onRetry: () => void }`.
  - `loading` → an `aria-busy="true"` region with a video-shaped skeleton (16:9) and the `states.loading.srText` screen-reader text; it must not shift the page when the video replaces it.
  - `error` → `ui/EmptyState` + a `ui/Button` "Retry" calling `onRetry`.
  - `notFound` / `failed` → `ui/EmptyState` with a `ui/ButtonLink` to `shareCopy.page.ctaHref` (no Retry — retrying a 404 is pointless).
  - `notReady` → `ui/EmptyState` + a `ui/Button` "Refresh" calling `onRetry`.
- **`ShareResult`** — props `{ job: PublicJob }`: the poster is the `<video>`'s `poster`; `<video src={job.video_url} controls muted playsInline loop preload="metadata">`; the preset name as the page's **only `h1`**; `shareCopy.page.attribution`; a `Download` link to `video_url`; a `ui/ButtonLink` "Make your own" → `/`. Render **no `<video>` element at all** when `video_url` is null.
- **`SharePage`** — no props: `useParams()` for `jobId`, `usePublicJob(jobId)`, and `document.title = shareCopy.page.documentTitle(job.preset_name)` once the job is known (restore "Higgsfield" on unmount, the `CreateVideoPage` `usePageTitle` pattern). It maps the hook's state to the components: `ready` + `status === "succeeded"` → `ShareResult`; `ready` + `queued`/`running` → `notReady`; `ready` + `failed` → `failed`; `notFound` → `notFound`; `error` → `error`; `loading` → `loading`.
- Nothing branches on identity: the owner and a stranger see the same page (AC-3).

## Acceptance checks
- [ ] exactly one `<h1>` (the preset name) and it is present on the succeeded state
- [ ] `muted` + `playsInline` + `controls` on the video; no `<video>` in the not-ready or failed states
- [ ] the error state calls `reload` via Retry; the not-ready state calls `reload` via Refresh; not-found and failed offer only "Make your own"
- [ ] every status is text (never colour-only) and the loading region is `aria-busy="true"`
- [ ] no user-visible string literal in any component — everything comes from `shareCopy`
- [ ] no file over 200 lines, no function over 40 lines, complexity ≤ 8

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```
(`npm run typecheck` is a known no-op in this repo; `tsc -b` inside `build` is the real gate — say so in the report.)

## Out of scope
- `App.tsx` and the `/v/:jobId` route (T-007-5) — the page is unreachable until that task lands.
- Editing T-007-3's files, `ui/**`, `styles.css`, `package.json`, the API, or any other feature.
- Likes, comments, view counts, share buttons, embeds (P1/P2 — see the spec).

## Report
Write `docs/tasks/T-007-4/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
