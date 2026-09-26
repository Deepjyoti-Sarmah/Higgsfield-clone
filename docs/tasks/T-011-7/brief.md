# Brief T-011-7: Trim UI, tool links, real showcase on the start page

**Role:** implementer (web) · **Depends on:** T-011-5 and T-011-6 merged, **plus** the orchestrator's showcase list (see step 3) · First read `docs/specs/011-quality-faceswap-trim/agent-rules.md` and `DESIGN.md`.

## Goal
Spec 011 AC-6 (UI) and AC-7.

## Allowed files
- `apps/web/src/features/sequence/*`, `apps/web/src/api/studioContracts.ts` (`SequenceDraftClip` gains `trimStartMs`/`trimEndMs`/`durationMs`), `apps/web/src/features/studio/{draftOps,useSequenceDraft}.ts` (+tests), `apps/web/src/api/sequenceJobs.ts`
- `apps/web/src/ui/AppShell.tsx` (tool links), `apps/web/src/features/start/*`, `apps/web/src/api/webMedia.ts` (showcase list)
- `docs/tasks/T-011-7/*`, `docs/verification/T-011-7/*`

## The change
1. **Trim in the Sequence strip:**
   - Each slot gets an in and out control: two small steppers in 0.5 s steps, mono readout `0:00.5–0:04.0`, keeping at least 1 s. The clip's length comes from the Library's `duration_ms` if present, otherwise 5 s.
   - The trims are sent as `trim_start_ms`/`trim_end_ms`.
   - The total readout uses the trimmed lengths.
   - Use **stable functional updaters** in the draft (learn from T-010-15: no updater may close over a stale draft).
2. **Tool links in the top bar:** `Studio` · `Face swap` (links to `/studio?tab=faceswap`), in the spirit of Pixovid's per-tool entry points, styled per DESIGN.md.
3. **Real showcase:**
   - The orchestrator puts real output URLs (a still, a clip, a face swap, a sequence from the fixed pipeline) in `docs/tasks/T-011-7/showcase.json`.
   - Put them into `webMedia.ts` as `SHOWCASE_*`.
   - The start page's step media use them (replacing the test-pattern and preset-preview stand-ins), and there's a compact 4-item showcase row under the steps. DESIGN.md §5 still applies: no three equal cards; a 2fr/1fr/1fr grid is fine.
   - If `showcase.json` doesn't exist yet, `scripts/task say T-011-7 QUESTION` and do parts 1–2 first.
4. **Tests:** the pure trim maths (clamping, the minimum 1 s, the total length) and the request body with trims.

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build
```
