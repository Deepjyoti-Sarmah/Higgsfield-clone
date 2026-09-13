# Report T-006-2

**Agent / model / tool:** implementer · deepseek-flash · DeepSeek Harness (DSH), working directly
**Result:** DONE

## Files changed
| File | New/Edit | Responsibility |
|---|---|---|
| `apps/web/src/features/explore/ExploreHero.tsx` | New | `h1` + subtitle + two `ButtonLink` CTAs; reads `exploreCopy.hero` |
| `apps/web/src/features/explore/ToolCard.tsx` | New | one tool card as a single `Link` (label + description inside) |
| `apps/web/src/features/explore/ToolCards.tsx` | New | maps `TOOL_CARDS` into the 1 → 2 (`sm`) → 5 (`lg`) grid |
| `docs/tasks/T-006-2/report.md` | New | this report |

Nothing else was touched. **No commit** (the orchestrator owns docs sync + the commit).

## What each component does
- **`ExploreHero`** — one `<section>` containing exactly one `h1` (`exploreCopy.hero.h1`), the subtitle, and two `ButtonLink`s: primary → `exploreCopy.hero.primaryHref` (`/create/video`), secondary with `variant="secondary"` → `exploreCopy.hero.secondaryHref` (`#effects`). Wrapped in `mx-auto max-w-2xl` with `text-center`; the page gutters stay `AppShell`'s.
- **`ToolCard`** — a single react-router `<Link>` wrapping both the label and the description, so the whole card is **one tab stop** and one activation target. Focus ring via the shared `focus-visible:outline-2 outline-offset-2 outline-accent` pattern from `ui/buttonStyles.ts`; hover changes only `border-color` (`hover:border-accent/60`), so nothing moves.
- **`ToolCards`** — `<ul>` grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`) with one `<li>` per `TOOL_CARDS` entry, `h-full` on the item and the link so the five cards stay equal height when a description wraps.

`grep` confirms **no user-visible string literal** appears in any of the three components — the only quoted strings are `className` values.

## Reused
- `ui/ButtonLink` for both CTAs (no raw `<a>` for an internal route; the `#effects` secondary is a hash target, which `ButtonLink`'s router `Link` handles fine).
- `exploreCopy.hero` (T-006-1) for every string **and** both hrefs; `TOOL_CARDS` (T-006-1) for the five cards — including their `to` values, so the AppShell nav and the tool cards cannot drift.
- `ui/buttonStyles.ts` focus-ring vocabulary; `styles.css` tokens only (`text-muted`, `bg-surface`, `border-border`, `text-text`, `accent/60`) — no new colour, no inline `style`, no CSS module.

## Verify output (full paste, no summarising)
```
$ npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards

> web@0.0.0 lint
> eslint .


> web@0.0.0 typecheck
> tsc --noEmit


> web@0.0.0 build
> tsc -b && vite build

vite v8.3.0 building client environment for production...
transforming...
✓ 78 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.74 kB │ gzip:   0.40 kB
dist/assets/index-BoOzhPFN.css   25.52 kB │ gzip:   5.44 kB
dist/assets/index-CW0W570A.js   321.06 kB │ gzip: 100.40 kB

✓ built in 195ms
check-standards: ok (0 violations)
```
Exit status of the chain: **0**.

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
`npm run lint` also passed (`max-lines: 200`, `max-lines-per-function: 40`, `max-depth: 3`, `complexity: 8`, `naming-convention`). The three files are 19, 14 and 14 lines.

## Open issues / guesses / things skipped
1. **`#effects` target is T-006-3's to provide.** The hero's secondary CTA points at `#effects`; per the design and T-006-3's brief, `PresetGallery` puts `id="effects"` on the gallery `<section>`. Until T-006-4 (ExplorePage) renders both, the anchor has no target on any live page — documented here so the contract is explicit, nothing to change in this task.
2. **`ToolCard` type is aliased on import** (`import type { ToolCard as ToolCardData } from "./toolCards"`), because `toolCards.ts` exports a *type* named `ToolCard` and this file declares a *component* of that name. This is the collision T-006-1 flagged; no rename of T-006-1's file was needed.
3. **Hero `h1` styling is `text-4xl sm:text-5xl`**, exactly the retired `HomePage` hero's scale, and deliberately **not** `font-display`: only the AppShell logo uses `font-display`, so adding it here would invent a heading convention the design did not ask for. If a display face is wanted for the hero, that is a one-class change — flagged for the reviewer rather than decided unilaterally.
4. **No consumer yet.** `ToolCards`/`ExploreHero` are not imported anywhere until T-006-4 wires `ExplorePage`, so the JS bundle is unchanged (78 modules, 321.06 kB). They are still fully type-checked: `apps/web/tsconfig.app.json` has `include: ["src"]`, so `tsc -b` compiles unreferenced files too — which is why a type error in them would fail `npm run build`.
5. **One `h1` per page** is satisfied by construction: `ExploreHero` owns the only `h1`; T-006-3's category headings are `h2` (and `ui/EmptyState` also renders an `h2`).
6. **Skipped:** no component/DOM tests — the repo's vitest runs in a Node environment with no jsdom/testing-library (design § Test strategy), so hero/card rendering is covered by T-006-4's manual pass and `verify-slice`, not unit tests. The brief lists no test file for this task.
7. **Unverified in a browser.** I did not start the dev server (Explore is not routed until T-006-4), so the visual result (grid breakpoints, equal card heights) is reasoned from the classes, not observed. `verify-slice` is the intended check.
8. **Capture:** my tool cannot be wrapped by `scripts/agent-run`, so per AGENTS.md the orchestrator must export this session's transcript into `.agent-logs/` at commit time.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Explore hero + tool cards: `ExploreHero` (one `h1`, subtitle, two `ButtonLink` CTAs) and `ToolCard`/`ToolCards` (5 cards from `TOOL_CARDS`, one link each, 1→2→5 grid) | `apps/web/src/features/explore/{ExploreHero,ToolCard,ToolCards}.tsx` | `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards` → all pass, 0 violations | 2026-09-13 |
