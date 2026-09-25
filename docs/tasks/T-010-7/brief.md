# Brief T-010-7: The studio (routes and redirects, rail, stage, composer tab host, sequence draft)

**Role:** implementer · **Suggested model:** medium/strong · **Depends on:** T-010-1 and T-010-5 merged · **Wave:** W2

## Start here (any harness)
1. `scripts/task claim T-010-7 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md` § Web, **`DESIGN.md`** (§4 rail/stage/composer, §6 layout, §7 responsive), and `docs/specs/010-reel-and-still/spec.md` AC-4, AC-6, AC-11 and AC-16.
3. Skim the `design-taste-frontend` skill (`.agents/skills/design-taste-frontend/SKILL.md`).
4. Read `apps/web/src/App.tsx`, `features/library/*`, `features/explore/*`, `api/library.ts`, `api/useJobEvents.ts`, `api/jobStatusWatcher.ts`, `features/session/useSession.ts`, and `ui/AppShell.tsx` (as rebuilt by T-010-5).
5. Questions: `scripts/task say T-010-7 QUESTION "…"`.

## Goal
`/studio` is the single workspace: the rail on the left (the Library), the stage (the selected item or a live job), and the composer below with **Still · Clip · Sequence** tabs. Later tasks plug their composers into the tab host you build. The interfaces below are **fixed contracts** for T-010-8, 9, 10 and 11, so implement them exactly.

## Allowed files (touch nothing else)
- `apps/web/src/App.tsx`
- `apps/web/src/features/studio/*` (new)
- `apps/web/src/api/studioContracts.ts` (new: shared types, no runtime code)
- `apps/web/src/api/jobProgress.ts` (new)
- `apps/web/src/ui/CreditsPopoverContext.tsx` (new)
- `apps/web/src/ui/usePrefersReducedMotion.ts` (new: a copy of the create-video hook; T-010-8 removes the old one)
- `apps/web/src/features/start/StartPage.tsx` (new **stub only**: a heading plus a link to `/studio`; T-010-10 replaces it) and `features/start/groupPresetsByCategory.ts(+.test.ts)` (moved from explore, unchanged)
- **Delete:** `apps/web/src/features/library/*` and `apps/web/src/features/explore/*`. Move `formatCreatedAt.ts(+test)` into `features/studio/`.
- `docs/tasks/T-010-7/report.md`, `docs/verification/T-010-7/*.png`

## Fixed contracts (other tasks code against these)
```ts
// api/studioContracts.ts
export type StudioTab = "still" | "clip" | "sequence"
export type SeedImage = { assetId: string; url: string }
export type SequenceTransition = "cut" | "crossfade" | "fade_black"
export type SequenceDraftClip = { jobId: string; posterUrl: string | null; aspect: number | null; transitionIn: SequenceTransition }
export type SequenceDraft = { clips: SequenceDraftClip[]; audio: { assetId: string; name: string } | null }
export type SequenceDraftControls = {
  draft: SequenceDraft
  addClip: (clip: Omit<SequenceDraftClip, "transitionIn">) => boolean   // false when 6 clips already
  removeClip: (index: number) => void
  moveClip: (from: number, to: number) => void
  setTransition: (index: number, transition: SequenceTransition) => void
  setAudio: (audio: SequenceDraft["audio"]) => void
  clearDraft: () => void
}
export type ComposerProps = { onJobStarted: (jobId: string) => void }
export type ClipComposerProps = ComposerProps & { seedImage: SeedImage | null; onSeedConsumed: () => void }
export type SequenceComposerProps = ComposerProps & { sequence: SequenceDraftControls; libraryItems: LibraryItem[] }
```
- **`ui/CreditsPopoverContext.tsx`:** `CreditsPopoverProvider` and `useCreditsPopover(): { isOpen: boolean; openCredits: () => void; closeCredits: () => void }`. App wraps the routes in the provider. T-010-11 renders the popover from `isOpen`.
- **`api/jobProgress.ts`:** `fetchJobForProgress(kind: "video"|"image"|"sequence", jobId)` returns the `FetchJobResult` shape `useJobEvents` expects, using `GET /jobs/{id}`, `/image-jobs/{id}` or `/sequence-jobs/{id}` according to the kind.

## The change
1. **Routes** (`App.tsx`, inside `AppShell`):

   | Path | Renders |
   |---|---|
   | `/` | `StartPage` |
   | `/studio` | `StudioPage` (full-bleed) |
   | `/v/:jobId` | `SharePage` (unchanged) |

   Redirects:
   - `/create/video` → `/studio?tab=clip`
   - `/create/image` → `/studio?tab=still`
   - `/library` → `/studio`, carrying `?job=` over as `?item=`
   - `/credits` → `/studio?credits=open`

   The redirects keep any other query params.
2. **`features/studio/StudioPage.tsx`:**
   - Reads and writes `?tab=` (default `still`) and `?item=`.
   - Owns `useLibrary(session)` and `useSequenceDraft()`, plus `seedImage` state.
   - Renders the grid layout from DESIGN.md §6 (≥ 1024 two columns; 768–1023 the rail in a drawer opened from a labelled "Library" button; < 768 one column).
   - `?credits=open` calls `openCredits()` once, then removes the param.
3. **Rail** (`StudioRail`, `RailItem`, `groupRailItemsByDay`):
   - Library items grouped under "Today" / "Yesterday" / a date, newest first.
   - Each item has a 56px thumb, a title (the prompt, the preset name, or `Sequence · N shots`), a mono meta line (`clip · 0:05 · 14:02`) and a status dot.
   - Selecting an item sets `?item=`.
   - States: skeleton rows (loading), an error with Retry, and the empty state from spec 010 § UI states.
4. **Stage** (`StudioStage` + small views per kind):
   - **Terminal item:**
     - Video and sequence: `<video controls playsInline poster>`.
     - Still: the images (click one to pick it).
     - A caption: the title plus mono meta. For sequences: `3 shots · 0:14 · ffmpeg`.
     - Backend honesty (AC-11): show `generated_by`, and a muted caption when it's a placeholder or the local fallback.
   - **Non-terminal item:** `useJobEvents(item.id, id => fetchJobForProgress(item.kind, id))` shows the phase with elapsed time and a polite live region. On a terminal status, it calls `reloadLibrary()`.
   - **Actions:**
     - Still: **Animate this** (sets `seedImage` from `images[i]` and `tab=clip`), Download, Share.
     - Clip: **Add to sequence** (calls `addClip`, then shows a toast "Added to sequence (n/6)" or "Sequence is full"), Download, Share.
     - Sequence: Download, Share.
   - Share links to `/v/{id}`.
   - Nothing selected: a quiet empty stage (serif line + sentence).
5. **Composer tab host** (`ComposerTabs.tsx`):
   - Uses `ui/Tabs` with **Still · Clip · Sequence**.
   - For now, mount the **existing** `CreateImagePage` (Still) and `CreateVideoPage` (Clip) as they are, and a small `SequencePlaceholder` ("Sequences arrive in the next build").
   - Leave one clearly marked import line per tab: T-010-8 and T-010-9 swap them for `StillComposer`/`ClipComposer`/`SequenceComposer` with the contract props.
   - `onJobStarted(jobId)` sets `?item=jobId` and reloads the library.
6. **`useSequenceDraft`:** implements `SequenceDraftControls`. The max is 6. `clips[0].transitionIn` is always `"cut"`. The draft persists to `sessionStorage` (wrap access in try/catch).
7. **Tests** (vitest):
   - The redirects (MemoryRouter), including `/library?job=x` → `?item=x`.
   - `useSequenceDraft`: add up to 6 then `false`; move; the first transition is forced to cut; remove; restore from sessionStorage.
   - `groupRailItemsByDay`.
   - `fetchJobForProgress` picks the right path per kind (mock the client).

## Acceptance checks
- [ ] AC-4, AC-6 and the stage parts of AC-11 and AC-16 hold
- [ ] No horizontal page scroll at 390px; the rail drawer has a labelled button; keyboard focus order is rail → stage → composer
- [ ] Features don't import each other's internals (studio imports only `CreateImagePage`/`CreateVideoPage` for now, and later the composer entry components)
- [ ] Every file ≤ 200 lines, one component per file, hooks own the data
- [ ] lint, test, typecheck, build and check-standards pass

## Verify command
```
npm --prefix apps/web run lint && npm --prefix apps/web run test && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && test ! -d apps/web/src/features/library && test ! -d apps/web/src/features/explore
```
Also save screenshots of `/studio` at 390 and 1440px, light and dark, to `docs/verification/T-010-7/`, with seeded Library items if the local API is running.

## Out of scope
- Restyling the Still/Clip composers (T-010-8), the Sequence UI (T-010-9), the start and share pages (T-010-10), the credits popover content (T-010-11).

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-7`
2. `scripts/task submit T-010-7 --as <you> [--transcript <file>]`
