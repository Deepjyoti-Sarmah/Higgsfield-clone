# Design 005: Library (my generations)

**Spec:** `docs/specs/005-library/spec.md` (APPROVED)
**Backend:** `docs/specs/003-generation-core/design.md` (ownership, presigned URLs), `docs/specs/004-create-video/design.md` (auto-guest runner, result actions).
**Contract:** **ONE** new route — `GET /api/v1/jobs`. Every existing path and schema is untouched (spec AC-12). **No migration:** the query is already indexed.
**Web patterns:** `docs/specs/006-explore/design.md` (shared data in `api/`, Files table, AC map), `docs/STANDARDS.md` § Styling.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Route | Route + layout | T-005-5 |
| AC-2 Signed out | Auto-guest flow, `api/guestSession.ts` | T-005-2 |
| AC-3 List | API contract, `useLibrary` | T-005-1 (api), T-005-2 (hook) |
| AC-4 Item | Component tree, Copy § Item | T-005-4 |
| AC-5 Open a result | `?job=` selection, `LibraryResultView` | T-005-4 |
| AC-6 Failed item | Copy § Result, item states | T-005-4 |
| AC-7 Missing item | `?job=` selection | T-005-4 |
| AC-8 Empty | Copy § States | T-005-3 (copy), T-005-4 (UI) |
| AC-9 Error | Copy § States, `useLibrary` status | T-005-2, T-005-4 |
| AC-10 Loading | Copy § States | T-005-3, T-005-4 |
| AC-11 Accessibility | Accessibility | T-005-4 |
| AC-12 Contract discipline | API contract, Data | T-005-0, T-005-1 |

## API contract (the only contract change)
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/api/v1/jobs` | query `limit` (int, 1–100, default 50) | **200** `LibraryListResponse { items: LibraryItemResponse[] }`, newest first | **401** `ErrorResponse` signed out · **422** invalid `limit` |

Ownership: `require_current_user`; the query filters `job.user_id == caller`. Another user's job is simply **absent** from the list (no 404, no existence leak) — the same rule `GET /jobs/{id}` applies per row.

### `LibraryItemResponse` (new; frozen by T-005-0)
| Field | Type | Meaning |
|---|---|---|
| `id` | uuid | the job id; the Library's `?job=` key |
| `status` | `"queued" \| "running" \| "succeeded" \| "failed"` | same literal as `JobStatus` |
| `preset_slug` | string | deep-link key for "Make another" |
| `preset_name` | string | shown as visible text; falls back to the slug if the preset row is gone |
| `thumbnail_url` | string \| null | poster when ready, else the input image when ready, else null |
| `video_url` | string \| null | the ready output video, else null |
| `created_at` | datetime | list ordering key and the item's time text |
| `error_message` | string \| null | user-safe failure copy for a failed item |

**Why a dedicated item schema instead of reusing `JobResponse`:** `JobResponse` carries `prompt`, `credit_cost`, `input_asset_id`, `started_at`, `finished_at` that this list never renders, and it would mint **three** presigned URLs per row (input + video + poster). `LibraryItemResponse` is the page's exact shape: one URL for the thumbnail and one for the video. Reusing `JobResponse` would also mean the Library inherits every future job field, which is the wrong coupling for a list.

## Data
**Nothing changes.** `GET /jobs` reads `job` joined to `preset`/`asset` for names and URLs.

- Index: `ix_job_user_created (user_id, created_at DESC)` already exists on `job` (`apps/api/app/models/job.py`), so `WHERE user_id = :id ORDER BY created_at DESC, id DESC` is index-served. **No migration, no model change.**
- Ledger, claims, leases and the worker are untouched: the Library is read-only. Architecture invariants 1–5 (`docs/architecture/architecture.md`) are unaffected.

## Flow
1. `/library` mounts → `useLibrary()` reads the session from the outlet context (`SessionContextValue`, the HomePage precedent). Signed out → it calls `startGuestSession()` through the moved `api/guestSession.ts` runner, so the page never opens a login wall (AC-2).
2. `apiClient.GET("/api/v1/jobs", { params: { query: { limit: 50 } } })`. A `401` is retried once after the guest session is ensured; non-200/throw → `status: "error"` (AC-9).
3. API: `list_jobs` (router) → `require_current_user` → service `list_owned_jobs_view(session, storage, settings, user_id, limit)` → repository `list_owned_jobs(session, user_id, limit)` → per job, resolve `preset_name` and the ready asset URLs with the existing `_ready_url` helper → `LibraryListResponse`.
4. Web: `status === "ready" && items.length === 0` → empty state (AC-8); otherwise the list. Selecting a **succeeded** item writes `?job=<id>` and renders `LibraryResultView` from the item **already in memory** — no `/jobs/{id}` call (AC-5).
5. `?job=<id>` not present in the list → the missing panel (AC-7). A `failed` item never renders a video (AC-6).

## Component tree
```
LibraryPage                       (features/library/LibraryPage.tsx)
├── title + subtitle              (exploreCopy-style copy table: libraryCopy)
├── LibraryStates                 loading | error | empty   (LibraryStates.tsx)
│   ├── ui/EmptyState             error + empty variants
│   └── ui/Button                 "Retry"
├── LibraryList                   <ul>            (LibraryList.tsx)
│   └── LibraryItem ×N            <li><button>    (LibraryItem.tsx)
└── LibraryResultView             selected item   (LibraryResultView.tsx)
```
- `LibraryPage` props: none — it calls `useLibrary()` and `useLibraryJobParam()`.
- `LibraryList` props: `{ items: LibraryItem[]; selectedJobId: string | null; onSelect: (id: string) => void }`.
- `LibraryItem` props: `{ item: LibraryItemResponse; isSelected: boolean; onSelect: () => void }`.
- `LibraryStates` props: `{ status: "loading" | "error" | "empty"; onRetry: () => void; emptyAction: ReactNode }`.
- `LibraryResultView` props: `{ item: LibraryItemResponse }`.

## Copy (`libraryCopy.ts`, one object; no inline literals in components)
| Key | Value |
|---|---|
| `page.title` | "Library" |
| `page.subtitle` | "Everything you have generated." |
| `states.loading.srText` | "Loading your library" (`skeletonCount` 4) |
| `states.error` | title "We couldn't load your library." · body "Check your connection and try again." · action "Retry" |
| `states.empty` | title "No generations yet." · body "Generate your first video and it will show up here." · action "Create video" |
| `item.status` | queued "Queued" · running "Generating" · succeeded "Ready" · failed "Failed" |
| `item.failedFallback` | "This generation failed and its credits were refunded." |
| `item.missing` | "This generation is no longer available." |
| `item.openLabel(name)` | `` `Open ${name}` `` (accessible name for the row button) |
| `result.download` | "Download" |
| `result.makeAnother` | "Make another" |
| `result.close` | "Close" |
| `time.label(iso)` | `formatCreatedAt` output |

### `formatCreatedAt(iso)` (pure, tested)
`Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" })` → `"13 Sep 2026, 19:40"`. **UTC is deliberate:** a local-time renderer would make the unit test depend on the machine's timezone. Invalid input returns `""` rather than throwing.

## Files (each ≤ 200 lines; one component per file; paths relative to the repo root)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `apps/api/app/schemas/jobs.py` | Edit | T-005-0 | `+ LibraryItemResponse`, `+ LibraryListResponse` (existing classes untouched) |
| `apps/api/app/routers/jobs.py` | Edit | T-005-0 → T-005-1 | T-005-0 adds the 501 stub; T-005-1 replaces the body keeping name/signature/responses |
| `apps/api/app/repositories/jobs.py` | Edit | T-005-1 | `list_owned_jobs(session, user_id, limit)` |
| `apps/api/app/services/job_views.py` | Edit | T-005-1 | `LibraryItemView` + `list_owned_jobs_view(...)` reusing `_ready_url` |
| `apps/api/tests/test_library_api.py` | New | T-005-1 | list, ordering, limit, ownership isolation, 401 |
| `apps/web/src/api/guestSession.ts` | New (moved) | T-005-2 | the spec-004 runner, moved out of the create-video feature |
| `apps/web/src/features/create-video/useGuestSessionRunner.ts` | Delete | T-005-2 | superseded by `api/guestSession.ts` |
| `apps/web/src/features/create-video/CreateVideoPage.tsx` | Edit | T-005-2 | the runner import path only |
| `apps/web/src/api/library.ts` | New | T-005-2 | `LibraryItem`, `LibraryState`, `useLibrary` |
| `apps/web/src/features/library/libraryCopy.ts` | New | T-005-3 | every user-visible Library string |
| `apps/web/src/features/library/formatCreatedAt.ts` | New | T-005-3 | deterministic UTC time text |
| `apps/web/src/features/library/formatCreatedAt.test.ts` | New | T-005-3 | formatting + invalid input |
| `apps/web/src/features/library/useLibraryJobParam.ts` | New | T-005-4 | `?job=` read/write + missing detection |
| `apps/web/src/features/library/LibraryPage.tsx` | New | T-005-4 | wire `useLibrary` → title, states, list, result |
| `apps/web/src/features/library/LibraryList.tsx` | New | T-005-4 | `<ul>` of items |
| `apps/web/src/features/library/LibraryItem.tsx` | New | T-005-4 | one row: thumbnail, name, time, status, button |
| `apps/web/src/features/library/LibraryStates.tsx` | New | T-005-4 | skeleton / error + Retry / empty |
| `apps/web/src/features/library/LibraryResultView.tsx` | New | T-005-4 | succeeded / failed / missing panel |
| `apps/web/src/App.tsx` | Edit | T-005-5 | `library` route → `LibraryPage` (replaces the placeholder) |
| `docs/tasks/T-005-{0..5}/report.md` | New | each | per-task report |

## Reused
- API: `require_current_user`, `get_session`, `get_object_storage`, `get_settings`, `find_active_preset`, `find_assets_by_ids`, `build_asset_url` and the `_ready_url` rule from `services/job_views.py`, `ErrorResponse`. The existing `ix_job_user_created` index.
- Web: `apiClient` + `api/generated/schema.d.ts` (never a hand-written API shape), the moved guest-session runner, `ui/Button`, `ui/ButtonLink`, `ui/EmptyState`, the `?preset=` deep link for "Make another" (spec 004/006 contract), `styles.css` tokens, the eslint limits.
- The `api/` shared-hook precedent set by `api/presets.ts` in T-006-1 — the runner moves there instead of the Library importing another feature's internals.

## Risks
- **N presigned URLs per response.** Up to 50 rows × 2 URLs. Presigning is local CPU work (no network, per design 003), so this is bounded and cheap; `limit` caps it at 100.
- **The list is not live.** A queued/running row shows the status returned at fetch time until Refresh. Deliberate P0 (spec § Out of scope); live progress stays in Create video's SSE.
- **No delete, so the list only grows.** Bounded by `limit`; P1 adds delete plus a cursor.
- **Moving the runner touches spec 004's files** (`CreateVideoPage.tsx` import, one deleted file). Mitigated the same way T-006-1 handled `usePresets`: the runner keeps identical behaviour, only its path changes, and T-005-2 owns every touched file.
- **Timezone.** `formatCreatedAt` renders UTC so its unit test is deterministic; if the demo wants local time that is a P1 change with a fakeable clock.
- **`preset_name` when a preset row is gone** falls back to the slug (the existing `job_views` rule), so a historical item never renders an empty name.
