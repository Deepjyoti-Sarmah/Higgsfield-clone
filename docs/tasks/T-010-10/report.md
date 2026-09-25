# Report T-010-10

**Agent:** glm-5.3-flash@freebuff · **Role:** implementer (visual) · **Result:** DONE

## Files changed
- `apps/web/src/features/start/startCopy.ts` (new): headline "Stills that move. Clips that cut together.", one pitch sentence, "Open the studio", step labels/captions, chips heading — §9 voice.
- `apps/web/src/features/start/StartStepMedia.tsx` (new): real media per step — Still: `SHOWCASE_STILLS[0]` (our R2/served FLUX generations); Clip: `usePresets()` `preview_url` looping muted `motion-safe` autoplay video with its poster fallback (poster fallback = another showcase still on error/absence); Sequence: two preset posters joined by an `XFADE` mono chip glyph.
- `apps/web/src/features/start/StartSteps.tsx` (new): the three steps **Still → Clip → Sequence** stacked vertically with mono captions.
- `apps/web/src/features/start/PresetChipRow.tsx` (new): chips grouped by `groupPresetsByCategory`, each linking `/studio?tab=clip&preset=<slug>`; loading shows skeleton pills (`aria-busy`), error hides the row; `presetChipHref` kept file-local for react-refresh.
- `apps/web/src/features/start/StartPage.tsx` (rewritten): asymmetric 5/12+7/12 grid (left headline+pitch+ONE primary CTA; right the step stack), chips below, single column below 768px with media after text, max-width 1200px.
- `apps/web/src/features/start/startSteps.test.tsx` (new, react-dom/server): exactly one `/studio` CTA; chip href `?tab=clip&preset=`; loading skeleton; error renders no chips.
- `apps/web/src/features/share/shareCopy.ts` (rewritten): `documentTitle` → "· Reel & Still"; `shareTitle` (Sequence/Still/preset name); `shareMeta` → `clip · 0:05` / `3 shots · 0:14` / `2 stills`; states restyled in §9 voice; CTA "Make your own" → `/studio`.
- `apps/web/src/features/share/ShareResult.tsx` (rewritten): brand mark → `/`, video for clips+sequences, image grid for stills, title, mono meta, one CTA. Uses `kind`, `image_urls`, `clip_count`, `duration_ms`.
- `apps/web/src/features/share/SharePage.tsx` (edit): document title now built from `shareTitle` ("Still · Reel & Still" etc.).
- `apps/web/src/features/share/shareMeta.test.ts` (new): meta per kind, titles, m:ss formatting.
- `docs/verification/T-010-10/*.png`: start 1440/390 light, start 1440 dark, share not-found state 1440.

## Reused
- `api/presets.ts` (`usePresets`), `api/webMedia.ts` (showcase stills + poster helper), `ui/{ButtonLink,Skeleton,BrandMark,EmptyState}`, `api/share.ts` untouched, `groupPresetsByCategory` from T-010-7 unchanged.

## no-ai-slop Detect mode (on startCopy.ts and shareCopy.ts)
- startCopy: no banned words, no binary contrasts, no throat-clearing, no em dashes, no exclamation marks. "one workspace, one credit ledger" is a concrete double, not puffery. Clean.
- shareCopy: state copy says what happened and what to do next ("This didn't finish." / "Make your own"), no "Oops"/"Something went wrong!". Clean. One fix made during writing: the old file's "Made with Higgsfield" attribution line and "· Higgsfield" title are gone.

## Verify (final run of the brief's exact command)
```
npm --prefix apps/web run lint     → eslint .            (clean)
npm --prefix apps/web run test     → Test Files 19 passed (19), Tests 101 passed (101)
npm --prefix apps/web run typecheck → tsc -b             (clean)
npm --prefix apps/web run build    → ✓ built in 171ms
! grep -rni higgsfield features/{start,share} → GREP_OK
scripts/check-standards            → ok (0 violations)
```
Fixes during the run: react-refresh export rule (presetChipHref made file-local), optional `clip_count`/`duration_ms` typing in `shareMeta`, `formatSeconds` exported from shareCopy for the test.

## Acceptance checks (yes/no + evidence)
- [x] AC-5 — one pitch line, three real-media steps, preset chips, one "Open the studio" → `/studio` (startSteps.test.tsx asserts exactly one CTA).
- [x] AC-18 — share viewer for all three kinds with brand mark, kind-aware title and mono meta, one "Make your own" → `/studio`, no studio/credits UI (ShareResult; shareMeta.test.ts).
- [x] All media from our storage — showcase stills are ours (`api/webMedia.ts`, R2 base or `/showcase/*` served by us), preview clips come from `usePresets()` `preview_url`. No stock/hotlinks added.
- [x] Asymmetric layout, one CTA, no centred hero, no three equal cards — grid-cols-12 with 5/7 split and a vertical stack (StartPage.tsx).
- [x] 390px single column, media after text — `grid-cols-1 lg:grid-cols-12` and stacked steps; screenshot start-390-light.png.
- [x] grep for Higgsfield in start+share returns nothing (GREP_OK above).
- [x] lint, test, typecheck, build, check-standards pass (output above).

## Open issues / guesses / skipped
- No succeeded public job existed to screenshot the ready share viewer; the not-found state is screenshotted instead (`share-404-1440-light.png`). The ready path is covered by shareMeta tests + ShareResult markup.
- Dark screenshots use `--enable-features=WebContentsForceDark` (headless ignores prefers-color-scheme) — same caveat as T-010-7.
- Clip step falls back to a poster still when no preset has a `preview_url`, per the brief's error fallback.
- `preset=` param is produced by the chips but the Clip composer doesn't read it yet (T-010-8's seeding job, out of scope here).

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Start page + share viewer rebuilt for Reel & Still (T-010-10) | `features/start/*`, `features/share/*` | glm-5.3-flash@freebuff (lint+101 tests+tsc+build+grep+check-standards, 4 screenshots) | 2026-09-26 |
