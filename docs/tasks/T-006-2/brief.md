# Brief T-006-2: Hero and tool cards

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/006-explore/spec.md` (AC-1, AC-2, AC-3, AC-9)
- Design: `docs/specs/006-explore/design.md` sections **Route + layout**, **Component tree**, **Props**, **Copy § Hero**, **Copy § Tools**, **Accessibility**, **Files**
- Existing patterns: `apps/web/src/ui/ButtonLink.tsx`, `apps/web/src/ui/Button.tsx`, `apps/web/src/ui/buttonStyles.ts`, `apps/web/src/features/home/HomePage.tsx` (the copy you are superseding), `apps/web/src/styles.css` (tokens)
- Provided by T-006-1: `apps/web/src/features/explore/exploreCopy.ts`, `apps/web/src/features/explore/toolCards.ts`

## Goal
The top of the Explore page: a hero (`h1`, subtitle, two CTAs) and the five tool cards, as small components that `ExplorePage` (T-006-4) can drop in without further edits.

## Allowed files (touch nothing else)
- `apps/web/src/features/explore/ExploreHero.tsx` (new)
- `apps/web/src/features/explore/ToolCard.tsx` (new)
- `apps/web/src/features/explore/ToolCards.tsx` (new)
- `docs/tasks/T-006-2/report.md`

## Must reuse
- `apps/web/src/ui/ButtonLink.tsx` for both hero CTAs (primary → `/create/video`, secondary → `#effects`). Do not write a raw `<a>` for internal routes.
- `apps/web/src/features/explore/exploreCopy.ts` (T-006-1) for **every** string, and `toolCards.ts` (T-006-1) for the card data (`TOOL_CARDS`). No user-visible literal may appear in these components.
- Tailwind v4 utilities only, with the tokens in `styles.css` (`text-accent`, `bg-surface`, `border-border`, `text-muted`, `font-display`). No new colours, no CSS modules, no inline `style`.
- The `focus-visible:outline-accent` focus pattern already used by `ui/buttonStyles.ts`.

## Acceptance checks
- [ ] `ExploreHero` renders exactly one `h1` (the copy string), the subtitle, and two `ButtonLink`s: primary "Start creating" → `/create/video`, secondary "Browse effects" → `#effects`.
- [ ] The `#effects` target id is documented by this task (T-006-3 puts `id="effects"` on the gallery section); the anchor must not 404 or jump nowhere once T-006-4 assembles the page.
- [ ] `ToolCard` renders **one** link for the whole card (label + description inside it), so there is exactly one tab stop per card.
- [ ] `ToolCards` maps `TOOL_CARDS` (5 entries, design order) into a responsive grid: 1 column, 2 at `sm`, 5 at `lg`.
- [ ] Every label and description is visible text — nothing depends on hover, `title`, or an icon-only control.
- [ ] Each card has a visible `focus-visible` ring and a hover style that does not move layout.
- [ ] No file over 200 lines; no function over 40 lines; complexity ≤ 8; `max-depth` ≤ 3 (`npm run lint`).

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- The gallery and its states (T-006-3), `ExplorePage`/routing (T-006-4).
- Editing `exploreCopy.ts`/`toolCards.ts` (T-006-1 owns them). If a string is missing, report it instead of adding it here.
- Contract/API changes, `styles.css`, `package.json`, any create-video file.

## Report
Write `docs/tasks/T-006-2/report.md` using `docs/templates/report.md`. Don't commit unless the brief says to; the orchestrator handles docs sync and commits.
