# Tasks 004: Create video page

Rules:
- One task = one agent run.
- No two tasks share a file; the Files lists below are the disjoint split of design.md's **Files** table (checked in T-004-0).
- Every task has a verify command. The full, copy-pasteable command is in each brief.
- Paths are repo-relative. design.md writes them `apps/web/`-relative (`F/` = `apps/web/src/features/create-video/`); this file expands the prefix.
- Task ownership comes straight from design.md's **AC → design → task map** and **Files** table; no other files may be touched.

**Waves:** T-004-1 → (T-004-2 ∥ T-004-4) → T-004-3 → T-004-5.
T-004-3 is gated on T-004-2 because `useActiveJob.ts` consumes the `CreditsControls` type exported by `useCredits.ts` and the `SessionHistory` type exported by `useSessionHistory.ts` (both T-004-2). T-004-4 only needs the T-004-1 types/copy/primitives, so it runs in the same wave as T-004-2.

- [x] **T-004-0** · Design spec 004 (contract check, `design.md`, this file, the five briefs, report)
  - Files: `docs/specs/004-create-video/**`, `docs/tasks/T-004-*/**`
  - Verify: `python3 -c "import json;print('\n'.join(sorted(json.load(open('packages/contracts/openapi.json'))['paths'])))" && ls docs/tasks | grep T-004 && scripts/check-standards`
  - Suggested role: designer (strongest model) · Depends on: T-003-0
- [ ] **T-004-1** · Shared types, copy tables, pure helpers, `ui/` primitives and the vitest runner
  - Files:
    - `apps/web/package.json`, `apps/web/package-lock.json` (add `vitest@^5` devDependency + `"test": "vitest run"`)
    - `apps/web/src/styles.css` (motion-hint + indeterminate-progress keyframes and `--animate-*` tokens)
    - `apps/web/src/ui/buttonStyles.ts`, `apps/web/src/ui/Button.tsx`, `apps/web/src/ui/ButtonLink.tsx`, `apps/web/src/ui/ProgressBar.tsx`, `apps/web/src/ui/Toast.tsx`
    - `apps/web/src/features/create-video/{createVideoTypes,createVideoCopy,canvasPhase,canvasPhase.test,imageFileRules,imageFileRules.test,elapsedTime,elapsedTime.test,presetMotionHints,usePrefersReducedMotion}.ts`
    - `docs/tasks/T-004-1/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-004-0
- [ ] **T-004-2** · Data hooks: guest runner, presets, URL selection, credits, session history, image upload
  - Files:
    - `apps/web/src/features/create-video/{useGuestSessionRunner,usePresets,usePresetSelection,useCredits,sessionHistoryStore,sessionHistoryStore.test,useSessionHistory,putFileWithProgress,useImageUpload}.ts`
    - `docs/tasks/T-004-2/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-004-1
- [ ] **T-004-3** · Job hooks: idempotent create, SSE watcher + poll fallback, events, elapsed, active job
  - Files:
    - `apps/web/src/features/create-video/{useCreateJob,jobStatusWatcher,jobStatusWatcher.test,useJobEvents,useElapsedSeconds,useActiveJob}.ts`
    - `docs/tasks/T-004-3/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run test && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer (orchestrator if available: the SSE watcher) · Depends on: T-004-1, T-004-2
- [ ] **T-004-4** · Panel components: drop zone, thumbnail, preset picker, prompt field, generate section
  - Files:
    - `apps/web/src/features/create-video/useClipboardImagePaste.ts`
    - `apps/web/src/features/create-video/{CreateVideoPanel,ImageDropZone,ImageThumbnail,PresetPicker,PresetCategoryChips,PresetCard,PromptField,GenerateSection}.tsx`
    - `docs/tasks/T-004-4/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-004-1
- [ ] **T-004-5** · Page assembly, canvas views, `App.tsx` routes, session history strip
  - Files:
    - `apps/web/src/features/create-video/{CreateVideoPage,StatusAnnouncer,CreateVideoCanvas,CanvasHeading,HowItWorks,HowItWorksStep,JobProgressView,StatusSteps,ResultView,ResultActions,FailureView,SessionHistoryStrip}.tsx`
    - `apps/web/src/features/create-video/useResultActions.ts`
    - `apps/web/src/App.tsx`
    - `docs/tasks/T-004-5/report.md`
  - Verify: `npm --prefix apps/web run lint && npm --prefix apps/web run typecheck && npm --prefix apps/web run build && scripts/check-standards`
  - Suggested role: implementer · Depends on: T-004-1, T-004-2, T-004-3, T-004-4
