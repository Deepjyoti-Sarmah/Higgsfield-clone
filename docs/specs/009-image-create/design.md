# Design 009: Create image (text → image)

**Spec:** `docs/specs/009-image-create/spec.md` (APPROVED)
**Backend core:** `docs/specs/003-generation-core/design.md` (job/asset/ledger, claim/lease/reaper, SSE). **Page conventions:** `docs/specs/004-create-video/design.md`. **Credits:** `docs/specs/008-credits/design.md` (balance + the shared runner).
**Contract:** **THREE** new routes — `GET /api/v1/image-options`, `POST /api/v1/image-jobs`, `GET /api/v1/image-jobs/{job_id}` — plus their schemas. Every pre-existing path and schema stays byte-identical. **ONE additive migration** (`0004_image_jobs`).
**Priority:** P1 (D-012). Real text→image is **P2** (D-002 licence + no GPU deploy); P1 ships a placeholder image backend.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Route | Component tree, Files | T-009-7 |
| AC-2 Signed out | Flow 1–2, `api/guestSession.ts` | T-009-2 |
| AC-3 Prompt | Component tree, Copy § Composer | T-009-6 |
| AC-4 Settings + cost | API contract (`/image-options`), Copy § Cost | T-009-0 (contract), T-009-4 (api), T-009-6 (UI) |
| AC-5 Create + HOLD | API contract, Flow 3–4 | T-009-4 (service), T-009-2 (hook) |
| AC-6 Progress (SSE) | Flow 5, Shared web plumbing | T-009-2 (moved watcher), T-009-6 (view) |
| AC-7 Result grid | API contract (`GET /image-jobs/{id}`), Component tree | T-009-4, T-009-6 |
| AC-8 Failure + refund | Flow 6, reused `complete_step_failure` | T-009-5 |
| AC-9 Out of credits | API contract (402), Copy § Generate | T-009-4, T-009-6 |
| AC-10 Backend honesty | Backend reality, `backend` field, Copy § Result | T-009-3, T-009-6 |
| AC-11 Library discipline | Data (kind filter), API contract | T-009-1 |
| AC-12 Contract + data | API contract, Data | T-009-0, T-009-1 |

## API contract (the only contract change)
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| GET | `/api/v1/image-options` | — (**public**, no auth, like `/presets`) | **200** `ImageOptionsResponse {aspect_ratios, qualities, max_count, credit_costs}` | — |
| POST | `/api/v1/image-jobs` | **202** body `ImageJobCreateRequest {prompt, aspect_ratio, quality, count, idempotency_key}` | **202** `ImageJobCreatedResponse {id, status, credit_cost, image_count}` | **401** signed out · **402** `InsufficientCreditsResponse {detail, balance, required}` · **422** |
| GET | `/api/v1/image-jobs/{job_id}` | path `job_id` (uuid) | **200** `ImageJobResponse {id, status, prompt, aspect_ratio, quality, count, credit_cost, backend, image_urls, error_message, created_at, started_at, finished_at}` | **401** · **404** unknown / not the owner / not an image job · **422** |

**Reused route (no change):** `GET /api/v1/jobs/{job_id}/events` — the SSE stream is status-only (`JobStatusEvent {job_id, status}`) and owner-scoped by job id, so an image job streams through it unchanged. **No new SSE route.**

### `ImageOptionsResponse` — why this route exists
The Generate button must show the cost *before* the POST (AC-4), and the cost depends on user-chosen settings, so the client cannot read it from a preset row (`preset.credit_cost` is the video mechanism). Mirroring the cost formula in TypeScript would duplicate money maths; instead the server publishes the allowed values and the unit costs, and the client multiplies by `count`. Same reasoning as `GET /presets` for video. It is **public** because none of it is private (the video presets route is public too).

### `ImageJobCreateRequest`
| Field | Type | Rule |
|---|---|---|
| `prompt` | str | required, 1–500 chars (the `job.prompt` column is `String(500)`) |
| `aspect_ratio` | `Literal["1:1","4:5","3:2","16:9","9:16"]` | required |
| `quality` | `Literal["standard","high"]` | required |
| `count` | int | `1 ≤ count ≤ 4` (`MAX_IMAGE_COUNT`) |
| `idempotency_key` | str | 8–100 chars, unique per `(user_id)` by the existing `uq_job_user_idempotency_key` |

### `backend` in the response (AC-10)
The field is read from the job's `job_step.backend` (already a column, set by `finish_step`), so the page can honestly caption a placeholder result without the client knowing `GENERATION_BACKEND`. It is `null` until a worker starts the step.

## Backend reality (what actually produces an image)
| Backend | Video today | Images after this spec |
|---|---|---|
| `local-motion` (default) | real ffmpeg motion mp4, 5 s ≤720p | **placeholder PNG** (deterministic gradient at the requested aspect) |
| `mock` | fixture mp4, 1 s 64×64 | **placeholder PNG** |
| `modal` | `BackendNotConfiguredError` | `BackendNotConfiguredError` ("image generation is not configured") |
| `openrouter` | `BackendNotConfiguredError` | `BackendNotConfiguredError` |

- **No real image model runs.** `ImageModelAdapter` is the new port; only `PlaceholderImageAdapter` implements it. The D-002 model (LLaDA-Image Turbo on Modal) is P2 and blocked on licence + GPU + R2 — the spec says so out loud.
- Both local backends return a **real, valid PNG file** of the right dimensions, written by a dependency-free pure-Python PNG encoder (`adapters/png_placeholder.py`, `zlib` + `struct`). It is a placeholder by content, not by format, so the whole upload/serve/view path is exercised for real.
- The UI must not name a model. The result caption says the images are demo placeholders whenever `backend` is a placeholder name.
- No new env var: `GENERATION_BACKEND` keeps its meaning; `select_image_adapter(settings)` maps it.

## Data (ONE additive migration `0004_image_jobs`)
**Nothing video changes shape.** `job`, `asset` and `job_step` are extended; no column is dropped and no existing index/constraint is removed.

| Change | Why |
|---|---|
| `asset.kind` check gains `'output_image'` | a generated image is a first-class asset, distinguishable from `input_image`/`output_video`/`output_poster` |
| `job.kind` `String(16) NOT NULL server_default 'video'` + check `kind IN ('video','image')` | one explicit discriminator, so the Library/read routes can stay video-only with an index-friendly predicate |
| `job.preset_slug` and `job.input_asset_id` become **nullable** | an image job has neither; the new `ck_job_inputs_by_kind` check keeps the video guarantee strong: `(kind='video' AND preset_slug IS NOT NULL AND input_asset_id IS NOT NULL) OR (kind='image' AND preset_slug IS NULL AND input_asset_id IS NULL)` |
| `job.aspect_ratio String(8)`, `job.quality String(16)`, `job.image_count Integer`, all nullable | the image request must be readable by the worker and the read route after a restart; the `ck_job_image_params` check requires them exactly when `kind='image'` (`image_count BETWEEN 1 AND 4`) and `NULL` when `kind='video'` |
| new table `job_image (id, job_id FK job ON DELETE CASCADE, position int, asset_id FK asset, created_at)` with `uq_job_image_position (job_id, position)` and `uq_job_image_asset (asset_id)` | `count` images per job; `job` has only two output FKs (video/poster), which do not generalise to N images |
| `ix_job_user_created` unchanged | it still serves `GET /jobs`; the added `kind='video'` predicate is applied by the existing index scan |

`GET /api/v1/jobs` (Library) and `GET /api/v1/jobs/{job_id}` gain `job.kind = 'video'` (AC-11), so image jobs never leak into the P0 video surfaces and `JobResponse`'s non-null `preset_slug` stays true. **No downgrade data loss beyond the new table/columns.**

## Flow
1. `/create/image` mounts → `useImageOptions()` reads the public options; `useCreditBalance(session)` (shared, `api/credits.ts`) reads the balance; the page reads the session from the outlet context. Signed out → `startGuestSession()` through `api/guestSession.ts` (AC-2).
2. The composer renders the prompt, the aspect/quality chips and the count stepper from the options payload; the Generate label is `Generate · count × unit` (AC-4). Nothing is fetched per keystroke.
3. Generate → `useCreateImageJob` mints a fresh `crypto.randomUUID()` key → `POST /api/v1/image-jobs` through the guest runner. **202** → phase `queued`; 402 → the balance/required line (AC-9); 401 after the guest retry → session error.
4. API: `create_image_job` (router) → `require_current_user` → service `create_image_job(session, user_id, request)`, **one transaction**: `lock_user_row` → idempotency lookup (`(user_id, key)` → same job, no second HOLD) → `image_credit_cost(quality, count)` → balance check → `insert_image_job(kind='image', …)` + `insert_job_step(kind='generate_image')` + `HOLD` → `notify_job_event` → `commit`. Insufficient → rollback + `InsufficientCreditsError` → router returns 402 with the top-level body (the spec-003 pattern).
5. Web watches `GET /jobs/{id}/events` (SSE, poll fallback) and reads the job through `GET /image-jobs/{id}`; the watcher is the spec-004 one, moved to `api/` and made generic over the job type, so there is exactly one implementation (AC-6).
6. Worker: the claim loop already returns `ClaimedStep.kind`. `worker.py` dispatches on it: `generate_video` → `generation_runs.run_claimed_step` unchanged; `generate_image` → `services/image_generation_runs.run_image_step` (no input download; reads `prompt/aspect_ratio/quality/image_count` from the job, calls `image_adapter.generate_image`, uploads each PNG); anything else → the step fails. The image run lives in its own module and imports `renew_lease_until_lost` from `generation_runs`, so the worker (not `generation_runs`) is the dispatcher — no import cycle and no 200-line overrun.
7. Success → `services/image_step_completion.complete_image_step_success` inserts one `output_image` asset per image + its `job_image` row, transitions the job to `succeeded`, writes `SETTLE 0`, notifies, commits. Failure (including `BackendNotConfiguredError`) → the existing `complete_step_failure` → job `failed` + `RELEASE` + notify (AC-8). Lease renewal and the reaper are untouched.
8. Web result: `GET /image-jobs/{id}` returns `image_urls` (ready assets only, presigned via the existing `build_asset_url`), `backend`, and the user-safe `error_message`. The grid renders `count` images with `alt` text and Download links (AC-7).

## Component tree
```
CreateImagePage                       (features/image-create/CreateImagePage.tsx)
├── title + subtitle                  (imageCreateCopy)
├── ImageComposer                     (ImageComposer.tsx)   prompt + settings + generate
│   ├── PromptField                    (prompt textarea + counter)
│   ├── ImageSettingsRow               (ImageSettingsRow.tsx) aspect chips · quality chips · count stepper
│   └── GenerateSection                (ui/Button + cost label + balance + 402 line)
├── ImageStage                        (ImageStage.tsx)      phases
│   ├── ImageOptionsStates             (options loading/error + Retry)
│   ├── ImageProgressView              (queued/running, aria-live)
│   ├── ImageResultGrid                (ImageResultGrid.tsx) count images + Download + placeholder caption
│   └── ImageFailureView               (failed / missing + retry / make another)
```
- `CreateImagePage` props: none — `useOutletContext<SessionContextValue>()`, `useImageOptions()`, `useCreditBalance(session)`, `useImageJob(session)` once each.
- `ImageComposer` props: `{ options: ImageOptionsState; settings: ImageSettingsControls; prompt: string; onPromptChange(value: string): void; generate: ImageGenerateProps }`.
- `ImageSettingsRow` props: `{ options: ImageOptionsResponse; settings: ImageSettingsControls }`.
- `ImageGenerateProps` = `{ cost: number; canGenerate: boolean; blockedReason: ImageBlockedReason | null; isSubmitting: boolean; balance: BalanceView; insufficient: InsufficientCredits | null; submitError: ImageSubmitErrorKind | null; onGenerate(): void }`.
- `ImageStage` props: `{ phase: ImagePhase; watch: ImageJobWatch; onRetry(): void; onMakeAnother(): void }`.
- `ImageResultGrid` props: `{ imageUrls: string[]; prompt: string; backend: string | null }`.

## Shared web plumbing (what moves, and why)
| Piece | Today | After | Reason |
|---|---|---|---|
| `jobStatusWatcher` (SSE + poll + final fetch) | `features/create-video/jobStatusWatcher.ts` (already dependency-injected: `deps.fetchJob`, `deps.openEventSource`) | **moved** to `api/jobStatusWatcher.ts`, made generic over the job type (`<J extends { status: JobStatus }>`), still owning the SSE URL `/api/v1/jobs/{id}/events`; the terminal-status predicate moves to `api/jobStatus.ts` because the watcher is at the 200-line limit (197 today) | the Library (P1 #2) and Create image need the same watcher; a feature may not import another feature's internals |
| `useJobEvents` | create-video only | imports the moved module and passes the video `Job` type | spec-004 behaviour unchanged |
| credit balance | `features/create-video/useCredits.ts` (feature-internal) | `api/credits.ts` gains `useCreditBalance(session)`; Create image uses it; create-video keeps its hook for now | rule of two + feature isolation; consolidating create-video onto the shared hook is a P2 cleanup |
| image job submit + read | — | `api/imageJobs.ts` (`useCreateImageJob`, `useImageJob`) and `api/imageOptions.ts` (`useImageOptions`) | one data owner per resource, the `api/library.ts` shape |

## Copy (`imageCreateCopy.ts`, one object; no inline literals in components)
| Key | Value |
|---|---|
| `page.title` | "Create image" |
| `page.subtitle` | "Describe an image, pick its shape, and generate up to four." |
| `prompt.label` | "Prompt" |
| `prompt.placeholder` | "Describe the scene you imagine" (the observed placeholder, screenshot 15) |
| `prompt.counter(value)` | `` `${value}/500` `` |
| `settings.aspectLabel` | "Aspect ratio" |
| `settings.qualityLabel` | "Quality" |
| `settings.countLabel` | "Number of images" |
| `settings.aspectLabels` | `{"1:1":"Square","4:5":"Portrait","3:2":"Landscape","16:9":"Wide","9:16":"Vertical"}` |
| `settings.qualityLabels` | `{"standard":"Standard","high":"High"}` |
| `settings.countValue(count)` | `` `${count}` `` |
| `generate.label` | "Generate" |
| `generate.withCost(cost)` | `` `Generate · ${cost} credits` `` (identical to create-video's label) |
| `generate.blockedNoPrompt` | "Describe the image first." |
| `generate.submitting` | "Starting..." |
| `generate.balanceKnown(balance)` | `` `Balance: ${balance} credits` `` |
| `generate.balanceLoading` | "Checking your credits..." |
| `generate.balanceError` | "Balance unavailable." |
| `generate.insufficient(balance, required)` | `` `You have ${balance} credits. This image needs ${required}.` `` |
| `generate.getCredits` | "Get credits" → `/credits` |
| `generate.sessionError` | "Your session ended. Reload to continue." |
| `states.optionsError` | title "We couldn't load the image options." · body "Check your connection and try again." · action "Retry" |
| `states.loading.srText` | "Loading image options" |
| `progress.queued` | "Queued" |
| `progress.running` | "Generating your image..." |
| `progress.succeeded` | "Your images are ready." |
| `result.imageAlt(index, prompt)` | `` `Generated image ${index}: ${prompt}` `` |
| `result.download` | "Download" |
| `result.makeAnother` | "Make another" |
| `result.placeholderNotice` | "Demo placeholder images - a real image model ships later." |
| `failure.title` | "This generation failed and its credits were refunded." |
| `failure.missing` | "This generation is no longer available." |
| `failure.retry` | "Try again" |

## Accessibility
- One `h1` (`page.title`); the composer's fieldset legends label the aspect/quality/count groups, and every chip is a real radio `<input>` with a visible text label (the source flow's unlabelled "Auto" chips are the anti-pattern).
- The prompt is a labelled `<textarea>` with a `maxlength=500` and a visible counter.
- The Generate button is `ui/Button` (real `<button>`, shared focus ring) and is `disabled` while submitting; the cost is part of its text, not a colour.
- Phase changes are announced in a `role="status"` polite region; failures use `role="alert"` (the create-video pattern).
- The result grid is a `<ul>` of `<li>`; each image is an `<img>` with `result.imageAlt(index, prompt)` and a Download link; the placeholder caption is visible text.
- The options-loading region is `aria-busy="true"` with an `sr-only` `states.loading.srText`.

## Files (each ≤ 200 lines; paths relative to the repo root)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `apps/api/app/domain/image_rules.py` | New | T-009-0 | the aspect/quality literals, allowed tuples, `MAX_IMAGE_COUNT`, the unit costs + `image_credit_cost(quality, count)`, the pixel sizes per aspect |
| `apps/api/app/schemas/image_jobs.py` | New | T-009-0 | the five image schemas (request, created, job, costs, options) |
| `apps/api/app/routers/image_jobs.py` | New | T-009-0 → T-009-4 | T-009-0 adds the three 501 stubs; T-009-4 replaces the bodies keeping names/signatures/responses |
| `apps/api/app/main.py` | Edit | T-009-0 | include the image router |
| `packages/contracts/openapi.json` | Edit | T-009-0 | regenerated |
| `apps/api/migrations/versions/0004_image_jobs.py` | New | T-009-1 | the additive migration (kind, params, nullable inputs, `output_image`, `job_image`) |
| `apps/api/app/models/job.py`, `models/asset.py`, `models/job_image.py` | Edit/New | T-009-1 | the columns/checks and the child table |
| `apps/api/app/repositories/jobs.py`, `repositories/image_jobs.py` | Edit/New | T-009-1 | video-only filters on the existing queries; `insert_image_job` + `insert_job_image` + `list_job_images` + `find_owned_image_job` |
| `apps/api/app/services/job_views.py` | Edit | T-009-1 | `read_owned_job` returns `None` for a non-video job (so `GET /jobs/{id}` 404s, AC-11) |
| `apps/api/app/adapters/image_model_adapter.py` | New | T-009-3 | the `ImageModelAdapter` port + request/result dataclasses |
| `apps/api/app/adapters/png_placeholder.py` | New | T-009-3 | dependency-free deterministic PNG encoder |
| `apps/api/app/adapters/placeholder_image_adapter.py` | New | T-009-3 | `PlaceholderImageAdapter` (writes count PNGs) + `UnconfiguredImageAdapter` (raises) |
| `apps/api/app/adapters/backend_selection.py` | Edit | T-009-3 | `select_image_adapter(settings)` |
| `apps/api/app/services/image_job_creation.py` | New | T-009-4 | the one-transaction create (lock → idempotency → cost → HOLD → step) |
| `apps/api/app/services/image_job_views.py` | New | T-009-4 | owner-scoped read with ready `image_urls` + `backend` |
| `apps/api/app/services/image_options.py` | New | T-009-4 | the public options payload from `image_rules` |
| `apps/api/app/services/image_generation_runs.py` | New | T-009-5 | the image step: no input download, reads the job's prompt/params, calls `generate_image`, uploads `count` PNGs |
| `apps/api/app/services/image_step_completion.py` | New | T-009-5 | one transaction: `output_image` assets + `job_image` rows + `succeeded` + `SETTLE` + notify |
| `apps/api/app/services/generation_runs.py` | — | — | **untouched**: it is 181 lines and `image_generation_runs` imports its `renew_lease_until_lost`, so dispatching in the worker avoids both a size overrun and an import cycle |
| `apps/api/app/worker.py` | Edit | T-009-5 | select the image adapter and dispatch on `claimed.kind` (`generate_image` → the image run) |
| `apps/web/src/api/jobStatus.ts` | New | T-009-2 | the shared `JobStatus` type + `TERMINAL_JOB_STATUSES`/`isTerminalJobStatus` predicate |
| `apps/web/src/api/jobStatusWatcher.ts` (+ `.test.ts`) | Move | T-009-2 | the shared, job-generic SSE/poll watcher (imports the predicate from `api/jobStatus.ts`) |
| `apps/web/src/features/create-video/{useJobEvents,canvasPhase}.ts` | Edit | T-009-2 | import the moved watcher/predicate (behaviour unchanged) |
| `apps/web/src/api/credits.ts` | Edit | T-009-2 | `+ useCreditBalance(session)` for pages that only read the balance |
| `apps/web/src/api/imageOptions.ts`, `api/imageJobs.ts` | New | T-009-2 | options read; image create + watch + read hooks |
| `apps/web/src/api/generated/schema.d.ts` | Edit | T-009-2 | regenerated from the new contract |
| `apps/web/src/features/image-create/imageCreateCopy.ts`, `imageCreateTypes.ts`, `imageSettings.ts` | New | T-009-6 | copy, types and the pure settings/cost helpers (+ tests) |
| `apps/web/src/features/image-create/{CreateImagePage,ImageComposer,ImageSettingsRow,ImageStage,ImageResultGrid,ImageFailureView}.tsx` | New | T-009-6 | the page and its components |
| `apps/web/src/App.tsx` | Edit | T-009-7 | the `create/image` route → `CreateImagePage` (replaces the placeholder) |
| `docs/tasks/T-009-{0..7}/report.md` | New | each | per-task report |

## Reused
- API: `require_current_user`, `get_session`, `lock_user_row`, `insert_job_step`, `find_job_by_idempotency_key`, `notify_job_event`, `transition_job_status`, `complete_step_failure` (generic RELEASE), the claim/lease/renew/reaper loop, `JobEventBroker`/`stream_job_status_events`, `find_assets_by_ids`, `build_asset_url`, `insert_asset`, `InsufficientCreditsResponse`, `ErrorResponse`, `JobStatus`. The existing `uq_job_user_idempotency_key`, `uq_job_step_job_kind`, `ix_job_user_created`.
- Web: `apiClient` + the generated schema, `api/guestSession.ts`, the moved `jobStatusWatcher` (one SSE implementation for video, image and the future Library), `api/credits.ts` balance, `ui/Button`, `ui/ButtonLink`, `ui/EmptyState`, `ui/buttonStyles`, the `api/library.ts` hook shape, `SessionContextValue`, `styles.css` tokens.
- Not reused on purpose: `features/create-video/useCreateJob.ts` (entangled with uploads/presets) and `useCredits.ts` (Generate-panel shape). `api/imageJobs.ts` mirrors the 402/idempotency mapping; consolidating the two is a P2 cleanup.

## Tasks
`docs/specs/009-image-create/tasks.md` — waves T-009-0 → (T-009-1 ∥ T-009-2 ∥ T-009-3) → (T-009-4 ∥ T-009-5 ∥ T-009-6) → T-009-7.

## Risks
- **A placeholder is not a product.** The page can generate images that are obviously fake gradients. Mitigated by AC-10 (the response names the backend and the page captions placeholders) and by the spec/README saying so. The upside is that the *entire* path — HOLD, step, adapter, upload, `job_image`, presets-free read, SSE, grid — is exercised for real, so the real model is a drop-in adapter.
- **`modal`/`openrouter` cannot do images**, so an operator who sets those backends gets a clear failure + refund rather than images. Documented in the backend table; `local-motion` (the default) and `mock` both work.
- **Migration touches `job`.** Making `preset_slug`/`input_asset_id` nullable could weaken video guarantees, so `ck_job_inputs_by_kind` + `ck_job_image_params` enforce them per kind. The migration is additive; the downgrade drops only what it added.
- **The Library no longer sees new kinds.** AC-11 filters `kind='video'`, so image jobs are invisible in the Library until P2. That is a deliberate, testable cut, not an accident.
- **Two credit-cost sources.** `image_credit_cost` (server) and the client's `count × unit` (using server-provided units). The units come from the API, so only the multiplication is duplicated; the created job's `credit_cost` is authoritative and the page displays the response value after creation.
- **Moving the watcher touches spec 004.** Mitigated the way T-005-2 moved the guest runner and T-006-1 moved `usePresets`: behaviour is unchanged, the test moves with it, and only the import path changes in `useJobEvents`/`canvasPhase`.
- **`GET /jobs/{id}/events` is shared by both kinds.** It is owner-scoped by job id and status-only, so no kind filter is needed; if a future route changes that, both pages must be revisited.
- **SSE for a fast terminal job.** The mock/placeholder adapter finishes in milliseconds, so SSE may deliver `succeeded` before the first poll; the watcher's initial fetch + final fetch path already handles that (create-video's `mock` runs prove it).
