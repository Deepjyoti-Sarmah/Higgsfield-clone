# Report T-007-4

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH)
**Result:** DONE

## Files changed
- `apps/web/src/features/share/ShareStates.tsx` (new) — `ShareStateKind` + the five states: `loading` (an `aria-busy="true"` 16:9 skeleton with `shareCopy.states.loading.srText` behind `sr-only`), `error` (`EmptyState` + `Button` "Retry" → `onRetry`), `notReady` (`EmptyState` + `Button` "Refresh" → `onRetry`), `notFound` and `failed` (`EmptyState` + `ButtonLink` "Make your own" → `shareCopy.page.ctaHref`, no Retry).
- `apps/web/src/features/share/ShareResult.tsx` (new) — the preset name as the page's only `h1`; the poster is the `<video>`'s `poster`; `<video controls muted playsInline loop preload="metadata">`; `shareCopy.page.attribution`; a `Download` `<a download>` styled with `buttonClasses("secondary")`; `ButtonLink` "Make your own" → `/`. When `video_url` is null it renders **no `<video>` and no Download link**.
- `apps/web/src/features/share/SharePage.tsx` (new) — `useParams()` → `usePublicJob(jobId)`; maps state as the design says (`ready`+`succeeded` → `ShareResult`; `ready`+`queued`/`running` → `notReady`; `ready`+`failed` → `failed`; `notFound`/`error`/`loading` → the matching state); sets `document.title` from `shareCopy.page.documentTitle(job.preset_name)` and restores it on unmount. Nothing branches on identity.
- `docs/tasks/T-007-4/report.md` (this file).
- **Not committed**, and no other file touched (no `App.tsx`, no T-007-3 files, no `ui/**`, no `styles.css`).

## Reused
- `apps/web/src/api/share.ts` (T-007-3): `usePublicJob`, `PublicJob`, `PublicJobState` — the only data source; no new fetch, no `apiClient` in the components.
- `apps/web/src/features/share/shareCopy.ts` (T-007-3): **every** user-visible string (`states.*`, `page.attribution`, `page.cta`, `page.ctaHref`, `page.documentTitle`, `result.download`).
- `ui/Button`, `ui/ButtonLink`, `ui/EmptyState` (so every state's copy renders as `h2` + paragraph text, never colour-only) and `ui/buttonStyles.buttonClasses` for the Download anchor.
- Patterns copied, not imported: `features/library/LibraryStates.tsx` (skeleton + `EmptyState` shape), `features/create-video/ResultView.tsx` (the video markup; read only — no cross-feature import), `CreateVideoPage`'s `usePageTitle` effect style.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint

> web@0.0.0 lint
> eslint .

-> exit 0

$ npm --prefix apps/web run typecheck

> web@0.0.0 typecheck
> tsc -b

-> exit 0

$ npm --prefix apps/web run build

> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 98 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-Cajc0ZMs.css   26.85 kB │ gzip:   5.67 kB
dist/assets/index-DRwkTUYF.js   333.92 kB │ gzip: 103.61 kB

✓ built in 167ms
-> exit 0

$ scripts/check-standards
check-standards: ok (0 violations)
-> exit 0

=== verify command: all steps exit 0 ===
```

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- **The brief's parenthetical is stale:** it says "`npm run typecheck` is a known no-op in this repo". T-000-6 already fixed that — the script is `tsc -b` now, so `typecheck` **is** a real gate in the run above. It matters here because my three files are not imported by `App.tsx` yet (T-007-5 owns the route); Vite tree-shakes unreferenced modules, but `tsconfig.app.json` has `include: ["src"]`, so `tsc -b` still type-checks them. Proof: `tsc -p tsconfig.app.json --noEmit --listFiles` lists `src/features/share/{SharePage,ShareResult,ShareStates}.tsx`.
- **One deliberate deviation from the brief's wording:** the brief says to restore `"Higgsfield"` on unmount "the `CreateVideoPage` `usePageTitle` pattern" — but that pattern reads `createVideoCopy.page.appTitle`, and `shareCopy` (T-007-3) exports **no** base app title. Rather than hard-code a user-visible literal (which the same acceptance checks forbid), `useDocumentTitle` captures `document.title` before changing it and restores that captured value on unmount. If you prefer an explicit constant, add `shareCopy.page.appTitle` — that file is T-007-3's, not mine.
- **The page is unreachable until T-007-5** routes `/v/:jobId` to `SharePage`; that is explicitly out of scope, so no in-browser check was possible from this session.
- `notFound` and `failed` intentionally share one branch (identical action: a `ButtonLink` to `shareCopy.page.ctaHref`, per the design's Copy table — both say "Make your own").
- The loading skeleton and the video use the same `w-full max-w-2xl` box and 16:9 aspect, so replacing the skeleton does not shift the page.
- All five state kinds carry their meaning as text (`EmptyState` title + body) — no colour-only signalling.

## Proposed STATUS.md line (WORKS)
| Share page UI `/v/{id}`: one `h1` (preset name) on success, `controls muted playsInline loop preload="metadata"` video with the poster, `Download`, and "Make your own"; "still generating" / "failed" / "not-found" / error states with Retry or Refresh wired to `usePublicJob.reload`; every string from `shareCopy`; works with no session | `apps/web/src/features/share/{SharePage,ShareResult,ShareStates}.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → lint/tsc clean, 98 modules built, 0 violations (full output in `docs/tasks/T-007-4/report.md`) | 2026-09-13 16:34 |
