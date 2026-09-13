# Design 004: Create video page

**Spec:** `docs/specs/004-create-video/spec.md` (APPROVED)
**Backend:** `docs/specs/003-generation-core/design.md` (contract, SSE frames, error codes). **No contract change.** Every path below is in `packages/contracts/openapi.json`.
**Web patterns it follows:** `apps/web/src/ui/*`, `api/client.ts` (typed `openapi-fetch`), the session in `features/session/useSession.ts` (delivered through the `AppShell` outlet context), the tokens in `styles.css`, the lint limits in `eslint.config.js`.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Layout | Route + layout, Component tree | T-004-4 (panel), T-004-5 (canvas + page) |
| AC-2 Image input | `useImageUpload`, `ImageDropZone`, Copy § Image, Accessibility | T-004-1 (file rules), T-004-2 (hook), T-004-4 (drop zone + paste) |
| AC-3 Presets + `?preset=` | `usePresets`, `usePresetSelection`, `PresetPicker`, Deep link | T-004-1 (motion hints), T-004-2 (hooks), T-004-4 (picker) |
| AC-4 Generate button | `useCredits`, `GenerateSection`, Copy § Generate | T-004-2 (credits), T-004-3 (create job), T-004-4 (section) |
| AC-5 Zero-friction auth | Auto-guest flow, `useGuestSessionRunner` | T-004-2 (runner), T-004-5 (wiring) |
| AC-6 Progress | `useJobEvents` + `jobStatusWatcher`, `JobProgressView`, state machine | T-004-1 (phase), T-004-3 (hooks), T-004-5 (view) |
| AC-7 Result | `ResultView`, `useResultActions`, Copy § Result | T-004-5 |
| AC-8 Failure | `FailureView`, `useActiveJob.retryFailedJob` | T-004-3 (retry), T-004-5 (view) |
| AC-9 Session memory | `useSessionHistory`, `SessionHistoryStrip` | T-004-2 (hook + store), T-004-5 (strip) |

## API contract used (no changes)
All calls go through `apiClient` (`api/client.ts`) except the two that `openapi-fetch` can't do. Those are noted.

| Method | Path (exact, from openapi.json) | Used by | Success | Errors handled |
|---|---|---|---|---|
| GET | `/api/v1/presets` | `usePresets` | 200 `PresetListResponse` | network / non-200 |
| POST | `/api/v1/auth/guest` | `useSession.startGuestSession` (existing) via `useGuestSessionRunner` | 201 `UserResponse` + cookie | any failure → `false` |
| GET | `/api/v1/credits` | `useCredits` | 200 `CreditsResponse {balance}` | 401, network |
| POST | `/api/v1/uploads` | `useImageUpload` | 201 `UploadCreateResponse` | 401 (guest retry), 422, network |
| PUT | `upload_url` (presigned storage URL, **not our API**) | `putFileWithProgress` (XMLHttpRequest, for upload progress) | 2xx | non-2xx, network, abort |
| POST | `/api/v1/uploads/{asset_id}/complete` | `useImageUpload` | 200 `AssetResponse` | 401, 404, 409 (one retry after 1s), 422 |
| POST | `/api/v1/jobs` | `useCreateJob` | 202 `JobCreatedResponse` | 401 (guest retry), **402 `InsufficientCreditsResponse` (top-level `balance`, `required`)**, 404, 409, 422, network |
| GET | `/api/v1/jobs/{job_id}` | `jobStatusWatcher` (initial load, poll, final read) | 200 `JobResponse` | 401/404 → not found, network → keep polling |
| GET (SSE) | `/api/v1/jobs/{job_id}/events` | `jobStatusWatcher` via native `EventSource` (openapi-fetch can't stream) | `event: status` frames, `data` = `JobStatusEvent` | `error` event → poll fallback + reconnect |
| GET | `video_url` (presigned storage URL, **not our API**) | `useResultActions.downloadVideo` (`fetch` → blob) | 2xx | any failure → open the URL in a new tab |

**SSE facts the client relies on** (from design 003): the first frame is the current status; frames only on change; the server **closes the stream after `succeeded`/`failed`**, and native `EventSource` would then reconnect, so the client must `close()` on a terminal frame. A `running → queued` frame (reaper re-queue) is valid. `retry: 3000` sets the browser's own reconnect delay. Cookies go along automatically (same origin), so no `withCredentials`.

**Types** come from `api/generated/schema.d.ts` only, re-exported once in `createVideoTypes.ts`:
`Preset = components["schemas"]["PresetResponse"]`, `PresetCategory = Preset["category"]`, `Asset = components["schemas"]["AssetResponse"]`, `Job = components["schemas"]["JobResponse"]`, `JobStatus = Job["status"]`, `JobStatusEvent`, `InsufficientCredits = components["schemas"]["InsufficientCreditsResponse"]`.

## Route + layout
- **Route:** `/create/video` → `CreateVideoPage` (replaces the `Placeholder` in `App.tsx`). Query: `?preset=<slug>`.
- **Also:** `/v/:jobId` → `EmptyState` placeholder ("Share page" / "Public share pages are coming soon.") so the Share link isn't a blank page before spec 007. The FastAPI share page will take over that path later.
- `document.title` = `Create video · Higgsfield` while mounted (reset to `Higgsfield` on unmount).

**Page container** (inside `AppShell`'s `<main>`): `mx-auto grid w-full max-w-[1400px] gap-6`.

| Width | Layout |
|---|---|
| `< 768px` (default) | One column, in order: **panel**, **canvas**, **history strip**. The panel is its natural height; its Generate footer is `sticky bottom-0` so it stays visible while the panel scrolls past. After a successful submit, the canvas scrolls into view (`scrollIntoView({ block: "start", behavior: "smooth" })`, `"auto"` under reduced motion). Preset grid: 3 columns. |
| `≥ 768px` (`md:`) | `md:grid-cols-[360px_minmax(0,1fr)]`, items `md:items-start`. **Panel** (left): `md:sticky md:top-20 md:max-h-[calc(100dvh-7rem)] md:overflow-y-auto`, with the Generate footer `sticky bottom-0` inside it. **Right column:** canvas above, history strip below. Preset grid: 3 columns. |
| `≥ 1280px` (`xl:`) | `xl:grid-cols-[420px_minmax(0,1fr)]`. Preset grid: 3 columns (cards get wider). |

**Surfaces** (only existing tokens: `bg`, `surface`, `border`, `text`, `muted`, `accent`, `accent-ink`, fonts `display`/`body`):
- Panel: `rounded-2xl border border-border bg-surface`, sections `p-4` separated by `border-t border-border`. Section labels: `text-xs font-semibold uppercase tracking-wide text-muted`.
- Canvas: `rounded-2xl border border-border bg-surface min-h-[420px] md:min-h-[560px]`, content centred, `p-6`.
- Selected/active: `border-accent`, and an accent check badge on the preset card. Focus: `outline-2 outline-offset-2 outline-accent` on `:focus-visible`.
- Errors: `text-red-400` (already used by `GuestButton`). Success/"Done" pill: `bg-accent text-accent-ink`.
- Headings use the display font (global `h1,h2,h3` rule). The page `<h1>` "Create video" sits at the top of the panel (`text-xl`).

## Component tree
Every file lives in `apps/web/src/features/create-video/` unless it's in `ui/`. **Components only render and call props. Hooks own data.** Every component and hook body must stay ≤ 40 lines (`max-lines-per-function`) with complexity ≤ 8, so the tree is deliberately fine-grained.

```
CreateVideoPage                          (T-004-5) wires hooks → props; no markup logic beyond the grid
├─ StatusAnnouncer                       (T-004-5) visually hidden aria-live region
├─ CreateVideoPanel                      (T-004-4)
│  ├─ ImageDropZone                      (T-004-4)  uses useClipboardImagePaste, ui/ProgressBar, ui/Button
│  │  └─ ImageThumbnail                  (T-004-4)  thumbnail + Replace/Remove, uses ui/Button
│  ├─ PresetPicker                       (T-004-4)  fieldset + legend + description line
│  │  ├─ PresetCategoryChips             (T-004-4)
│  │  └─ PresetCard ×n                   (T-004-4)  uses presetMotionHints
│  ├─ PromptField                        (T-004-4)
│  └─ GenerateSection                    (T-004-4)  uses ui/Button, ui/ButtonLink
├─ CreateVideoCanvas                     (T-004-5)  switch on CanvasPhase
│  ├─ HowItWorks                         (T-004-5)  phases empty | uploading | ready
│  │  └─ HowItWorksStep ×3               (T-004-5)
│  ├─ JobProgressView                    (T-004-5)  phases submitting | queued | generating; uses ui/ProgressBar
│  │  └─ StatusSteps                     (T-004-5)  Queued → Generating → Done pills
│  ├─ ResultView                         (T-004-5)  phase succeeded
│  │  └─ ResultActions                   (T-004-5)  uses useResultActions, ui/Button, buttonClasses
│  ├─ FailureView                        (T-004-5)  phase failed (and job not found)
│  └─ (all four render inside) CanvasHeading (T-004-5) the stable, focusable h2
├─ SessionHistoryStrip                   (T-004-5)
└─ ui/Toast                              (T-004-1)  network errors (presets load, job submit)
```

### Props (exact; types from `createVideoTypes.ts`)
| Component | File | Props | Uses |
|---|---|---|---|
| `CreateVideoPage` | `CreateVideoPage.tsx` | — (reads `useOutletContext<SessionContextValue>()`, `useSearchParams` via `usePresetSelection`) | all hooks |
| `StatusAnnouncer` | `StatusAnnouncer.tsx` | `message: string` | — |
| `CreateVideoPanel` | `CreateVideoPanel.tsx` | `upload: ImageUploadControls`, `presets: PresetsState`, `selection: PresetSelection`, `prompt: string`, `onPromptChange(value: string)`, `generate: GenerateSectionProps` | children below; owns the "focus after upload" effect (Accessibility) |
| `ImageDropZone` | `ImageDropZone.tsx` | `upload: ImageUploadControls` | `useClipboardImagePaste(upload.selectImage)`, `ImageThumbnail`, `ui/ProgressBar`, `ui/Button`, `imageFileRules.ACCEPTED_IMAGE_TYPES` (for `accept`) |
| `ImageThumbnail` | `ImageThumbnail.tsx` | `previewUrl: string`, `progress: number \| null` (null = not uploading), `onReplace()`, `onRemove()` | `ui/ProgressBar`, `ui/Button` |
| `PresetPicker` | `PresetPicker.tsx` | `presets: PresetsState`, `selection: PresetSelection`, `previewImageUrl: string \| null`, `groupRef: RefObject<HTMLFieldSetElement \| null>` | `PresetCategoryChips`, `PresetCard` |
| `PresetCategoryChips` | `PresetCategoryChips.tsx` | `value: PresetCategoryFilter`, `onChange(value: PresetCategoryFilter)` | — |
| `PresetCard` | `PresetCard.tsx` | `preset: Preset`, `isSelected: boolean`, `previewImageUrl: string \| null`, `onSelect(slug: string)` | `presetMotionClass(slug)` |
| `PromptField` | `PromptField.tsx` | `value: string`, `onChange(value: string)` | — |
| `GenerateSection` | `GenerateSection.tsx` | `GenerateSectionProps` = `{ selectedPreset: Preset \| null, blockedReason: GenerateBlockedReason \| null, isSubmitting: boolean, balance: BalanceView, insufficient: InsufficientCredits \| null, submitError: SubmitErrorKind \| null, onGenerate() }` | `ui/Button`, `ui/ButtonLink` |
| `CreateVideoCanvas` | `CreateVideoCanvas.tsx` | `phase: CanvasPhase`, `canvas: CanvasView`, `headingRef: RefObject<HTMLHeadingElement \| null>`, `onMakeAnother()`, `onRetry()`, `onDismissMissing()` | the views below |
| `CanvasHeading` | `CanvasHeading.tsx` | `text: string`, `headingRef` | — |
| `HowItWorks` | `HowItWorks.tsx` | `phase: "empty" \| "uploading" \| "ready"`, `hasPreset: boolean`, `presetCount: number` | `HowItWorksStep` |
| `HowItWorksStep` | `HowItWorksStep.tsx` | `index: 1 \| 2 \| 3`, `title: string`, `body: string`, `state: "todo" \| "current" \| "busy" \| "done"`, `illustration: "image" \| "preset" \| "video"` | `presetMotionClass` for the animated illustration |
| `JobProgressView` | `JobProgressView.tsx` | `phase: "submitting" \| "queued" \| "generating"`, `inputImageUrl: string \| null`, `presetName: string`, `elapsedSeconds: number`, `wasRequeued: boolean`, `headingRef` | `CanvasHeading`, `StatusSteps`, `ui/ProgressBar` (indeterminate), `elapsedTime.formatElapsed` |
| `StatusSteps` | `StatusSteps.tsx` | `current: "queued" \| "generating" \| "done"` | — |
| `ResultView` | `ResultView.tsx` | `job: Job`, `elapsedSeconds: number`, `headingRef`, `onMakeAnother()` | `CanvasHeading`, `ResultActions`, `usePrefersReducedMotion` |
| `ResultActions` | `ResultActions.tsx` | `job: Job`, `onMakeAnother()` | `useResultActions(job)`, `ui/Button`, `ui/buttonClasses` |
| `FailureView` | `FailureView.tsx` | `variant: "failed" \| "missing"`, `job: Job \| null`, `headingRef`, `onRetry()`, `onMakeAnother()`, `onDismissMissing()` | `CanvasHeading`, `ui/Button` |
| `SessionHistoryStrip` | `SessionHistoryStrip.tsx` | `entries: HistoryEntry[]`, `activeJobId: string \| null`, `onOpen(jobId: string)` | — |
| `Toast` | `ui/Toast.tsx` | `message: string`, `actionLabel?: string`, `onAction?()`, `onDismiss()` | `ui/Button` |
| `ProgressBar` | `ui/ProgressBar.tsx` | `value: number \| null` (0..1; null = indeterminate), `label: string` | — |
| `ButtonLink` | `ui/ButtonLink.tsx` | `to: string`, `variant?: ButtonVariant`, `children`, `className?` | `buttonClasses`, react-router `Link` |

### New shared primitives (`ui/`) and why they qualify (rule of two)
- **`ui/buttonStyles.ts` → `buttonClasses(variant)`**: the button look is needed by `<button>` (`Button`), router links (`ButtonLink`: "Get credits") and a plain `<a>` (Share). Three users → one source of classes. Adds the focus-visible outline to all buttons.
- **`ui/ButtonLink.tsx`**: "Get credits" and "Back to create"-style navigation. A link must be `<a>`, and nesting `<button>` in `<Link>` is the bug T-002-7 fixed.
- **`ui/ProgressBar.tsx`**: upload progress (determinate) and the generating bar (indeterminate). Two users.
- **`ui/Toast.tsx`**: "Couldn't load presets." and "Couldn't reach the server." Two users. Other specs (005/008) will reuse it.
- **Not extracted** (one user each for now): the drop zone (`ImageDropZone`), the video player (`ResultView`), the category chips. Specs 005/007 move the player to `ui/` when they need it.

## Shared types (`createVideoTypes.ts`, T-004-1; everyone imports, nobody else edits)
```ts
export type PresetCategoryFilter = "all" | PresetCategory
export type PresetsState = { status: "loading" | "ready" | "error"; presets: Preset[]; reloadPresets: () => void }
export type PresetSelection = {
  selectedSlug: string | null; selectedPreset: Preset | null; isUnknownSlug: boolean
  categoryFilter: PresetCategoryFilter; setCategoryFilter: (v: PresetCategoryFilter) => void
  selectPreset: (slug: string) => void; clearPreset: () => void
}
export type UploadErrorKind = "invalid-file" | "network" | "session" | "not-finished"
export type UploadState =
  | { status: "idle" }
  | { status: "uploading"; file: File; previewUrl: string; progress: number }
  | { status: "ready"; file: File; previewUrl: string; asset: Asset }
  | { status: "error"; file: File; previewUrl: string; errorKind: Exclude<UploadErrorKind, "invalid-file"> }
export type ImageUploadControls = {
  state: UploadState; rejection: "invalid-file" | null
  selectImage: (file: File) => void; clearImage: () => void; retryUpload: () => void
}
export type JobDraft = { presetSlug: string; presetName: string; inputAssetId: string; prompt: string | null }
export type SubmitErrorKind = "network" | "input-missing" | "input-not-ready" | "session" | "invalid"
export type SubmitState =
  | { status: "idle" }
  | { status: "submitting"; draft: JobDraft }
  | { status: "accepted"; jobId: string }
  | { status: "insufficient-credits"; insufficient: InsufficientCredits }
  | { status: "error"; errorKind: SubmitErrorKind; draft: JobDraft }
export type BalanceView =
  | { status: "guest-offer" } | { status: "loading" } | { status: "error" } | { status: "known"; balance: number }
export type GenerateBlockedReason = "no-image-no-preset" | "no-image" | "no-preset" | "uploading"
export type CanvasPhase = "empty" | "uploading" | "ready" | "submitting" | "queued" | "generating" | "succeeded" | "failed"
export type JobWatch = {
  job: Job | null; status: JobStatus | null; connection: "idle" | "live" | "polling"
  isMissing: boolean; wasRequeued: boolean
}
export type CanvasView = {
  presetCount: number; hasPreset: boolean; job: Job | null; isMissing: boolean
  inputImageUrl: string | null; presetName: string; elapsedSeconds: number; wasRequeued: boolean
}
export type HistoryEntry = { jobId: string; presetName: string; status: JobStatus; thumbnailUrl: string | null; createdAt: string }
export type GuestSessionOutcome<T> = { outcome: "done"; result: T } | { outcome: "session-failed" }
export type RunWithGuestSession = <T extends { response: Response }>(request: () => Promise<T>) => Promise<GuestSessionOutcome<T>>
```

## Hooks
All hooks live in `features/create-video/`. Network calls are wrapped in `try/catch`, because `openapi-fetch` throws on network failure. A thrown error or a 5xx counts as `network`. No hook ever shows raw server text except `Job.error_message`, which is user-safe by contract.

### `useGuestSessionRunner(session: SessionContextValue): RunWithGuestSession` (T-004-2)
Makes AC-5 a property of every authenticated call instead of a dialog.
1. It keeps `session.status` in a ref, so a stale closure never re-creates a guest.
2. If the status is `"signed-out"`, it runs `ensureGuest()` first. If that returns `false`, the result is `{ outcome: "session-failed" }`.
3. It runs `request()`. If `response.status !== 401`, the result is `{ outcome: "done", result }`.
4. On a 401 (the status was still `"loading"`, or the cookie expired), it runs `ensureGuest()` once and then `request()` once more. A failed `ensureGuest()` gives `session-failed`. A second 401 is returned as `done` for the caller to map.
5. **`ensureGuest()`** shares one in-flight promise (a ref), so an image drop and a Generate press arriving together create **one** guest. It calls `session.startGuestSession()` (existing, `POST /api/v1/auth/guest`), which also updates the header badge because it's the same outlet-context state.
- **Errors:** a network failure inside `startGuestSession` already resolves `false` (existing code), so it becomes `session-failed`. Throws from `request()` propagate to the caller's `try/catch`.
- The page calls this hook **once** and passes the function to `useImageUpload` and `useCreateJob`. **Never call `useSession()` in this feature**: that would make a second, disconnected session state.

### `usePresets(): PresetsState` (T-004-2)
- **Input:** none. **Path:** `GET /api/v1/presets` (no auth), on mount and on `reloadPresets()`.
- **Output:** `{ status, presets, reloadPresets }`. Presets are kept in server order (`sort_order`).
- **Errors:**
  - Throw or non-200 → `status: "error"`, and the previous `presets` are kept. The page shows the toast "Couldn't load presets." with the action **Retry** (`reloadPresets`).
  - 200 with an empty array → `status: "ready"`, `presets: []`, and the picker shows "No presets available right now."
- A reload sets `status: "loading"` only if there are no presets yet, so the grid doesn't flash.

### `usePresetSelection(presets: PresetsState): PresetSelection` (T-004-2)
The URL is the single source of truth for the selection (see Deep link).
- `selectedSlug` = `searchParams.get("preset")`.
- `selectedPreset` = the preset with that slug, or `null`.
- `isUnknownSlug` = `presets.status === "ready" && selectedSlug !== null && selectedPreset === null`.
- `selectPreset(slug)` → `setSearchParams(p => { p.set("preset", slug); return p }, { replace: true })`.
- `clearPreset()` deletes the param (also `replace`).
- `categoryFilter` is local state, default `"all"`. A deep-linked slug always shows, because the default is `"all"`.
- **Errors:** none (pure state).

### `useCredits(isSignedIn: boolean): CreditsControls` (T-004-2)
`CreditsControls = { balanceView: BalanceView; balance: number | null; refreshCredits: () => Promise<void>; applyKnownBalance: (balance: number) => void }`
- **Path:** `GET /api/v1/credits`, called when `isSignedIn` becomes true and on `refreshCredits()`.
- **Output mapping:**
  - not signed in → `{ status: "guest-offer" }`
  - first load in flight → `loading`
  - 200 → `known`
  - A refresh keeps the last `known` value visible (no flash back to `loading`).
- **Errors:**
  - 401 → `guest-offer`, `balance: null` (session gone; the next authenticated call re-creates a guest).
  - Throw or other status → `{ status: "error" }` and `balance: null`. Generate stays enabled, because the server enforces the balance with a 402.
- `applyKnownBalance(n)` sets `known` straight from a 402 body, with no extra request.
- **When the page refreshes:** after a 202, and when a watched job reaches `succeeded` or `failed` (a failure refunds).

### `useImageUpload(runWithGuestSession: RunWithGuestSession): ImageUploadControls` (T-004-2)
The sequence for `selectImage(file)`:
1. **`checkImageFile(file)`** (`imageFileRules.ts`): the type must be `image/jpeg`, `image/png` or `image/webp`, and `0 < file.size ≤ 10 485 760`.
   - If it fails, set `rejection = "invalid-file"` and stop. The **current state is kept** (a valid ready image survives a bad replacement).
   - Any later `selectImage` or `clearImage` resets `rejection` to `null`.
2. Abort the in-flight upload (`AbortController`) and revoke the previous object URL.
3. `previewUrl = URL.createObjectURL(file)`, then state `uploading` with `progress: 0`.
4. `runWithGuestSession(() => apiClient.POST("/api/v1/uploads", { body: { content_type: file.type, byte_size: file.size } }))`.
   - `session-failed` → `error/session`.
   - 201 → go on.
   - 422 → `rejection = "invalid-file"`, and the state goes back to what it was before step 2. If there was no ready image, it goes to `idle`.
   - Throw, 401 or other → `error/network`.
5. **`putFileWithProgress({ url: upload_url, file, headers: upload_headers, signal, onProgress })`** (`putFileWithProgress.ts`):
   - `XMLHttpRequest` `PUT`, sending **exactly** `upload_headers` (the signature covers `Content-Type`), `withCredentials = false`.
   - `upload.onprogress` → `progress = loaded / total`.
   - It resolves on 2xx. It rejects `UploadHttpError` on non-2xx or `onerror`, and `AbortError` on abort.
   - Abort → return silently (a newer selection owns the state).
   - Any other rejection → `error/network`.
6. `apiClient.POST("/api/v1/uploads/{asset_id}/complete", { params: { path: { asset_id } } })`:
   - 200 → state `ready` with `asset`.
   - 409 → wait 1000 ms and retry once. A second 409 → `error/not-finished`.
   - 422 → `rejection = "invalid-file"` and state `idle`. The server deleted the object; the preview is revoked.
   - Throw, 401, 404 or other → `error/network`.
- `retryUpload()` re-runs steps 2–6 with the file from the `error` state (a new asset).
- `clearImage()`: abort, revoke, `idle`.
- **Unmount:** abort and revoke.
- **Output:** `ImageUploadControls` (types above). The hook never moves focus (see Accessibility).

### `useCreateJob(runWithGuestSession, callbacks): CreateJobControls` (T-004-3)
`callbacks = { onAccepted(jobId: string, draft: JobDraft): void; onInsufficient(insufficient: InsufficientCredits): void }`.
`CreateJobControls = { state: SubmitState; submitJob(draft: JobDraft): void; retrySubmit(): void; resetSubmit(): void }`.
- **Idempotency:** `submitJob` makes `idempotencyKey = crypto.randomUUID()` (36 chars, inside 8..100) and keeps it in a ref with the draft.
  - `retrySubmit()` (the toast's Retry after a network error) re-sends the **same draft with the same key**, so a request that did reach the server can't charge twice.
  - Any new `submitJob` call makes a new key.
- **Guard:** calls while `submitting` are ignored (double-click).
- **Path:** `runWithGuestSession(() => apiClient.POST("/api/v1/jobs", { body: { preset_slug, input_asset_id, prompt, idempotency_key } }))`. `prompt` is trimmed; an empty prompt is sent as `null`.
- **Results:**
  | Response | State | Side effect |
  |---|---|---|
  | 202 | `accepted { jobId }` | `onAccepted(data.id, draft)` |
  | 402 | `insufficient-credits { insufficient: error }` | `onInsufficient(error)` (the body is top-level `{detail, balance, required}`) |
  | 404 | `error/input-missing` | — |
  | 409 | `error/input-not-ready` | — |
  | 422 | `error/invalid` | — |
  | `session-failed` or a second 401 | `error/session` | — |
  | throw or 5xx | `error/network` | the page shows the toast with Retry → `retrySubmit` |
- `resetSubmit()` → `idle`. It's called by "Make another", by a new image, and when the preset changes after a 402.

### `useJobEvents(jobId: string | null): JobWatch` (T-004-3)
A thin React wrapper around **`createJobStatusWatcher`** (`jobStatusWatcher.ts`, framework-free so it's unit-tested with a fake `EventSource` and fake timers).
- On a `jobId` change or unmount: `watcher.stop()`, and the state resets to `{ job: null, status: null, connection: "idle", isMissing: false, wasRequeued: false }`.
- `wasRequeued` becomes `true` when the status goes `running → queued`, and resets when it reaches `running` again.

```ts
type EventSourceLike = { readyState: number; close(): void; addEventListener(type: "open" | "error" | "status", fn: (e: MessageEvent | Event) => void): void }
type FetchJobResult = { kind: "ok"; job: Job } | { kind: "missing" } | { kind: "network" }
type WatcherDeps = { openEventSource(url: string): EventSourceLike; fetchJob(jobId: string): Promise<FetchJobResult>; timers?: Pick<typeof globalThis, "setTimeout" | "clearTimeout" | "setInterval" | "clearInterval"> }
type WatcherCallbacks = { onJob(job: Job): void; onStatus(status: JobStatus): void; onConnection(c: "live" | "polling"): void; onMissing(): void }
export function createJobStatusWatcher(jobId: string, deps: WatcherDeps, callbacks: WatcherCallbacks): { stop(): void }
export const POLL_INTERVAL_MS = 5000
export const RECONNECT_DELAYS_MS = [3000, 6000, 12000, 24000, 30000]
```
**Behaviour** (each rule is a unit test in `jobStatusWatcher.test.ts`):
1. **Start:**
   - Call `fetchJob(jobId)` once, for `preset_name`, `input_image_url` and `created_at`. A history reopen needs these too.
   - In parallel, open `openEventSource("/api/v1/jobs/" + jobId + "/events")`.
   - If the initial fetch returns a terminal job, deliver it and stop. That closes the SSE too.
2. **`status` event:** `JSON.parse(e.data)`. Ignore it if parsing fails or `job_id !== jobId`. Otherwise:
   - `onStatus(status)`.
   - If polling, stop the poll and `onConnection("live")`.
   - If the status is terminal: `close()` the EventSource **before** the server closes it, stop all timers, then run `fetchJob` for the final URLs and `error_message`. A `network` result retries every 5000 ms, up to 3 tries.
3. **`open` event:** `onConnection("live")`, stop polling, reset the reconnect attempt counter.
4. **`error` event:**
   - If not polling yet, start polling: `fetchJob` now, then every `POLL_INTERVAL_MS`, and `onConnection("polling")`.
   - If `readyState === 2` (CLOSED: an HTTP error or a server close before terminal), close it and schedule a new EventSource after `RECONNECT_DELAYS_MS[min(attempt, 4)]`.
   - If `readyState === 0` (CONNECTING), the browser is already retrying, so do nothing more.
5. **Poll result:**
   - `ok`: `onJob(job)`.
   - A terminal `job.status`: `onStatus` and stop everything.
   - A non-terminal status is passed to `onStatus` **only while not live**, so a late poll can't overwrite a newer SSE frame.
   - `missing` (401/404): `onMissing()` and stop everything.
   - `network`: keep polling.
6. **`stop()`** is idempotent: close the EventSource, clear every timer, and ignore any callback that arrives later (a `stopped` flag).
- **`fetchJob` in the hook:** `apiClient.GET("/api/v1/jobs/{job_id}", { params: { path: { job_id } } })`. 200 → `ok`; 401/404 → `missing`; anything else or a throw → `network`.
- **`openEventSource`** = `url => new EventSource(url)`.

### `useElapsedSeconds(startIso: string | null, endIso: string | null): number` (T-004-3)
- `start = Date.parse(startIso)`. The result is `Math.max(0, floor(((endIso ? Date.parse(endIso) : Date.now()) - start) / 1000))`.
- It re-renders every 1000 ms only while `startIso` is set and `endIso` is null.
- `null` start → `0`.
- **Clock skew:** the start is the server's `created_at`, and a negative result clamps to 0. Before the job loads, the page passes the submit time (`submittedAtIso`, stored by `useActiveJob`).
- Formatting is `elapsedTime.formatElapsed(seconds)` → `"0:07"`, `"1:42"`, `"12:05"` (T-004-1).

### `useSessionHistory(): SessionHistory` (T-004-2)
`SessionHistory = { entries: HistoryEntry[]; recordJob(entry: HistoryEntry): void; updateJob(jobId: string, patch: Partial<Pick<HistoryEntry, "status" | "thumbnailUrl">>): void; removeJob(jobId: string): void }`
- **Storage:**
  - `window.sessionStorage`, key **`hf.createVideo.history.v1`**, value `JSON.stringify(HistoryEntry[])`, newest first.
  - Pure functions live in `sessionHistoryStore.ts`: `readHistory(storage)`, `writeHistory(storage, entries)`, `upsertHistoryEntry(entries, entry)`.
  - `upsertHistoryEntry` removes any entry with the same `jobId`, puts the new one first and **caps the list at `MAX_HISTORY_ENTRIES = 6`**.
- **Errors:**
  - Invalid JSON, a non-array, or an entry missing string `jobId`/`presetName`/`createdAt` or a valid `status` → those entries are dropped, and invalid JSON reads as `[]`.
  - A `setItem`/`getItem` throw (private mode, quota) → the hook keeps working in memory only, with no UI error.
- **Updates:**
  - `thumbnailUrl` is `job.poster_url ?? job.input_image_url`, updated whenever the watched job changes.
  - Presigned URLs expire after 1h, so the strip handles `<img onError>` with a fallback tile, and reopening always re-fetches the job.

### `useActiveJob(deps): ActiveJob` (T-004-3)
The page-level controller for "which job the canvas shows". It keeps `CreateVideoPage` under 40 lines.
- **`deps`:** `{ createJob: CreateJobControls; history: SessionHistory; credits: CreditsControls; upload: ImageUploadControls; selection: PresetSelection }`.
- **Returns:** `{ activeJobId: string | null; submittedAtIso: string | null; watch: JobWatch; startJob(draft: JobDraft): void; openHistoryEntry(jobId: string): void; makeAnother(): void; retryFailedJob(): void; dismissMissing(): void }`.
- **The `onAccepted` handler:** the page builds `useCreateJob` with callbacks that call into this hook. To avoid a hook cycle, `useActiveJob` exposes **`handleJobAccepted(jobId, draft)`** and **`handleInsufficient(insufficient)`**, and the page passes those two into `useCreateJob`. `createJob` is then passed to `useActiveJob` through a ref setter. The T-004-3 implementer may instead fold `useCreateJob` inside `useActiveJob`, as long as the returned shapes above stay the same.
- **`handleJobAccepted`:** set `activeJobId`, `history.recordJob({ jobId, presetName: draft.presetName, status: "queued", thumbnailUrl: null, createdAt: now })`, then `credits.refreshCredits()`.
- **`startJob(draft)`:** set `activeJobId = null` and `submittedAtIso = now`, then `createJob.submitJob(draft)`.
- **Effect on `watch.job`:** `history.updateJob(job.id, { status, thumbnailUrl })`. On the first terminal status for that job id, `credits.refreshCredits()`.
- **Effect on `watch.isMissing`:** `history.removeJob(activeJobId)`.
- **`openHistoryEntry(jobId)`:** set `activeJobId = jobId`, `submittedAtIso = null`, and `createJob.resetSubmit()`.
- **`makeAnother()`:** set `activeJobId = null`, `selection.clearPreset()`, `createJob.resetSubmit()`. The image stays, and so does the prompt.
- **`retryFailedJob()`:**
  - With `watch.job` failed, run `startJob({ presetSlug: job.preset_slug, presetName: job.preset_name, inputAssetId: job.input_asset_id, prompt: job.prompt })`.
  - A new key is made. This works for history-reopened jobs too.
  - A 402 shows "Get credits" in the panel.
- **`dismissMissing()`:** set `activeJobId = null`.

## State machine for the canvas (`canvasPhase.ts`, T-004-1)
The phase is **derived, never stored**, so it can't drift from the hooks:
```ts
export function deriveCanvasPhase(input: { uploadStatus: UploadState["status"]; submitStatus: SubmitState["status"]; activeJobId: string | null; jobStatus: JobStatus | null; isJobMissing: boolean }): CanvasPhase
```
**Priority** (first match wins):
1. `activeJobId !== null`:
   - `isJobMissing` → `failed`. `FailureView` shows the `missing` variant.
   - Otherwise map `jobStatus`: `succeeded` → `succeeded`, `failed` → `failed`, `running` → `generating`, `queued` or `null` → `queued`.
2. `submitStatus === "submitting"` → `submitting`.
3. `uploadStatus === "uploading"` → `uploading`. `"ready"` → `ready`. `"idle"` or `"error"` → `empty`.

**Allowed transitions** (exported as `CANVAS_TRANSITIONS: Record<CanvasPhase, CanvasPhase[]>`; `canvasPhase.test.ts` walks every user journey below through `deriveCanvasPhase` and asserts each step is allowed):

| From | To | Trigger |
|---|---|---|
| `empty` | `uploading` | an image is selected (drop, browse, paste) |
| `empty` | `queued`, `generating`, `succeeded`, `failed` | a history entry is opened |
| `uploading` | `ready` | complete → 200 |
| `uploading` | `empty` | upload error, or Remove |
| `uploading` | `uploading` | Replace mid-upload |
| `ready` | `uploading` | Replace |
| `ready` | `empty` | Remove |
| `ready` | `submitting` | Generate |
| `ready` | `queued`, `generating`, `succeeded`, `failed` | a history entry is opened |
| `submitting` | `queued` | 202 |
| `submitting` | `ready` | 402, 404, 409, 422, session or network error (the image is still ready) |
| `submitting` | `empty` | the image was removed while submitting |
| `queued` | `generating`, `succeeded`, `failed` | SSE/poll (`succeeded` directly when a fast job's frames were missed) |
| `queued` | `submitting` | Generate pressed again (a new job; the old one stays in history) |
| `generating` | `succeeded`, `failed` | SSE/poll |
| `generating` | `queued` | reaper re-queue |
| `generating` | `submitting` | Generate pressed again |
| `succeeded` | `ready` | Make another (image still ready) |
| `succeeded` | `empty` | Make another after the image was removed |
| `succeeded` | `submitting` | Generate (same or new inputs) |
| `failed` | `submitting` | Retry, or Generate |
| `failed` | `ready`, `empty` | Make another, or "Back to create" (missing) |
| `queued`, `generating`, `succeeded`, `failed` | `queued`, `generating`, `succeeded`, `failed` | another history entry is opened |

**Panel behaviour per phase:**
- The panel stays usable in every phase. Generate is disabled only by `blockedReason` or `isSubmitting`.
- **Generate while a job is running** starts a second job. That's allowed: the backend handles parallel jobs, the label shows the cost, and the first job stays in the strip.

**`blockedReason`** (computed in the page from upload state and selection, first match):
1. no ready image and no preset → `no-image-no-preset`
2. uploading → `uploading`
3. no ready image → `no-image`
4. no preset → `no-preset`
5. otherwise `null`

**`insufficient`** shows (the button becomes the "Get credits" link) when **either** the submit state is `insufficient-credits` **or** `balance !== null && selectedPreset && balance < selectedPreset.credit_cost` (pre-check, no request). The pre-check builds `{ detail: "", balance, required: cost }`.

## Every UI state with exact copy (`createVideoCopy.ts`, T-004-1)
All user-visible strings live in `createVideoCopy.ts` (a `const` object plus small template functions), so a reviewer diffs one file against this table. The `—` is an em dash (U+2014), `·` is U+00B7, `…` is U+2026, and quotes are typographic where shown.

### Page + panel
| State | Element | Copy |
|---|---|---|
| always | panel `<h1>` | `Create video` |
| always | section labels | `Image` · `Preset` · `Prompt` |
| always | `document.title` | `Create video · Higgsfield` |

### Image (AC-2)
| State | Element | Copy |
|---|---|---|
| idle | title | `Add an image` |
| idle | body | `Drop it here, browse, or paste from your clipboard.` |
| idle | button | `Browse files` |
| idle, invalid-file | hint (always visible) / inline error | `PNG, JPG or WebP up to 10 MB` (hint in `text-muted`; when `rejection === "invalid-file"` the same text turns `text-red-400` with `role="alert"`) |
| dragging over | title | `Drop to upload` |
| uploading | thumbnail overlay + progress label | `Uploading… {pct}%` (`pct` = `Math.round(progress * 100)`) |
| ready | buttons | `Replace` · icon button with `aria-label` `Remove image` |
| ready | `<img alt>` | `Your image` |
| error/network | inline error + button | `Upload failed. Check your connection and try again.` · `Try again` |
| error/session | inline error + button | `Couldn't start a session. Try again.` · `Try again` |
| error/not-finished | inline error + button | `Upload didn't finish. Try again.` · `Try again` |

### Preset (AC-3)
| State | Element | Copy |
|---|---|---|
| always | category chips | `All` · `Camera` · `Cinematic` · `Dynamic` |
| always | chips group `aria-label` | `Preset categories` |
| loading | 6 skeleton cards + visually hidden text | `Loading presets…` |
| ready, empty list | text | `No presets available right now.` |
| ready, filter has none | text | `No presets in this category.` |
| error | inline text + toast | inline `Presets didn't load.`; toast `Couldn't load presets.` action `Retry` |
| `isUnknownSlug` | hint under the chips | `That preset isn't available. Pick another one.` |
| nothing selected | description line | `Pick a camera move for your video.` |
| selected | description line | `{name}: {description}` |
| card | name (always visible, max 2 lines) | `{preset.name}` |

### Prompt
| Element | Copy |
|---|---|
| label + badge | `Prompt` · `Optional` |
| placeholder | `Describe the mood or motion, e.g. “foggy morning, slow and calm”` |
| counter | `{n}/500` |
| helper | `Some presets ignore the prompt.` |

### Generate (AC-4, AC-5)
| State | Element | Copy |
|---|---|---|
| preset selected | button | `Generate · {cost} credits` |
| no preset | button | `Generate` |
| submitting | button (spinner via `isLoading`) | `Starting…` |
| no-image-no-preset | helper | `Add an image and pick a preset to generate.` |
| no-image | helper | `Add an image to generate.` |
| no-preset | helper | `Pick a preset to generate.` |
| uploading | helper | `Wait for the upload to finish.` |
| balance known | line | `Balance: {balance} credits` |
| balance loading | line | `Balance: …` |
| balance error | line | `Balance unavailable` |
| guest-offer (signed out) | line | `Free credits to start. No sign-up needed.` |
| insufficient | link (`ButtonLink` to `/credits`) + line | `Get credits` · `You have {balance} credits. This video needs {required}.` |
| error/input-missing | inline error | `That image is no longer available. Add it again.` |
| error/input-not-ready | inline error | `Your image is still uploading. Try again in a moment.` |
| error/session | inline error | `Couldn't start a session. Try again.` |
| error/invalid | inline error | `Something went wrong. Try again.` |
| error/network | toast | `Couldn't reach the server.` action `Retry` |

### Canvas: empty / uploading / ready (`HowItWorks`)
| Element | Copy |
|---|---|
| heading | `Make a video in three steps` |
| sub | `Add a photo, pick a camera move and press Generate. Your video is ready in about a minute.` |
| step 1 | `Add image` · `Drop, browse or paste a photo.` |
| step 2 | `Pick a preset` · `Choose one of {n} camera moves.` (`n = 0` → `Choose a camera move.`) |
| step 3 | `Generate` · `Get a 5-second video to download and share.` |
| step state badges | `Done` · `Uploading…` · (current step: accent border, no badge) |

Step states: `empty` → 1 current, 2 todo, 3 todo. `uploading` → 1 busy, 2 current. `ready` without a preset → 1 done, 2 current. `ready` with a preset → 1 done, 2 done, 3 current.
**Illustrations** (ours, no external assets): 1 = a dashed-border image frame with an arrow glyph; 2 = three mini cards, the middle one accent-bordered; 3 = a 16:9 frame with a gradient "scene" running the `hf-motion-zoom-in` loop. All are CSS/inline SVG. Motion only under `motion-safe:`.

### Canvas: progress (AC-6)
| Phase | heading (`CanvasHeading`) | sub |
|---|---|---|
| submitting | `Starting…` | `Sending your job.` |
| queued | `Queued` | `Waiting for a free worker…` |
| queued with `wasRequeued` | `Queued` | `Retrying on another worker…` |
| generating | `Generating` | `Animating your image. This usually takes under a minute.` |

- **Also shown:**
  - the input thumbnail (`inputImageUrl`: the local `previewUrl` for this tab's upload, else `job.input_image_url`), `alt=""` because the heading carries the meaning
  - the preset name (`{presetName}`)
  - the timer `{m:ss} elapsed`
  - `StatusSteps` pills `Queued` → `Generating` → `Done`, with the current one accent-filled
  - an indeterminate `ProgressBar` labelled `Generating video`
- **Connection:** when `connection === "polling"`, a muted line reads `Live updates paused. Checking every 5 seconds.`

### Canvas: result (AC-7)
| Element | Copy |
|---|---|
| heading | `Your video is ready` |
| meta | `{presetName} · done in {m:ss}` (from `created_at` → `finished_at`) |
| video | `<video src={video_url} poster={poster_url} autoPlay muted loop playsInline controls>`; under `prefers-reduced-motion: reduce`, `autoPlay` is off |
| actions | `Download` (busy: `Downloading…`) · `Make another` · `Share` (after copying: `Link copied` for 2s) |

**The actions (`useResultActions(job)`, T-004-5):**
- **Download:** `fetch(video_url)` → blob → an object-URL `<a download="higgsfield-{preset_slug}-{first 8 of id}.mp4">` click → revoke. On any failure (CORS, expired URL): `window.open(video_url, "_blank", "noopener")`.
- **Share:**
  - `url = location.origin + "/v/" + job.id`, then `navigator.clipboard.writeText(url)`.
  - On success, the label shows `Link copied` for 2000 ms.
  - If the clipboard is unavailable or rejects, `window.open(url, "_blank", "noopener")`.
  - Share renders as a `<button>`, with a real `<a href="/v/{id}">` "Open share page" link (`text-muted underline`, small) under the actions, so the link exists for users without clipboard access.
- **Make another:** `useActiveJob.makeAnother`, then focus moves to the preset group.

### Canvas: failure (AC-8) and missing
| Variant | heading | body | actions |
|---|---|---|---|
| failed | `Generation failed` | `Generation failed — your {credit_cost} credits were refunded` then, if `job.error_message` is set, a second muted line with `{error_message}` | `Retry` (primary) · `Make another` (secondary) |
| missing | `Not available` | `This generation isn't available anymore.` | `Back to create` (`onDismissMissing`) |

### History strip (AC-9)
| State | Copy |
|---|---|
| 0 entries | not rendered |
| ≥ 1 entry | label `This session` |
| each tile | `aria-label` `Open {presetName}, {statusLabel}`; `statusLabel` ∈ `Queued` · `Generating` · `Done` · `Failed`; the preset name shows under the tile (1 line, truncated); a status dot shows for queued/running/failed |
| image fails / null | fallback tile: the first letter of the preset name on `bg-bg` |
| active | `aria-current="true"` + accent border |

### Announcements (`StatusAnnouncer`, polite)
The announcer gets **one** message per phase change (never per timer tick):
- `uploading` → `Uploading image`
- `ready` (from uploading) → `Image uploaded`
- `submitting` → `Starting generation`
- `queued` → `Generation queued`
- `generating` → `Generating video`
- `succeeded` → `Video ready`
- `failed` → `Generation failed. Your {credit_cost} credits were refunded.`
- missing → `This generation isn't available anymore.`

The rule: the page keeps the previous phase in a ref and sets the message only when the phase changes.

### Toasts (network)
- Only one toast shows at a time. The submit toast has priority over the presets toast.
- Error toasts don't auto-dismiss. **Dismiss** (`aria-label="Dismiss"`) hides the toast until the next failure.

## Auto-guest flow (AC-5)
**Decision:** the guest session is created **lazily by the first call that needs auth**, and no dialog ever appears.
- The first image drop (upload needs auth, per contract) creates the session. A signed-out visitor's upload starts immediately, and the upload runs while they pick a preset.
- Generate also goes through the same runner, so it still works if the session was lost in between (cookie expired, created in another tab, `/me` still loading).

**Sequence: a signed-out visitor, one Generate click:**
1. `App` → `useSession()`: `GET /api/v1/me` → 401 → `status: "signed-out"`. The header shows `GuestButton`. The page renders; `useCredits(false)` → the `Free credits to start. No sign-up needed.` line.
2. The visitor drops `photo.jpg`. `useImageUpload.selectImage` passes `checkImageFile`, shows the preview and sets `uploading`.
3. The runner sees `signed-out` → `ensureGuest()` → `startGuestSession()` → `POST /api/v1/auth/guest` → 201, and the cookie is set. The outlet state becomes `signed-in`, so the header shows `SessionBadge`.
4. `useCredits(true)` → `GET /api/v1/credits` → `Balance: 60 credits`.
5. The runner → `POST /api/v1/uploads` → 201 → the XHR `PUT upload_url` with progress → `POST /api/v1/uploads/{asset_id}/complete` → 200 → `ready`. Focus follows the rule in Accessibility.
6. The visitor picks "Dolly In" (the URL becomes `?preset=dolly-in`). The button reads `Generate · 20 credits`.
7. **Click Generate** → `useActiveJob.startJob(draft)` → `useCreateJob.submitJob` → runner (signed in, so no guest call) → `POST /api/v1/jobs` with a new `idempotency_key` → 202.
8. `handleJobAccepted`: `activeJobId` set, a history entry recorded, `refreshCredits()` → `Balance: 40 credits`. `useJobEvents` opens `EventSource /api/v1/jobs/{id}/events` and runs `GET /api/v1/jobs/{id}`. The canvas is `queued`, the heading gets focus, and on mobile the canvas scrolls into view.

**Variant: the session is lost before Generate** (step 7 returns 401):
1. The runner → `ensureGuest()` → a new guest → the create is retried once.
2. The retry returns **404** (the asset belongs to the old guest) → `error/input-missing` → `That image is no longer available. Add it again.`
3. Nothing is charged, and the visitor re-adds the image.

**Variant: guest creation fails** (network): upload → `error/session` → `Couldn't start a session. Try again.` The **Try again** button runs the whole sequence again.

## `?preset=<slug>` deep link (AC-3)
1. `usePresetSelection` reads `searchParams.get("preset")`. Presets load; if a preset has that slug, it is `selectedPreset`. The category filter stays `all`, so the card is visible.
2. **Once**, on the first render where `presets.status === "ready"` and a preset is selected, `PresetPicker` scrolls the checked card into view (`block: "nearest"`, not smooth), without moving focus.
3. An unknown slug → `isUnknownSlug` → the hint `That preset isn't available. Pick another one.`. Nothing is selected, and the param stays until the user picks (no redirect, no error toast).
4. Selecting a card writes `?preset=<slug>` with `replace: true`, so a reload or a shared link reopens the same preset without flooding history. **Make another** removes the param.
5. Other query params are preserved by the functional `setSearchParams` updater.
6. Explore's "Recreate" (spec 006) links to `/create/video?preset=<slug>`, and nothing else is needed.

## Accessibility
- **Preset keyboard selection:**
  - `PresetPicker` renders a `<fieldset ref={groupRef}>` with `<legend>` `Preset`.
  - Each `PresetCard` is a `<label>` wrapping `<input type="radio" name="preset" value={slug} checked={isSelected} onChange={() => onSelect(slug)} className="peer sr-only">`.
  - Native radios give one Tab stop for the group, **Arrow keys move and select**, and Space selects.
  - The card's focus ring comes from `has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent`, and its selected style from `has-[:checked]:border-accent`. Tailwind 4.3 supports `has-[…]`.
  - A selected preset hidden by the filter leaves no radio checked; Tab then lands on the first card (native behaviour, acceptable).
- **Category chips:** `<div role="group" aria-label="Preset categories">` of `<button type="button" aria-pressed>`.
- **Drop zone:**
  - The whole zone is a drop target (`onDragOver` → `preventDefault` + highlight, `onDragLeave`, `onDrop` → the first file of `dataTransfer.files`).
  - Keyboard and screen-reader access is the real `<button>` `Browse files`, which clicks a hidden `<input type="file" accept="image/png,image/jpeg,image/webp">`. The input's `value` is reset after each pick, so choosing the same file again works.
  - The zone has `aria-describedby` pointing at the hint and error ids. Errors are `role="alert"`.
- **Paste:** `useClipboardImagePaste(onImage)` adds a `window` `paste` listener while the page is mounted. It acts **only** when `clipboardData.files` has an image. It then calls `preventDefault()` and `onImage(file)`. Text pastes into the prompt are untouched.
- **Focus after upload:** a `CreateVideoPanel` effect runs when the upload status goes `uploading → ready`.
  - **If `document.activeElement` is inside the drop zone** (the user is still there: the Browse/Replace button, or the body after a drop), focus moves to the checked radio in `groupRef`, or else the first radio.
  - If the user already moved on (typing a prompt, picking a preset), focus is left alone.
  - The announcer says `Image uploaded` either way.
- **Focus after Generate:**
  - When the phase becomes `submitting`, focus moves to the canvas `CanvasHeading` (`<h2 tabIndex={-1}>`).
  - The heading element is **the same element** across submitting/queued/generating/succeeded/failed (only its text changes), so focus isn't lost when the view switches. `CreateVideoCanvas` renders `CanvasHeading` once, above the view body.
  - **After "Make another"**, focus moves to the preset group.
  - After opening a history entry, focus moves to the canvas heading.
- **Live status:** `StatusAnnouncer` is `<p className="sr-only" aria-live="polite" aria-atomic="true">`, messages as listed. The elapsed timer is outside the live region. `StatusSteps` marks the current pill with `aria-current="step"`.
- **Progress bars:** `role="progressbar"`, `aria-label`, `aria-valuemin=0`, `aria-valuemax=100`, and `aria-valuenow` when determinate (omitted when indeterminate).
- **Motion:** every animation is under `motion-safe:`. `usePrefersReducedMotion()` (`matchMedia("(prefers-reduced-motion: reduce)")`, T-004-1 in `usePrefersReducedMotion.ts`) turns off video autoplay and smooth scrolling.
- **Buttons:** every clickable element is a `<button>`, `<a>` or `<label>` + radio. `Button` gets the shared focus outline through `buttonClasses`.
- **Toast:** `role="alert"`, the action and Dismiss are real buttons, and focus isn't moved to the toast.

## Preset card visuals (motion hints)
- `preview_url` is `null` until spec 006, so cards animate **the visitor's own image** (the ready or uploading `previewUrl`) with a CSS approximation of the move. Before an image exists, a neutral gradient tile (`bg-gradient-to-br from-border to-bg`) is used.
- If `preview_url` is set, the card shows `<video src muted loop playsInline autoPlay>` instead (reduced motion: no autoplay).
- The animation runs **only on hover, focus-within or selected** (`motion-safe:` + `group-hover:`/`has-[:checked]:`/`has-[:focus-visible]:` variants), so the grid stays calm.
- `presetMotionHints.ts` maps slug → class, with fallback `hf-motion-zoom-in`:
  `dolly-in, ken-burns, orbit-push, spiral-in, crash-zoom` → `hf-motion-zoom-in`; `dolly-out` → `hf-motion-zoom-out`; `pan-left, whip-pan` → `hf-motion-pan-left`; `pan-right, slow-drift` → `hf-motion-pan-right`; `tilt-up` → `hf-motion-tilt-up`; `handheld` → `hf-motion-shake`.
- **`styles.css`** (T-004-1) adds `@theme` tokens: `--animate-hf-motion-zoom-in: hf-zoom-in 2.4s ease-in-out infinite alternate`, and likewise `zoom-out`, `pan-left`, `pan-right`, `tilt-up`, `shake` (0.5s linear infinite), plus `--animate-hf-progress: hf-progress 1.4s ease-in-out infinite` for the indeterminate bar. Each has matching `@keyframes`, using transforms only (`scale`/`translate`), within 1.0–1.15 scale so image edges never show (the image is `object-cover` inside `overflow-hidden`).
- `presetMotionClass(slug)` returns the Tailwind utility string, e.g. `"motion-safe:group-hover:animate-hf-motion-zoom-in …"`. Keep the full class names as **literal strings** in the file, so Tailwind's scanner sees them.
- **Card layout:** `aspect-square` tile (`rounded-xl overflow-hidden`), name below it (`text-xs font-semibold`, `line-clamp-2`), an accent check badge at the tile's top-right when selected, `border-2 border-transparent` → `border-accent` when checked.

## Test strategy (web)
- **Runner:** T-004-1 adds **`vitest@^5`** (peer `vite ^8`, checked with `npm view`) as the only new devDependency, with the script `"test": "vitest run"`. It uses the Node environment (no jsdom, no testing-library): only framework-free modules are unit-tested.
- **Tests:**
  | Test file | Proves | Task |
  |---|---|---|
  | `canvasPhase.test.ts` | the priority rules; every journey in the transitions table stays inside `CANVAS_TRANSITIONS` | T-004-1 |
  | `imageFileRules.test.ts` | 3 accepted types; gif/heic rejected; 0 bytes and 10 485 761 bytes rejected; exactly 10 485 760 accepted | T-004-1 |
  | `elapsedTime.test.ts` | `0:00`, `0:07`, `1:42`, `12:05`, negative → `0:00` | T-004-1 |
  | `sessionHistoryStore.test.ts` | newest first, dedupe by id, cap 6, invalid JSON → `[]`, bad entries dropped, a throwing storage doesn't throw | T-004-2 |
  | `jobStatusWatcher.test.ts` | rules 1–6 above with a fake `EventSource` + `vi.useFakeTimers()`: terminal frame closes the ES; error starts a 5s poll; open stops the poll; CLOSED reconnects with backoff; a late poll doesn't override live; `missing` stops; `stop()` silences callbacks | T-004-3 |
- **Lint on tests:** `max-lines-per-function: 40` applies to test callbacks too, so use top-level `test(...)` calls (no big `describe` wrappers) and small builders.
- **Hooks and components:** not unit-tested here (no DOM runner). They're covered by typecheck plus the manual flow check in T-004-5 against the local stack (once T-003-3/4/5 land) and by `verify-slice` on the live URL.

## Files (each ≤ 200 lines; one component per file)
Paths are relative to `apps/web/`. **F** = `src/features/create-video/`.

| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `package.json`, `package-lock.json` | Edit | T-004-1 | add `vitest` devDependency + `test` script |
| `src/styles.css` | Edit | T-004-1 | motion-hint + indeterminate-progress keyframes and `--animate-*` tokens |
| `src/ui/buttonStyles.ts` | New | T-004-1 | `ButtonVariant` + `buttonClasses(variant)` incl. focus outline |
| `src/ui/Button.tsx` | Edit | T-004-1 | use `buttonClasses` (behaviour unchanged) |
| `src/ui/ButtonLink.tsx` | New | T-004-1 | router `Link` styled as a button |
| `src/ui/ProgressBar.tsx` | New | T-004-1 | determinate/indeterminate accessible bar |
| `src/ui/Toast.tsx` | New | T-004-1 | fixed bottom-right toast with action + dismiss |
| `F/createVideoTypes.ts` | New | T-004-1 | all shared types of this feature (§ Shared types) |
| `F/createVideoCopy.ts` | New | T-004-1 | every user-visible string (§ copy tables) |
| `F/canvasPhase.ts` | New | T-004-1 | `deriveCanvasPhase`, `CANVAS_TRANSITIONS`, `isTerminalJobStatus` |
| `F/canvasPhase.test.ts` | New | T-004-1 | phase priority + journeys |
| `F/imageFileRules.ts` | New | T-004-1 | `ACCEPTED_IMAGE_TYPES`, `MAX_IMAGE_BYTES`, `checkImageFile` |
| `F/imageFileRules.test.ts` | New | T-004-1 | type/size edges |
| `F/elapsedTime.ts` | New | T-004-1 | `formatElapsed(seconds)` |
| `F/elapsedTime.test.ts` | New | T-004-1 | formatting edges |
| `F/presetMotionHints.ts` | New | T-004-1 | slug → motion utility classes (literal strings) |
| `F/usePrefersReducedMotion.ts` | New | T-004-1 | `matchMedia` reduced-motion boolean |
| `F/useGuestSessionRunner.ts` | New | T-004-2 | lazy guest session + one 401 retry, shared in-flight promise |
| `F/usePresets.ts` | New | T-004-2 | load presets |
| `F/usePresetSelection.ts` | New | T-004-2 | `?preset=` URL selection + category filter |
| `F/useCredits.ts` | New | T-004-2 | balance view + refresh + apply 402 balance |
| `F/sessionHistoryStore.ts` | New | T-004-2 | pure read/write/upsert of the 6-entry history |
| `F/sessionHistoryStore.test.ts` | New | T-004-2 | store rules |
| `F/useSessionHistory.ts` | New | T-004-2 | React state over the store |
| `F/putFileWithProgress.ts` | New | T-004-2 | XHR PUT to the presigned URL with progress + abort |
| `F/useImageUpload.ts` | New | T-004-2 | validate → presign → PUT → complete |
| `F/useCreateJob.ts` | New | T-004-3 | idempotent submit + 402/404/409/network mapping |
| `F/jobStatusWatcher.ts` | New | T-004-3 | SSE + poll fallback + reconnect (framework-free) |
| `F/jobStatusWatcher.test.ts` | New | T-004-3 | watcher rules 1–6 |
| `F/useJobEvents.ts` | New | T-004-3 | React wrapper over the watcher → `JobWatch` |
| `F/useElapsedSeconds.ts` | New | T-004-3 | ticking elapsed seconds |
| `F/useActiveJob.ts` | New | T-004-3 | active job id, history/credits sync, make another, retry, open history |
| `F/useClipboardImagePaste.ts` | New | T-004-4 | window paste → image file |
| `F/CreateVideoPanel.tsx` | New | T-004-4 | panel layout + focus-after-upload effect |
| `F/ImageDropZone.tsx` | New | T-004-4 | drop / browse / paste zone + inline errors |
| `F/ImageThumbnail.tsx` | New | T-004-4 | thumbnail, upload overlay, Replace/Remove |
| `F/PresetPicker.tsx` | New | T-004-4 | fieldset, chips, grid, states, deep-link scroll |
| `F/PresetCategoryChips.tsx` | New | T-004-4 | category filter buttons |
| `F/PresetCard.tsx` | New | T-004-4 | radio card with motion preview + always-visible name |
| `F/PromptField.tsx` | New | T-004-4 | optional prompt textarea + counter |
| `F/GenerateSection.tsx` | New | T-004-4 | cost button / Get credits link, balance, helper, inline errors |
| `F/CreateVideoPage.tsx` | New | T-004-5 | wires hooks → panel/canvas/strip/toast/announcer |
| `F/StatusAnnouncer.tsx` | New | T-004-5 | polite live region |
| `F/CreateVideoCanvas.tsx` | New | T-004-5 | phase → view, stable heading |
| `F/CanvasHeading.tsx` | New | T-004-5 | focusable `h2` |
| `F/HowItWorks.tsx` | New | T-004-5 | 3-step onboarding with step states |
| `F/HowItWorksStep.tsx` | New | T-004-5 | one step card + illustration |
| `F/JobProgressView.tsx` | New | T-004-5 | thumbnail, preset, status, timer, bar |
| `F/StatusSteps.tsx` | New | T-004-5 | Queued → Generating → Done pills |
| `F/ResultView.tsx` | New | T-004-5 | video player + meta |
| `F/ResultActions.tsx` | New | T-004-5 | Download / Make another / Share buttons |
| `F/useResultActions.ts` | New | T-004-5 | blob download + copy share link |
| `F/FailureView.tsx` | New | T-004-5 | failed (refund) / missing views |
| `F/SessionHistoryStrip.tsx` | New | T-004-5 | last-6 strip |
| `src/App.tsx` | Edit | T-004-5 | `/create/video` → `CreateVideoPage`; `/v/:jobId` placeholder |

## Reused
- `ui/Button` (every action; `isLoading` for Starting…), `ui/EmptyState` (the `/v/:jobId` placeholder), `ui/AppShell` (outlet context carries the session).
- `api/client.ts` `apiClient` + `api/generated/schema.d.ts` types. No hand-written fetch to our API; the only non-client calls are the presigned storage PUT/GET and `EventSource`, which the typed client can't express.
- `features/session/useSession.ts`: the `SessionContextValue` type and `startGuestSession`, read through `useOutletContext` like `HomePage` does. The `status` it keeps drives the header badge.
- Design tokens in `styles.css` (no new colours), the display font for headings, the `text-red-400` error style from `GuestButton`.
- The contract rules of design 003: 402 top-level body, idempotency keys, SSE close-after-terminal, `: ping`, 5s poll fallback (architecture invariant 4).

## Risks
- **Backend not implemented yet** (routes return 501 until T-003-3/4/5). The web tasks build against the contract types. T-004-5's manual flow check runs only when `curl -s localhost:8000/api/v1/presets` returns 200; otherwise it's reported as SKIPPED, and `verify-slice` covers it later.
- **ESLint `max-lines-per-function: 40` / `complexity: 8`** also hit components and hooks. That's why the tree is fine-grained and `useActiveJob` exists. Map-heavy JSX should move into child components, not grow the parent.
- **The `useActiveJob` ↔ `useCreateJob` callback cycle:** resolved by passing callbacks (§ `useActiveJob`). T-004-3 owns both files, so it picks the concrete wiring, but the returned shapes are fixed by this design.
- **Native `EventSource` reconnects after the server's terminal close:** mitigated by closing on the terminal frame (watcher rule 2) and by a unit test.
- **EventSource can't report HTTP status:** a 404/401 surfaces only as `error` + CLOSED. The poll's `GET /jobs/{id}` then gives the real answer (`missing`), and the watcher stops.
- **Presigned URLs expire after 1h:** history thumbnails fall back to a letter tile, reopen re-fetches, and Download falls back to opening the URL.
- **Cross-origin download needs bucket CORS for GET** (already listed for R2 in design 003). Without it, Download opens a new tab instead of saving.
- **Presigned PUT from the browser needs bucket CORS for PUT + `Content-Type`.** MinIO allows it locally; the R2 rule is in design 003's risks.
- **`local-motion` ignores the prompt:** hence the helper `Some presets ignore the prompt.`
- **Upload on drop creates a guest for visitors who drop and leave** (one row + a 60-credit grant). Accepted for the zero-friction goal; see the Auto-guest decision.
- **Features importing `features/session`:** this matches the existing `HomePage` precedent (type + outlet context only). Moving session to a shared place is a separate refactor, not in this spec.
- **Tailwind class scanning:** dynamic class names (e.g. template strings for motion classes) won't be generated, so `presetMotionHints.ts` keeps full literal strings.
