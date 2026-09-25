# Design 010: Reel & Still

**Spec:** `docs/specs/010-reel-and-still/spec.md` · **Visual source:** `DESIGN.md` (repo root) · **Task protocol:** `scripts/task` (T-042)

The backend changes **extend** the spec 003/009 core. They add no new machinery:
- a third `job.kind` (`sequence`);
- one child table (`job_sequence_clip`);
- one step kind (`stitch_video`);
- one worker branch;
- a handful of additive fields.

The frontend is rebuilt on top of the existing `apps/web/src/api/*` layer and its hooks.

## API contract (T-010-1 publishes it with 501 stubs; later tasks fill the bodies)
| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| POST | `/api/v1/sequence-jobs` | `SequenceJobCreateRequest` | 202 `SequenceJobCreatedResponse` | 401, 402 `InsufficientCreditsResponse`, 404 (clip or audio not found / not yours), 422 (ineligible clip, bad count, key used by another kind), 429 `LimitExceededResponse` |
| GET | `/api/v1/sequence-jobs/{job_id}` | none | 200 `SequenceJobResponse` | 401, 404 |
| GET | `/api/v1/credits/ledger?limit=10` (1–50) | none | 200 `LedgerListResponse` | 401 |
| POST | `/api/v1/uploads` (existing) | `content_type` gains `audio/mpeg`, `audio/mp4`, `audio/wav` | unchanged | unchanged |
| POST | `/api/v1/jobs` (existing) | unchanged schema; `input_asset_id` may now be the user's own ready `output_image` | unchanged | unchanged (404 for someone else's or a non-image asset) |
| GET | `/api/v1/jobs` (existing Library) | unchanged | items gain `images`, `clip_count`, `duration_ms`; `kind` may be `sequence` | unchanged |
| GET | `/api/v1/public/jobs/{job_id}` (existing share) | unchanged | gains `kind`, `image_urls`, `clip_count`, `duration_ms`; `preset_slug`/`preset_name` become nullable | unchanged |

SSE (`GET /jobs/{id}/events`) is unchanged. It is already kind-agnostic (`find_owned_job`).

### New and changed schemas (exact; T-010-1 writes these)
```python
# schemas/sequence_jobs.py (new)
SequenceTransition = Literal["cut", "crossfade", "fade_black"]

class SequenceClipIn(BaseModel):
    job_id: uuid.UUID
    transition_in: SequenceTransition = "cut"   # ignored for clips[0]; stored as "cut"

class SequenceJobCreateRequest(BaseModel):
    clips: list[SequenceClipIn] = Field(min_length=2, max_length=6)
    audio_asset_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=8, max_length=100)

class SequenceJobCreatedResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    clip_count: int

class SequenceClipResponse(BaseModel):
    position: int
    job_id: uuid.UUID
    transition_in: SequenceTransition
    thumbnail_url: str | None

class SequenceJobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    credit_cost: int
    clips: list[SequenceClipResponse]
    has_audio: bool
    video_url: str | None
    poster_url: str | None
    duration_ms: int | None
    generated_by: str | None
    error_message: str | None
    created_at: datetime

# schemas/credits.py (add)
LedgerKind = Literal["GRANT", "HOLD", "SETTLE", "RELEASE", "TOPUP"]
class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    kind: LedgerKind
    amount: int
    job_id: uuid.UUID | None
    created_at: datetime
class LedgerListResponse(BaseModel):
    items: list[LedgerEntryResponse]

# schemas/jobs.py (change)
JobKind = Literal["video", "image", "sequence"]
class LibraryImageResponse(BaseModel):
    asset_id: uuid.UUID
    url: str
class LibraryItemResponse(...):          # existing fields unchanged, plus:
    images: list[LibraryImageResponse] = []
    clip_count: int | None = None
    duration_ms: int | None = None

# schemas/uploads.py (change)
UploadContentType = Literal["image/jpeg", "image/png", "image/webp", "audio/mpeg", "audio/mp4", "audio/wav"]

# schemas/share.py (change)
class PublicJobResponse(BaseModel):
    id: uuid.UUID
    kind: JobKind = "video"
    status: JobStatus
    preset_slug: str | None
    preset_name: str | None
    poster_url: str | None
    video_url: str | None
    image_urls: list[str] = []
    clip_count: int | None = None
    duration_ms: int | None = None
    created_at: datetime
```
The `LedgerEntry` model's column names decide the field names above. If a column is named differently (for example `entry_id`), the schema keeps the names above and the service maps them.

## Data: migration `0007_sequences` (additive only)
- `ck_job_kind` becomes `kind IN ('video','image','sequence')`.
- `ck_job_inputs_by_kind` gains `OR (kind = 'sequence' AND preset_slug IS NULL AND input_asset_id IS NULL)`.
- `ck_job_image_params` gains `OR (kind = 'sequence' AND aspect_ratio IS NULL AND quality IS NULL AND image_count IS NULL)`.
- New `job.audio_asset_id UUID NULL REFERENCES asset(id)`, plus the check `ck_job_audio_sequence_only`: `audio_asset_id IS NULL OR kind = 'sequence'`.
- New `job.duration_ms INTEGER NULL`, plus the check `ck_job_duration_positive`: `duration_ms IS NULL OR duration_ms > 0`. It is written by the stitch step, and could be written by others later.
- `ck_asset_kind` gains `'input_audio'`.
- New table `job_sequence_clip`:

  | Column | Type | Rule |
  |---|---|---|
  | `job_id` | UUID NOT NULL | FK `job(id)` ON DELETE CASCADE |
  | `position` | SMALLINT NOT NULL | CHECK 0–5 |
  | `source_job_id` | UUID NOT NULL | FK `job(id)` |
  | `transition_in` | VARCHAR(16) NOT NULL | CHECK IN ('cut','crossfade','fade_black') |

  The primary key is `(job_id, position)`, and there's an index on `source_job_id`.
- `downgrade()` reverses all of it exactly.
- `domain/credit_rules.py`: `GUEST_PER_IP_DAILY = 30` (it was 5). No other rule changes.
- `domain/sequence_rules.py` (new) holds the constants every other file imports:
  - `SEQUENCE_CREDIT_COST = 1`, `MIN_CLIPS = 2`, `MAX_CLIPS = 6`
  - `TRANSITIONS = ("cut", "crossfade", "fade_black")`, `TRANSITION_SECONDS = 0.5`
  - `OUTPUT_WIDTH = 1280`, `OUTPUT_HEIGHT = 720`, `OUTPUT_FPS = 24`
  - `MUSIC_FADE_SECONDS = 1.0`, `POSTER_AT_SECONDS = 1.0`
  - `STITCH_STEP_KIND = "stitch_video"`, `STITCH_BACKEND = "ffmpeg"`
  - `MAX_AUDIO_BYTES = 10 * 1024 * 1024`

## Flow
**Create a sequence.** One transaction in `services/sequence_job_creation.create_sequence_job`, mirroring `image_job_creation`:
1. The web client posts `clips[]` (each with its transition), an optional `audio_asset_id` and a fresh idempotency key.
2. `lock_user_row`, then replay by idempotency key. A job of another kind with that key raises `IdempotencyKeyConflictError` (the existing class, reused), which becomes 422.
3. `enforce_creation_limits(session, user_id, is_paid_backend=False, paid_budget_cents=0)`, so the daily cap applies and the paid budget does not.
4. Validate the clips:
   - Each `job_id` must be the user's own (otherwise 404).
   - Each must be `kind == 'video'`, `status == 'succeeded'`, with `output_video_asset_id` set (otherwise 422).
   - Duplicates are allowed: the same clip twice is a legitimate edit.
   - `audio_asset_id`, if present, must be the user's own `input_audio` asset with status `ready` (otherwise 404).
5. Balance check against `SEQUENCE_CREDIT_COST` (402 if it falls short).
6. Writes:
   - `insert_sequence_job` (kind `sequence`, cost 1, `audio_asset_id`);
   - `insert_sequence_clips` (positions 0..n-1, `clips[0]` stored as `cut`);
   - `insert_job_step(job.id, "stitch_video")`;
   - a HOLD of −1;
   - `notify_job_event`;
   - commit, with the same IntegrityError race handling as the image path.

**Render.** The worker handles this in `services/stitch_runs.run_stitch_step`:
1. `run_claimed_step_for_kind` sends `stitch_video` to `run_stitch_step`. No model adapter and no fallback are involved.
2. `load_stitch_inputs` (in `repositories/stitch_inputs.py`) reads, in one session: the clips in position order, each with its source job's `output_video` asset `storage_key`; the transitions; and the audio asset's `storage_key`.
3. In a temp dir, while the lease is renewed concurrently, as in `image_generation_runs.generate_with_lease`:
   1. `storage.download_to_path` for each clip and the audio.
   2. `adapters/ffmpeg_stitcher.stitch_clips(...)` probes each clip's duration and builds the command with `adapters/stitch_filtergraph.build_stitch_command`. That command:
      - normalises every clip: `scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=24,format=yuv420p,settb=AVTB`;
      - folds the clips left to right: `cut` → `concat=n=2:v=1:a=0`; `crossfade` → `xfade=transition=fade:duration=0.5:offset=<acc-0.5>`; `fade_black` → `xfade=transition=fadeblack:…`;
      - handles audio: with music, `apad,atrim=0:<total>,afade=t=out:st=<total-1>:d=1`, encoded to AAC. Without music, `-an`, so clip audio is always dropped;
      - encodes with `libx264 -crf 23 -preset veryfast -pix_fmt yuv420p -movflags +faststart`.
   3. It extracts the poster at `min(1.0, total/2)` seconds.
4. Upload `users/{uid}/jobs/{job}/video.mp4` and `poster.jpg`. Then `complete_step_success(..., backend="ffmpeg", duration_ms=…)`, which writes the output assets, `succeeded`, `SETTLE 0` and `duration_ms`.
5. Any `GenerationError` or other exception → `complete_step_failure` (RELEASE, user-safe message: "Render failed. Your credit was refunded."). A lost lease → write nothing, exactly as in the other runs.
6. `generated_by = "ffmpeg"` keeps sequences out of `sum_paid_spend_cents`, which only counts paid backends.

**Still → clip.** `services/job_creation.create_job` accepts `asset.kind in ("input_image", "output_image")`, with the same owner and `ready` checks. The worker already downloads by `storage_key`, so nothing else changes.

**Web.**
1. `/studio` reads `?item=` and `?tab=`.
2. The rail is `useLibrary`, refreshed whenever an active job reaches a terminal status.
3. The stage renders the selected Library item, or the active job's SSE phase.
4. Composer tabs:
   - **Still** is the image-create feature.
   - **Clip** is the create-video feature, which can be seeded with `{assetId, url}` by "Animate this".
   - **Sequence** is the new sequence feature. Its draft (an ordered array of clips and transitions, plus the audio) lives in `StudioPage` and is passed down as props, so the stage's "Add to sequence" and the Sequence tab share it.
5. **Aspect eligibility** is computed client-side from each clip poster's `naturalWidth/naturalHeight`. The backend letterboxes anyway, so this is purely presentational.

## Files (each ≤ 200 lines; owner task in brackets)
### API
| File | New/Edit | Responsibility |
|---|---|---|
| `apps/api/app/schemas/sequence_jobs.py` | New [1] | request/response models above |
| `apps/api/app/schemas/{credits,jobs,uploads,share}.py` | Edit [1] | the additive fields above |
| `apps/api/app/routers/sequence_jobs.py` | New [1 stub → 3 body] | thin HTTP for the two sequence routes |
| `apps/api/app/routers/credits.py` | Edit [1 stub → 4 body] | `GET /credits/ledger` |
| `apps/api/app/main.py` | Edit [1] | include the sequence router |
| `packages/contracts/openapi.json` | Regenerated [1, and any later task that changes schemas] | the contract |
| `apps/api/migrations/versions/0007_sequences.py` | New [2] | the migration above |
| `apps/api/app/models/{job,asset}.py`, `models/job_sequence_clip.py`, `models/__init__.py` | Edit/New [2] | ORM for the migration |
| `apps/api/app/domain/sequence_rules.py` | New [2] | constants |
| `apps/api/app/domain/credit_rules.py` | Edit [2] | `GUEST_PER_IP_DAILY = 30` |
| `apps/api/app/repositories/sequence_jobs.py` | New [3] | insert job and clips, find owned sequence, find clip jobs for validation, list clips with thumbnails' asset ids, count clips by job ids |
| `apps/api/app/services/sequence_job_creation.py` | New [3] | the create use case |
| `apps/api/app/services/sequence_job_views.py` | New [3] | the read use case → `SequenceJobResponse` |
| `apps/api/app/services/job_creation.py` | Edit [4] | accept `output_image` input |
| `apps/api/app/services/uploads.py` | Edit [4] | audio types → `input_audio` kind and extensions (`mp3`, `m4a`, `wav`) |
| `apps/api/app/repositories/ledger.py`, `services/credits.py` | Edit [4] | `list_user_ledger_entries`, `read_ledger` |
| `apps/api/app/services/job_views.py` + `services/library_media.py` (new) | Edit/New [4] | move the image-url lookup out (`job_views.py` is 179 lines), add `images`, `clip_count`, `duration_ms` |
| `apps/api/app/services/share_views.py`, `services/share_html.py` | Edit [4] | the sequence and still share fields; OG title "Reel & Still" |
| `apps/api/app/adapters/ffmpeg_process.py` | New [6] | `run_ffmpeg(args)`, `probe_duration_seconds(path)` (async subprocess, `GenerationError` on failure) |
| `apps/api/app/adapters/stitch_filtergraph.py` | New [6] | pure `build_stitch_command(...) -> (argv, total_seconds)` |
| `apps/api/app/adapters/ffmpeg_stitcher.py` | New [6] | `stitch_clips(...) -> StitchResult(video_path, poster_path, duration_ms)` |
| `apps/api/app/repositories/stitch_inputs.py` | New [6] | `load_stitch_inputs(session, job_id)` |
| `apps/api/app/services/stitch_runs.py` | New [6] | `run_stitch_step` (lease, download, stitch, upload, complete) |
| `apps/api/app/services/step_completion.py`, `repositories/jobs.py` | Edit [6] | optional `duration_ms` through `complete_step_success` → `transition_job_status` |
| `apps/api/app/worker.py` | Edit [6] | dispatch `stitch_video` |

### Web (`apps/web/src`)
| File(s) | New/Edit | Responsibility |
|---|---|---|
| `styles.css`, `index.html`, `ui/*` (Button, ButtonLink, buttonStyles, EmptyState, ProgressBar, Toast, GenerationBadge), `ui/BrandMark.tsx`, `ui/AppShell.tsx`, `ui/Skeleton.tsx`, `ui/Tabs.tsx`, `ui/Popover.tsx` | Edit/New [5] | tokens (light and dark), fonts, brand, top bar, primitives |
| `App.tsx`, `features/studio/*`, `api/studioContracts.ts`, `api/jobProgress.ts`, `ui/CreditsPopoverContext.tsx`, `ui/usePrefersReducedMotion.ts`, deleting `features/library/*` and `features/explore/*` | Edit/New/Delete [7] | routes and redirects, the studio grid, rail, stage, tab host, sequence-draft state, the popover-open context |
| `features/image-create/*`, `features/create-video/*` | Edit [8] | the compact Still and Clip composers, "Animate this" seeding, backend captions, removing `SessionHistoryStrip`/`HowItWorks` |
| `features/sequence/*`, `api/sequenceJobs.ts`, `api/audioUpload.ts` | New [9] | the Sequence tab: strip, transitions, music, eligibility, render, progress |
| `features/start/*` | New [10] | the start page |
| `features/share/*` | Edit [10] | the share viewer for all three kinds |
| `features/credits/*`, `api/ledger.ts`, `api/credits.ts` | Edit/New [11] | the credits button and popover (balance, demo top-up, ledger) |

## Reused
- The ledger, holds and settles: `insert_ledger_entry`, `sum_user_balance`, `hold_amount`, `lock_user_row`.
- Job creation: `enforce_creation_limits`, `find_job_by_idempotency_key`, `insert_job_step`, `notify_job_event`, `IdempotencyKeyConflictError`, `InsufficientCreditsError`.
- The worker: `claim_step`, the lease reaper, `renew_lease_until_lost`, `complete_step_success`, `complete_step_failure`, `ObjectStorage.download_to_path` / `upload_from_path`, `build_asset_url`.
- The contract tooling: `scripts/export-openapi` and the CI sync check.
- Web: `api/client.ts`, `useJobEvents`, `jobStatusWatcher`, `useGuestSessionRunner`, `useLibrary`, `useCreditBalance`/`useCreditsPage`, `usePresets`, `webMedia` (preset preview media for the start page), the create-video hooks (`useCreateJob`, `useImageUpload`, `useActiveJob`, `usePresetSelection`, `useClipboardImagePaste`, `usePrefersReducedMotion`), and `useImageJob`.

## Architecture and standards check
- Routers stay thin. Services own the transactions. Repositories hold no rules. The state machine is untouched: sequences use the same job statuses.
- Ports and adapters only at real boundaries. ffmpeg is an external process, so it gets an adapter module. It gets **no** `Protocol`, because there's one implementation.
- **Rule of two:** `ffmpeg_process.py` becomes the shared runner. Migrating `local_motion_adapter` and `modal_adapter` onto it is **out of scope** (logged as a follow-up), so they stay untouched.
- **Web:** a feature never imports another feature's internals. `features/studio` imports only each feature's public entry component (`StillComposer`, `ClipComposer`, `SequenceComposer`, `CreditsButton`). Shared state crosses through props or `ui/CreditsPopoverContext.tsx`.

## Risks
- **xfade and duration drift:** `xfade` needs exact input durations, so the stitcher probes rather than assuming 5 s. The tests cover mixed 960×544 and 1280×720 inputs.
- **Shared dev DB races** (STATUS BROKEN): run DB-backed verifies one at a time across worktrees.
- **Visual churn breaking tested hooks:** UI tasks may not edit hooks or `api/` files outside their own list. The hook tests must stay green.
- **Font licensing and load:** all three fonts are on Google Fonts under the OFL, loaded with `display=swap`.
