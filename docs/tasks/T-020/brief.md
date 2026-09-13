# Brief T-020: reference-look reskin (visual only)

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Reference screenshots (gitignored, never commit): `reference-images/Screenshot from 2026-09-13 *.png`
  (real higgsfield.ai: pure-black bg, electric-lime `#ccff00` CTAs/badges/active nav,
  condensed uppercase headings, dark `#131316` cards, pill buttons, hover Recreate overlay)
- Flow notes: `docs/research/flows/{explore,image-create,video-create,auth}.md`
- Theme: `apps/web/src/styles.css` (already Anton + Inter, lime accent base)

## Goal
Make the clone's six routed pages look like the reference screenshots with
**styles only**: no copy changes, no route changes, no behavior changes, no test changes.

## Allowed files (touch nothing else)
- `apps/web/src/styles.css` (tokens: bg `#000`, surface, border, accent `#ccff00`)
- `apps/web/src/ui/AppShell.tsx` (nav reskin + slim footer, real routes only)
- `apps/web/src/ui/buttonStyles.ts` (subtle lime glow on primary)
- `apps/web/src/features/explore/ExploreHero.tsx` (bigger condensed headline)
- `apps/web/src/features/explore/toolCards.ts` (add a `tag` per card)
- `apps/web/src/features/explore/ToolCard.tsx` (tag pill + glyph + hover ring)
- `apps/web/src/features/explore/PresetGallery.tsx` (lime section/category headings)
- `apps/web/src/features/explore/PresetGalleryCard.tsx` (lime Recreate pill, hover ring/zoom)
- `apps/web/src/features/explore/presetTileStyles.ts` (richer placeholder gradients)
- `apps/web/src/features/create-video/PresetCard.tsx` (lime selected glow)
- `apps/web/src/features/create-video/CreateVideoPanel.tsx` (card polish only)
- `apps/web/src/features/library/LibraryPage.tsx` (heading scale only)
- `apps/web/src/features/credits/CreditsPage.tsx` (heading scale only)
- `docs/tasks/T-020/brief.md` (this file), `docs/tasks/T-020/report.md`
- `docs/STATUS.md`, `docs/PLAN.md`, `docs/WORKLOG.md` (append one line)
- `.agent-logs/*T-020*` (own session transcript export)

## Must reuse
- Existing `@theme` tokens (`bg`, `surface`, `border`, `text`, `muted`, `accent`,
  `accent-ink`, `font-display`); `buttonClasses`; `exploreCopy` strings verbatim.

## Acceptance checks
- [ ] No text/copy string changed anywhere (accessible names identical)
- [ ] No route, behavior, or test file changed
- [ ] `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards` all pass
- [ ] Served bundle contains the new tokens (spot-grep `ccff00` / footer copy)
- [ ] The WhatsApp credential screenshot stays deleted (it is gitignored; verify `git status` clean of it)

## Verify command (paste its full output in report.md)
```
npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards
```

## Out of scope
- Deleting the rest of `reference-images/` (Stage 4 hygiene owns it)
- Rotating the exposed R2 key (needs the human in the Cloudflare dashboard)
- Real gallery videos/model names from the reference (scope CUT: no fake product)
- Promo/discount strips, signup modal, OAuth (T-018 owns auth UI)
- Mobile pass beyond what already exists (T-019 owns it)

## Report
Write `docs/tasks/T-020/report.md` using `docs/templates/report.md`. Commit all of the
above in ONE commit with a plain message (no attribution trailers), including the
`.agent-logs/` export. Do not mark your own work reviewed.
