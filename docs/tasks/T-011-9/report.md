# Report T-011-9

**Agent:** sonnet-5@claude-code · **Role:** implementer (web, visual) · **Result:** DONE

## Files changed
- `apps/web/src/api/webMedia.ts`: added a typed `SHOWCASE` constant (`still`, `clip`, `faceswap`, `sequence`) sourced from `docs/tasks/T-011-7/showcase.json`, each with `url`, `poster` (nullable) and a one-line mono `caption`. Kept the existing `SHOWCASE_STILLS`/`SHOWCASE_MEDIA` constants since `StartStepMedia.tsx` and `PresetChipRow` still touch preset preview helpers.
- `apps/web/src/api/webMedia.test.ts` (new): pure test asserting all four `SHOWCASE` items have a url + caption, and that both video items have a poster fallback.
- `apps/web/src/features/start/StartStepMedia.tsx`: `StillStepMedia`, `ClipStepMedia`, `SequenceStepMedia` now render the real `SHOWCASE.still` / `SHOWCASE.clip` / `SHOWCASE.sequence` assets (muted/looped/`motion-safe`-friendly autoplay video with poster) instead of preset-preview stand-ins or static sample images. `ClipStepMedia` no longer needs a `preset` prop. Each falls back to `null` (renders nothing) on load error via `onError`.
- `apps/web/src/features/start/StartSteps.tsx`: dropped the now-unused `clipPreset` prop/type since `ClipStepMedia` no longer takes a preset.
- `apps/web/src/features/start/ShowcaseRow.tsx` (new): the compact 4-item showcase row (still / clip / face swap / sequence) using DESIGN.md §5's asymmetric-ratio rule: `grid-cols-2` on mobile, `2fr/1fr/1fr/1fr` from `sm:` up (never three/four equal-weighted cards — the still gets visual emphasis). Each cell has a one-line mono caption from `SHOWCASE`, and falls back to its poster (or hides itself if none) on media error.
- `apps/web/src/features/start/StartPage.tsx`: removed the now-unused `clipPreset` derivation, added `<ShowcaseRow />` between the steps/headline grid and the preset-chip row.
- `docs/tasks/T-011-9/*`, `docs/verification/T-011-9/*`: this report + screenshots.

## Reused
- Existing `previewPosterUrl`/`R2_PUBLIC_BASE` helpers were left untouched; the new `SHOWCASE` items carry their own `poster` field directly (the showcase.json already ships explicit `clip_poster`/`sequence_poster` keys, so no derivation needed).
- Kept the existing `StepRow` layout, button styles, and `startCopy` copy structure as-is.

## Verify: see `verify.log`
```
RESULT: PASS
```
Standards check (part of the same verify run):
```
check-standards: ok (0 violations)
```

## Open issues / guesses / things skipped
- The `clip` asset in `showcase.json` (`.../739eab6b.../video.mp4`) visually renders as a still portrait shot with no obvious camera motion in the ~2s sampled in the screenshot — it is real pipeline output (not a colour-bar test pattern), so it satisfies AC-7 literally, but it's worth the orchestrator double-checking that job is actually a "dolly in" render and not a fallback from the T-011-8 live run. Out of scope for this brief (I only consume `showcase.json`, I don't regenerate it).
- Left `SHOWCASE_STILLS` and `SHOWCASE_MEDIA` in `webMedia.ts` in place per the brief ("keep the existing constants if other code still uses them") — `PresetChipRow`/preset preview code still reference them.
- Did not touch `apps/web/src/api/presets.ts` or `PresetChipRow.tsx`; both were outside the allowed-files list and didn't need changes.

## Proposed STATUS.md line
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| Start page shows real showcase media (still/clip/face swap/sequence) from `showcase.json`, not test patterns | `apps/web/src/features/start/ShowcaseRow.tsx`, `apps/web/src/api/webMedia.ts` | `npm --prefix apps/web run lint/test/typecheck/build` (T-011-9) | 2026-09-26 |
