# Brief T-002-2: Web shell (Vite + React + TS)

You are the **implementer** for this one task. Before starting:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.

## Context links
- Spec: `docs/specs/002-walking-skeleton/spec.md` (AC-2, AC-3, AC-7; UI states section)
- Design: `docs/specs/002-walking-skeleton/design.md` (API contract, Flow steps 1–4)
- Contract: `packages/contracts/openapi.json`, paths `GET /api/v1/me`, `POST /api/v1/auth/guest`
- Visual reference: `docs/research/flows/explore.md` § Global chrome; screenshot `docs/research/screenshots/01-explore-hero-and-tool-cards.png`

## Goal
A dark, polished app shell with a 5-item nav and a working one-click guest session against the real API. Later specs add pages into it.

## Allowed files (touch nothing else)
- `apps/web/**`

## Required setup
- **Package manager:** npm (a `package-lock.json` must exist; Railway's Docker build uses `npm ci`).
- **Stack:** Vite + React 18/19 + TypeScript strict, `react-router-dom`, Tailwind CSS v4 (`@tailwindcss/vite`), `openapi-fetch`, `openapi-typescript`.
- **Scripts in `package.json`:**
  - `dev`: Vite, with the server proxy `/api` → `http://localhost:8000`
  - `build`: output in `apps/web/dist`, assets under `dist/assets/` (FastAPI mounts `/assets`)
  - `typecheck`: `tsc --noEmit`
  - `lint`: `eslint .`
  - `gen:api`: `openapi-typescript ../../packages/contracts/openapi.json -o src/api/generated/schema.d.ts`
- **`eslint.config.js`** enforcing STANDARDS: `max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `@typescript-eslint/naming-convention` (camelCase functions and variables, PascalCase components and types), react-hooks rules. Ignore `dist` and `src/api/generated`.

## Structure (feature folders; each file ≤200 lines, one component per file)
```
src/main.tsx                     mount + router
src/App.tsx                      routes: / (HomePage), /create/video, /create/image, /library, /credits (placeholders via EmptyState)
src/styles.css                   Tailwind import + design tokens
src/ui/Button.tsx                primary (accent) / secondary variants, loading + disabled states
src/ui/AppShell.tsx              sticky header: wordmark, NavLink items, right-side slot; <Outlet/>
src/ui/EmptyState.tsx            title + description + optional action
src/api/client.ts                createClient<paths>({ baseUrl: "" }) from openapi-fetch
src/api/generated/schema.d.ts    generated, never hand-edited
src/features/session/useSession.ts   loads /me (401 = signed out), exposes startGuestSession(), status
src/features/session/GuestButton.tsx "Continue as guest": idle / loading / error states
src/features/session/SessionBadge.tsx "Guest · <first 6 chars of id>"
src/features/home/HomePage.tsx   hero heading + subline + GuestButton, or a "Create video" link when signed in
```

## Design tokens (dark, from the research screenshots; original work, not a copy)
- Background `#0b0b0d`, surface `#16171a`, border `#26282d`, text `#f2f3f5`, muted `#8b9099`.
- Accent `#d7ff1f` with text `#0b0b0d` on it.
- **Display headings:** a condensed uppercase font from Google Fonts (e.g. "Anton"), with a system fallback stack. **Body:** Inter, with a system fallback.
- **Nav labels:** Explore, Create video, Create image, Library, Credits. The active item uses the accent colour.
- **Responsive:** the nav collapses into a horizontally scrollable row under 640px, with no horizontal page scroll.

## Must reuse
- Every button uses `ui/Button`. Every placeholder page uses `ui/EmptyState`. Every API call goes through `api/client.ts` with the generated types (no raw `fetch`).

## Acceptance checks
- [ ] AC-2: the shell renders dark, with the 5 nav items, and "Continue as guest" is the primary CTA when signed out
- [ ] AC-3 (web part): clicking the CTA calls `POST /api/v1/auth/guest`, the badge shows `Guest · xxxxxx`, and after a reload `/me` still returns the same user
- [ ] UI states from the spec: loading (spinner, disabled), error (inline "Couldn't start a session. Try again."), success (the CTA becomes a "Create video" link)
- [ ] Nothing in `src/` exceeds the STANDARDS limits

## Verify command (paste its full output in report.md)
```
cd apps/web && npm install && npm run gen:api && npm run lint && npm run typecheck && npm run build && cd ../.. && scripts/check-standards
```
Then the end-to-end check. The database is already running in docker compose, and the API needs no env beyond the defaults:
```
STATIC_DIR=../web/dist uv --directory apps/api run uvicorn app.main:app --port 8000 &
curl -s localhost:8000/ | head -5          # the SPA's index.html
curl -s -i -X POST localhost:8000/api/v1/auth/guest | head -12   # 201 + set-cookie
kill %1
```

## Out of scope
- Explore content, presets, generation, credits data, auth providers other than guest, the Dockerfile, any `apps/api` change.
- Don't commit. The orchestrator reviews and commits.

## Report
Write `docs/tasks/T-002-2/report.md` using `docs/templates/report.md`.
