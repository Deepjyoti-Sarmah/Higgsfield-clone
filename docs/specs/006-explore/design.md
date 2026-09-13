# Design 006: Explore (signed-out landing page)

**Spec:** `docs/specs/006-explore/spec.md` (APPROVED)
**Backend:** `docs/specs/003-generation-core/design.md`. **No contract change** — the page uses one existing path,
`GET /api/v1/presets`. `packages/contracts/openapi.json` stays byte-identical.
**Web patterns it follows:** `docs/specs/004-create-video/design.md` (files table, AC map, hook-per-concern),
`apps/web/src/ui/*`, `api/client.ts` (typed `openapi-fetch`), the tokens in `styles.css`, the lint limits in
`eslint.config.js`, and the Tailwind v4 rule in `docs/STANDARDS.md` § Styling.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Layout | Route + layout, Component tree | T-006-2, T-006-3, T-006-4 |
| AC-2 Hero | Component tree, Copy § Hero | T-006-2 |
| AC-3 Tool cards | `toolCards.ts`, Component tree, Copy § Tools | T-006-1 (data), T-006-2 (UI) |
| AC-4 Effect gallery | Shared preset data, `groupPresetsByCategory`, `PresetGallery` | T-006-1 (helper), T-006-3 (UI) |
| AC-5 Preset card | `PresetGalleryCard`, `presetTileStyles`, Copy § Card | T-006-1 (tiles), T-006-3 (card) |
| AC-6 Recreate | `recreateHref`, Recreate deep-link | T-006-1 (helper), T-006-3 (link) |
| AC-7 Signed out | Shared preset data, Recreate deep-link | T-006-1, T-006-4 |
| AC-8 States | `PresetGalleryStates`, Copy § States | T-006-3 |
| AC-9 Accessibility | Accessibility | T-006-2, T-006-3 |
| AC-10 No contract change | API contract used | T-006-0 (this pack) |

## API contract used (no changes)
One path, already in `openapi.json` and already public (no auth dependency in
`apps/api/app/routers/presets.py`).

| Method | Path (exact, from openapi.json) | Used by | Success | Errors handled |
|---|---|---|---|---|
| GET | `/api/v1/presets` | `usePresets` (`api/presets.ts`) | 200 `PresetListResponse { presets: PresetResponse[] }` | network / non-200 → `status: "error"` |

**Types** come from `api/generated/schema.d.ts` only, never hand-written:
`Preset = components["schemas"]["PresetResponse"]` (`slug`, `name`, `description`, `category`,
`credit_cost`, `preview_url: string | null`), `PresetCategory = Preset["category"]`
(`"camera" | "cinematic" | "dynamic"`).

**No new route is needed.** The gallery is a read of an existing public list. The P1 sample-outputs gallery is out
of scope precisely because it *would* need new assets and possibly a new public route; it must not be smuggled in
here.

## Route + layout
- Route: `/` (the index route). The nav already labels it "Explore" (`ui/AppShell.tsx`), so no nav change.
- `features/home/HomePage.tsx` is retired: its two lines of hero copy are superseded by `ExploreHero`, which is a
  superset (same H1, plus CTAs), so nothing is lost. Nothing else imports `HomePage`.
- Layout, top to bottom, inside `AppShell`'s `<main>` (`mx-auto` column, `max-w-6xl`):
  1. **Hero** — `h1` + subtitle + primary/secondary CTAs.
  2. **Tool cards** — 5 equal cards, `grid` 1 col → 2 (`sm`) → 5 (`lg`).
  3. **Effect gallery** — section heading + one `section` per category; cards `grid` 1 → 2 (`sm`) → 3 (`lg`).
- Widths use the existing page gutters from `AppShell`; Explore adds only inner `mx-auto max-w-*` wrappers so it
  never assumes the shell's padding.

## Component tree
```
ExplorePage                      (features/explore/ExplorePage.tsx)
├── ExploreHero                  (features/explore/ExploreHero.tsx)
│   └── ui/ButtonLink ×2         primary -> /create/video, secondary -> #effects
├── ToolCards                    (features/explore/ToolCards.tsx)
│   └── ToolCard ×5              (features/explore/ToolCard.tsx)
└── PresetGallery                (features/explore/PresetGallery.tsx)
    ├── PresetGalleryStates      loading | error | empty   (features/explore/PresetGalleryStates.tsx)
    │   ├── ui/EmptyState        error + empty variants
    │   └── ui/Button            "Retry"
    └── section per category
        ├── h2 + count
        └── ul
            └── PresetGalleryCard ×N   (features/explore/PresetGalleryCard.tsx)
                └── Link               "Recreate" -> recreateHref(preset.slug)
```

### Props (exact)
| Component | Props |
|---|---|
| `ExplorePage` | none; calls `usePresets()` and renders the three sections |
| `ExploreHero` | none; reads `exploreCopy` |
| `ToolCards` | none; maps `TOOL_CARDS` |
| `ToolCard` | `{ label: string; description: string; to: string }` |
| `PresetGallery` | `{ state: PresetsState }` |
| `PresetGalleryStates` | `{ status: "loading" \| "error" \| "empty"; onRetry: () => void }` |
| `PresetGalleryCard` | `{ preset: Preset }` |

No component takes the whole session object: Explore is read-only and must render identically signed in or out.

## Shared preset data (the one structural change)
`usePresets` currently lives in `features/create-video/usePresets.ts`. Explore needs the same list, and
`docs/STANDARDS.md` forbids a feature importing another feature's internals. Rule of two therefore applies.

**Decision:** move the hook and its types to a shared data module, `apps/web/src/api/presets.ts`:

```ts
export type Preset = components["schemas"]["PresetResponse"]
export type PresetsState = { status: "loading" | "ready" | "error"; presets: Preset[]; reloadPresets: () => void }
export function usePresets(): PresetsState   // same implementation, unchanged behaviour
```

The blast radius is small and was measured, not guessed:
- `usePresets` has exactly **one** importer today: `features/create-video/CreateVideoPage.tsx`.
- `Preset` / `PresetsState` are imported through `features/create-video/createVideoTypes.ts`, which keeps every
  existing import working by **re-exporting** them from `api/presets` instead of defining them.
- `features/create-video/usePresets.ts` is deleted (no forwarding wrapper: STANDARDS forbids a module that only
  forwards calls).

`api/` is where the typed client lives; a hook over that client is data access, not a feature, so it does not
violate the `api/` description in STANDARDS. Explore then imports `usePresets` and `Preset` from `api/presets`
and never from `features/create-video`.

## Recreate deep-link (AC-6)
Explore does **not** import `usePresetSelection`. The reuse is the URL contract that spec 004 already reads:

```ts
// features/explore/recreateHref.ts
export function recreateHref(slug: string): string {
  return `/create/video?preset=${encodeURIComponent(slug)}`
}
```

`CreateVideoPage` → `usePresetSelection` → `useSearchParams().get("preset")` selects the matching preset and marks
an unknown slug. So "Recreate" is a plain router `Link`, which keeps keyboard, middle-click and "open in new tab"
behaviour. A unit test asserts the exact string, including encoding, because this is the seam between two specs.

## Copy (`exploreCopy.ts`, one object, no inline literals in components)
### Hero
- `h1`: "Make your next video"
- `subtitle`: "Pick an effect, drop in a photo, and generate a 5-second clip. Start free as a guest."
- `primaryCta`: "Start creating" → `/create/video`
- `secondaryCta`: "Browse effects" → `#effects`

### Tools
| label | description | to |
|---|---|---|
| Explore | "Browse every effect and start creating." | `/` |
| Create video | "Turn a photo into a 5-second clip." | `/create/video` |
| Create image | "Generate images from a prompt." | `/create/image` |
| Library | "Every generation from this session." | `/library` |
| Credits | "Your balance and top-ups." | `/credits` |

### Gallery
- title: "Effects"
- subtitle: "Every effect is a camera move you can apply to your own photo."
- category labels: camera → "Camera", cinematic → "Cinematic", dynamic → "Dynamic"
- card cost: `{credit_cost} credits` (rendered as "20 credits")
- card CTA: "Recreate"
- card aria label: `` `Recreate ${preset.name}` ``
- image alt (when `preview_url` is set): `` `${preset.name} preview` ``

### States (AC-8)
| State | Copy |
|---|---|
| Loading | visually: 6 skeleton tiles; `aria-busy="true"`, screen-reader text "Loading effects" |
| Error | title "We couldn't load the effects." · body "Check your connection and try again." · action "Retry" |
| Empty | title "No effects yet." · body "Effects will appear here as soon as they are published." |

The three states reuse `ui/EmptyState` (title + description + optional action) so Explore adds no new state
primitive; the loading state is the only bespoke one.

## Accessibility (AC-9)
- One `h1` (hero); each category is an `h2` inside a `section` with `aria-labelledby`.
- The gallery `<ul>` gives every card a list item; card names are real text nodes, never `title`/hover-only.
- "Recreate" is an `<a>` (router `Link`) with an accessible name that includes the preset name, so screen-reader
  users do not hear twelve identical "Recreate" links.
- Decorative fallback tiles are `aria-hidden="true"`; the card's text carries the meaning.
- Focus uses the existing `focus-visible:outline-accent` pattern from `ui/buttonStyles.ts`.
- No autoplaying media on this page, so there is no reduced-motion branch to design (unlike spec 004's canvas).

## Test strategy (web)
Vitest runs in a **Node** environment in this repo (no jsdom, see spec 004 T-004-2's note), so tests cover the
pure helpers only — the same approach spec 004 used:

| Test | Proves |
|---|---|
| `groupPresetsByCategory.test.ts` | fixed category order, empty categories omitted, all presets kept, unknown category handled |
| `recreateHref.test.ts` | exact `/create/video?preset=<slug>` string, URL-encoding, round-trip through `URLSearchParams` |

Behaviour that needs a DOM (loading/error rendering, focus order) is covered by T-006-0's `verify-slice` on the
live URL, not by unit tests. Component tests would need jsdom, which is a separate, deliberate decision.

## Files (each ≤ 200 lines; one component per file; paths relative to `apps/web/`)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `src/api/presets.ts` | New | T-006-1 | `Preset`, `PresetsState`, `usePresets` (moved from the create-video feature) |
| `src/features/create-video/createVideoTypes.ts` | Edit | T-006-1 | re-export `Preset`, `PresetsState` from `api/presets`; other types unchanged |
| `src/features/create-video/usePresets.ts` | Delete | T-006-1 | superseded by `api/presets.ts` |
| `src/features/create-video/CreateVideoPage.tsx` | Edit | T-006-1 | import `usePresets` from `../../api/presets` |
| `src/features/explore/exploreCopy.ts` | New | T-006-1 | every user-visible Explore string (Copy above) |
| `src/features/explore/toolCards.ts` | New | T-006-1 | `TOOL_CARDS` + `ToolCard` type (5 entries) |
| `src/features/explore/groupPresetsByCategory.ts` | New | T-006-1 | pure grouping into the fixed category order |
| `src/features/explore/groupPresetsByCategory.test.ts` | New | T-006-1 | grouping/order/empty edges |
| `src/features/explore/recreateHref.ts` | New | T-006-1 | `recreateHref(slug)` deep-link builder |
| `src/features/explore/recreateHref.test.ts` | New | T-006-1 | exact string + encoding |
| `src/features/explore/presetTileStyles.ts` | New | T-006-1 | `PresetCategory` → literal fallback-tile classes |
| `src/features/explore/ExploreHero.tsx` | New | T-006-2 | hero heading, subtitle and two CTAs |
| `src/features/explore/ToolCard.tsx` | New | T-006-2 | one tool card as a single link |
| `src/features/explore/ToolCards.tsx` | New | T-006-2 | the 5-card responsive row |
| `src/features/explore/PresetGalleryCard.tsx` | New | T-006-3 | one effect card: tile, name, category, cost, Recreate link |
| `src/features/explore/PresetGallery.tsx` | New | T-006-3 | gallery section + per-category sections |
| `src/features/explore/PresetGalleryStates.tsx` | New | T-006-3 | loading skeleton / error + Retry / empty |
| `src/features/explore/ExplorePage.tsx` | New | T-006-4 | wire `usePresets` → hero, tools, gallery |
| `src/App.tsx` | Edit | T-006-4 | index route → `ExplorePage` |
| `src/features/home/HomePage.tsx` | Delete | T-006-4 | superseded by Explore |
| `docs/tasks/T-006-{1..4}/report.md` | New | each | per-task report |

## Reused
- `ui/Button` (`Retry`), `ui/ButtonLink` (both hero CTAs), `ui/EmptyState` (error + empty states).
- `ui/AppShell`: the nav already has exactly the 5 items (`/`, `/create/video`, `/create/image`, `/library`,
  `/credits`), so AC-3's routes and the nav cannot drift apart.
- `api/client.ts` `apiClient` + `api/generated/schema.d.ts`; the moved `usePresets` keeps its retry/mounted-ref
  behaviour exactly.
- `features/create-video/usePresetSelection.ts` — **unchanged**; Explore only writes the `?preset=` parameter it
  already reads.
- Design tokens in `styles.css` (no new colours) and Tailwind v4 utilities only.

## Risks
- **Editing spec 004's files.** The move touches `createVideoTypes.ts` and `CreateVideoPage.tsx`. Mitigated by
  re-exporting the types (so no other create-video file changes) and by the measured single importer of
  `usePresets`. T-006-1 owns all four touched files, so no task overlap.
- **`npm run typecheck` is a no-op** (the root tsconfig is solution-style; recorded in `STATUS.md`). Every verify
  command therefore includes `npm run build`, whose `tsc -b` is the real type gate.
- **No preview assets.** `preview_url` is `null` for all 12 presets, so cards render a static tile. The card
  renders `preview_url` when it is present, so a later asset task needs no card change.
- **Tailwind class scanning.** Fallback-tile classes are literal strings in `presetTileStyles.ts`; no class name is
  built dynamically, because Tailwind cannot see those.
- **ESLint limits:** `max-lines` 200, `max-lines-per-function` 40, `max-depth` 3, `complexity` 8 apply to
  components. The gallery's grouping lives in a pure helper and the card is its own file so the page stays small.
- **Retiring `HomePage`.** `/` keeps working (the nav's "Explore" already points there); only the old copy is
  replaced. Nothing else imports `HomePage`.
- **`GET /presets` needs the DB seeded** (migration `0003`). In a fresh environment the gallery is empty rather
  than broken; the empty state is designed and tested by `verify-slice`.
