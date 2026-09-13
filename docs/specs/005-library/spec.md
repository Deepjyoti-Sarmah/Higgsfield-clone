# Spec 005: Library (my generations)

**Status:** APPROVED (handing off this pack is the user's approval, the convention spec 004/006 use)  ·  **Priority:** P0
**Research refs:** `docs/research/product-map.md` rows 16 ("Video create: History panel" → becomes the "My generations" library) and 18 ("Assets" → merged with History: ONE library of every output); `docs/research/flows/video-create.md` (History panel behaviour); `docs/specs/003-generation-core/design.md` (`GET /api/v1/jobs/{id}`, ownership, presigned URLs); `docs/specs/004-create-video/design.md` (auto-guest runner, `?preset=` deep link)

## Problem / why
A generation is only visible inside Create video's canvas and its in-session strip (the last 6, in `sessionStorage`). There is no server-backed list, and the API has no list sibling of `POST /api/v1/jobs`: `GET /api/v1/jobs` does not exist. So a returning visitor cannot see what they made, and the same output cannot be reopened without regenerating it (and paying credits again). The product map merges the original's History panel and Assets page into ONE library of every output — this spec builds exactly that one list, owner-scoped and server-backed.

## User story
As a guest, I want to see every generation I have made, with its status and thumbnail, so that I can reopen a result instead of generating it again.

## Acceptance criteria (each one testable; verify-slice checks exactly these)
- **AC-1 Route:** `/library` renders the Library page inside `AppShell`; the nav item already points there, so no nav change is needed.
- **AC-2 Signed out:** with no cookie, the page first gets a guest session automatically (the spec-004 runner pattern) and then lists that guest's generations. There is no login wall. A 401 on the list is retried exactly once after the guest session is ensured; if it still fails the error state shows.
- **AC-3 List:** on mount the page calls `GET /api/v1/jobs?limit=50` once, and renders every returned item newest first. "Retry" (AC-9) is the only other trigger.
- **AC-4 Item:** each generation shows a thumbnail (poster when ready, else the input image, else a decorative tile), the preset name as visible text, the created time as readable text, and a **text** status for queued / running / succeeded / failed. Nothing is hover-only and no state is conveyed by colour alone.
- **AC-5 Open a result:** selecting a **succeeded** item shows its video in an inline result panel **without a second API call** (the list item already carries `video_url`). The selection is written to the URL as `/library?job=<id>`, so Back/Forward and a refresh keep it.
- **AC-6 Failed item:** a failed generation shows the failure state with the job's `error_message` when present, or a generic message when it is null, and never shows a video.
- **AC-7 Missing item:** a `?job=<id>` that is not in the returned list shows "This generation is no longer available." instead of an empty panel, and the page still renders the list.
- **AC-8 Empty:** 200 with zero items → "No generations yet." plus a link to Create video.
- **AC-9 Error:** network failure or non-200 → "We couldn't load your library." with a Retry action that re-fetches.
- **AC-10 Loading:** skeleton rows inside an `aria-busy="true"` region while the first request is in flight.
- **AC-11 Accessibility:** the list is a `<ul>` with one `<li>` per generation; each item is a real `<button>` (keyboard operable, visible focus ring) that reports its state via `aria-current`; the result video is `muted` + `playsInline`; the decorative tile is `aria-hidden="true"`.
- **AC-12 Contract discipline:** every pre-existing path and schema in `packages/contracts/openapi.json` stays byte-identical; the only additions are `GET /api/v1/jobs`, `LibraryItemResponse` and `LibraryListResponse`. No migration is added (the list index already exists).

## UI states (every one must be designed)
- **Empty:** title "No generations yet." · body "Generate your first video and it will show up here." · action "Create video" → `/create/video`.
- **Loading:** `aria-busy="true"` region with skeleton rows that mirror the item layout, so the swap does not shift the page.
- **Error:** title "We couldn't load your library." · body "Check your connection and try again." · action "Retry".
- **Success:** the list; plus the result panel when a succeeded item is selected, and the failed/missing panels for AC-6/AC-7.

## Out of scope
- **Delete a generation (P1).** Removing a job touches assets, stored objects and the ledger; that is a separate spec, not a P0 list.
- **Live progress in the Library (P1).** A queued/running item shows its current status and a manual "Refresh"; the Library does not open an SSE stream (spec 003's stream stays a Create-video concern).
- **Pagination beyond `?limit=` (P1).** A single bounded page of 50 is enough at this size; a cursor is a follow-up.
- The public share page `/v/{id}` (spec 007): the Library's result panel is the owner's private view, not a public link.
- Filters, search, sort controls, bulk actions, favourites.
- Image generations, real per-preset preview assets (P1), credits/top-up (spec 008).

## Open questions
- None blocking. The Library replaces the need for the in-session strip long-term, but the strip is left untouched here (spec 004 owns it) and the server list is the source of truth for this page.
