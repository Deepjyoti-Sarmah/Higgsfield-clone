# Brief T-005-4: Web UI — the Library page, list, items, states and result panel

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/005-library/spec.md` (AC-4 … AC-11)
- Design: `docs/specs/005-library/design.md` sections **Component tree**, **Props**, **Flow**, **Copy**, **Accessibility**
- Contract: `packages/contracts/openapi.json` → `LibraryItemResponse` (`id`, `status`, `preset_slug`, `preset_name`, `thumbnail_url`, `video_url`, `created_at`, `error_message`)
- Provided by T-005-2: `apps/web/src/api/library.ts` (`LibraryItem`, `LibraryState`, `useLibrary`), `apps/web/src/api/guestSession.ts`
- Provided by T-005-3: `apps/web/src/features/library/libraryCopy.ts`, `formatCreatedAt.ts`
- Existing patterns: `apps/web/src/ui/{Button,ButtonLink,EmptyState}.tsx`, `apps/web/src/features/explore/PresetGallery.tsx` + `PresetGalleryStates.tsx` (the list/states style), `apps/web/src/features/session/useSession.ts` (read the outlet context)

## Goal
The Library page: the signed-out visitor gets a guest session, the list renders newest-first with thumbnails, preset names, times and text statuses, and selecting a succeeded item shows its video inline from data already in memory.

## Allowed files (touch nothing else)
- `apps/web/src/features/library/useLibraryJobParam.ts` (new)
- `apps/web/src/features/library/LibraryPage.tsx` (new)
- `apps/web/src/features/library/LibraryList.tsx` (new)
- `apps/web/src/features/library/LibraryItem.tsx` (new)
- `apps/web/src/features/library/LibraryStates.tsx` (new)
- `apps/web/src/features/library/LibraryResultView.tsx` (new)
- `docs/tasks/T-005-4/report.md`

## What to build
Follow the design's **Props** table exactly.
- **`useLibraryJobParam()`** — reads/writes `?job=<id>` via `useSearchParams` (`{ replace: true }` when selecting) and reports whether the selected id is absent from the list, so the page can show the missing panel (AC-7).
- **`LibraryPage`** — reads the session from `useOutletContext<SessionContextValue>()` (the HomePage precedent), calls `useLibrary(session)` **once**, and renders title/subtitle → states → list → result panel. No component fetches.
- **`LibraryList`** — a `<ul>` with one `<li>` per item.
- **`LibraryItem`** — a `<button>` (one tab stop) containing: a thumbnail (`<img>` with `alt=""` when `thumbnail_url` is set, else a decorative `aria-hidden` tile), the preset name as visible text, `formatCreatedAt(item.created_at)`, and the **text** status from `libraryCopy.item.status`. `aria-current` marks the selected item and the accessible name is `libraryCopy.item.openLabel(preset_name)`.
- **`LibraryStates`** — loading (`aria-busy="true"` + `states.loading.srText` + `skeletonCount` skeleton rows mirroring the item layout), error (`ui/EmptyState` + Retry `ui/Button` calling `onRetry`), empty (`ui/EmptyState` + `ui/ButtonLink` "Create video" → `/create/video`, no Retry).
- **`LibraryResultView`** — for a selected item: `succeeded` → `<video src={video_url} controls muted autoPlay loop playsInline>` (no video element when `video_url` is null), plus a `Download` link to `video_url` and a "Make another" `ButtonLink` to `/create/video?preset=${encodeURIComponent(preset_slug)}` (the spec 004/006 deep-link contract); `failed` → `item.failedFallback`, or `error_message` when present, and **never** a video; a selected id that is not in the list → `item.missing`.
- No second API call anywhere: the result renders from the list item (AC-5).

## Acceptance checks
- [ ] AC-4: name, created time and status are visible text; nothing is hover-only; the status is never conveyed by colour alone
- [ ] AC-5: selecting a succeeded item sets `?job=<id>` and renders the video without calling `/jobs/{id}`
- [ ] AC-6 failed item shows the message and no `<video>`; AC-7 unknown `?job=` shows the missing copy
- [ ] AC-8/AC-9/AC-10: empty, error + Retry, and the `aria-busy` skeleton region all render from `LibraryStates`
- [ ] AC-11: `<ul>`/`<li>`, one real `<button>` per row, visible focus ring, decorative tile `aria-hidden`, video `muted` + `playsInline`
- [ ] no user-visible string literal in any component — everything comes from `libraryCopy`
- [ ] no file over 200 lines, no function over 40 lines, complexity ≤ 8

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- `App.tsx` and the `/library` route (T-005-5) — so the page is reachable only after that task.
- Editing T-005-2/T-005-3 files, `ui/**`, `styles.css`, `package.json`, or any other feature.
- Delete, live SSE progress, filters, pagination (P1 — see the spec).

## Report
Write `docs/tasks/T-005-4/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and the commit.
