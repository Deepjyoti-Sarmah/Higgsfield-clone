# Design 003: Generation core

**Spec:** `docs/specs/003-generation-core/spec.md` (APPROVED)
**Contract:** already published. Schemas are in `apps/api/app/schemas/{presets,uploads,jobs,credits}.py`, 501 stubs in `apps/api/app/routers/{presets,uploads,jobs,credits}.py`, and `packages/contracts/openapi.json` is regenerated.
**Frozen:** the schemas files are the contract. No T-003-k task edits them. A contract change goes back to the orchestrator.

## AC → design → task map
| AC | Design section | Task |
|---|---|---|
| AC-1 Presets | Contract, Data `preset`, Presets catalog | T-003-1 (catalog + seed), T-003-3 (endpoint) |
| AC-2 Uploads | Contract, Data `asset`, Storage | T-003-1 (storage adapter), T-003-2 (asset repo), T-003-3 (endpoints) |
| AC-3 Create job | Contract, Data `job`/`ledger_entry`, Flow 1 | T-003-2 (repos), T-003-4 (service + router) |
| AC-4 Worker | Flow 2–4, ModelAdapter | T-003-2 (claim SQL), T-003-5 (worker) |
| AC-5 Reaper | Flow 5 | T-003-2 (SQL), T-003-5 (reaper service) |
| AC-6 Progress | Flow 6 (NOTIFY + SSE fan-out) | T-003-4 |
| AC-7 Credits | Data `ledger_entry`, Credit rules | T-003-1 (rules), T-003-2 (ledger repo), T-003-3 (endpoint + guest grant) |
| AC-8 Backends | ModelAdapter, Presets catalog (recipes) | T-003-6 |
| AC-9 Tests | Test plan | T-003-2, T-003-3, T-003-4, T-003-5, T-003-6; end-to-end T-003-7 |

## API contract
All paths are under `/api/v1`. Auth means the `session` cookie from spec 002, via `require_current_user`. 401 bodies are `ErrorResponse {detail}`.

| Method | Path | Auth | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/presets` | none | — | 200 `PresetListResponse {presets: PresetResponse[]}`; `PresetResponse {slug, name, description, category: camera\|cinematic\|dynamic, credit_cost, preview_url: str\|null}` | — |
| POST | `/uploads` | yes | `UploadCreateRequest {content_type: image/jpeg\|image/png\|image/webp, byte_size: 1..10485760}` | 201 `UploadCreateResponse {asset_id, upload_url, upload_method:"PUT", upload_headers: {"Content-Type": …}, expires_at}` | 401, 422 (type/size, from pydantic) |
| POST | `/uploads/{asset_id}/complete` | yes | — | 200 `AssetResponse {id, kind, status, content_type, byte_size, url}` | 401; 404 unknown or not the caller's; 409 object not in storage yet; 422 stored object > 10 MB or size ≠ declared (the object is deleted, the asset stays `pending`) |
| POST | `/jobs` | yes | `JobCreateRequest {preset_slug, input_asset_id, prompt?: ≤500 chars, idempotency_key: 8..100 chars}` | 202 `JobCreatedResponse {id, status, credit_cost}` | 401; **402 `InsufficientCreditsResponse {detail, balance, required}`** (top-level, not nested in `detail`); 404 unknown/inactive preset or asset not the caller's `input_image`; 409 asset still `pending`; 422 |
| GET | `/jobs/{job_id}` | yes | — | 200 `JobResponse {id, status, preset_slug, preset_name, prompt, credit_cost, input_asset_id, input_image_url, video_url, poster_url, error_message, created_at, started_at, finished_at}` | 401; 404 unknown or not the owner |
| GET | `/jobs/{job_id}/events` | yes | — | 200 `text/event-stream`, frames below | 401; 404 unknown or not the owner (plain JSON, checked before the stream opens) |
| GET | `/credits` | yes | — | 200 `CreditsResponse {balance}` | 401 |

**Rules the contract implies:**
- **Idempotent create:** a repeat of `(user, idempotency_key)` returns **202** with the existing job's `id`, current `status` and `credit_cost`. It never creates a second hold, even if the body differs (documented; not an error).
- **URLs** (`url`, `input_image_url`, `video_url`, `poster_url`) are presigned GETs valid for `DOWNLOAD_URL_TTL_SECONDS` (3600), minted on every read. When `S3_PUBLIC_BASE_URL` is set, they're `{S3_PUBLIC_BASE_URL}/{key}` instead. `null` until the asset is `ready`.
- **402 body** is sent with `JSONResponse(status_code=402, content=InsufficientCreditsResponse(...).model_dump())`, so the UI reads `balance` and `required` at the top level.
- **SSE frames** (`JobStatusEvent` is the `data` JSON; ids and a status only, never the full job):
  ```
  retry: 3000

  event: status
  data: {"job_id":"…","status":"queued"}

  : ping

  event: status
  data: {"job_id":"…","status":"running"}

  event: status
  data: {"job_id":"…","status":"succeeded"}
  ```
  - The first `status` frame is sent immediately on connect (the current status). A frame is only sent when the status differs from the last one sent.
  - The server closes the stream after a terminal status (`succeeded`/`failed`). The client then calls `GET /jobs/{id}` for URLs and `error_message`.
  - Response headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
  - A job moved back to `queued` by the reaper produces a `queued` frame; clients must accept it.

## Data
Migrations (Alembic, style of `0001_create_app_user.py`): **`0002_create_generation_tables`** (down_revision `0001`) and **`0003_seed_preset_catalog`** (down_revision `0002`).
The migrations are the DDL source of truth; the SQLAlchemy models mirror columns, FKs and checks. All ids are `uuid default gen_random_uuid()`, and all times are `timestamptz`.

### `preset`
| Column | Type | Notes |
|---|---|---|
| `slug` | `varchar(64)` PK | |
| `name` | `varchar(80)` not null | |
| `description` | `varchar(240)` not null | |
| `category` | `varchar(16)` not null | check in (`camera`, `cinematic`, `dynamic`) |
| `credit_cost` | `int` not null | check `> 0` |
| `preview_url` | `text` null | filled by spec 006 |
| `sort_order` | `int` not null | |
| `is_active` | `bool` not null default true | |
| `created_at` | `timestamptz` not null default now() | |

`0003` inserts the 12 rows from `app/domain/preset_catalog.py` with `INSERT … ON CONFLICT (slug) DO UPDATE`; downgrade deletes those slugs.

### `asset`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` not null FK `app_user.id` | |
| `kind` | `varchar(16)` not null | check in (`input_image`, `output_video`, `output_poster`) |
| `status` | `varchar(16)` not null | check in (`pending`, `ready`) |
| `storage_key` | `text` not null | unique `uq_asset_storage_key` |
| `content_type` | `varchar(64)` not null | |
| `byte_size` | `bigint` null | null while pending |
| `created_at`, `updated_at` | `timestamptz` not null default now() | |

Index `ix_asset_user_created (user_id, created_at desc)`.

### `job`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` not null FK `app_user.id` | |
| `preset_slug` | `varchar(64)` not null FK `preset.slug` | |
| `input_asset_id` | `uuid` not null FK `asset.id` | |
| `prompt` | `varchar(500)` null | |
| `idempotency_key` | `varchar(100)` not null | |
| `status` | `varchar(16)` not null | check in (`queued`, `running`, `succeeded`, `failed`) |
| `credit_cost` | `int` not null | copied from the preset at creation |
| `output_video_asset_id`, `output_poster_asset_id` | `uuid` null FK `asset.id` | |
| `error_message` | `varchar(300)` null | user-safe text only |
| `created_at`, `updated_at` | `timestamptz` not null default now() | |
| `started_at`, `finished_at` | `timestamptz` null | |

- **`uq_job_user_idempotency_key` UNIQUE (`user_id`, `idempotency_key`)** (invariant 3).
- `ix_job_user_created (user_id, created_at desc)` for the library (spec 005).

### `job_step` (the queue)
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `job_id` | `uuid` not null FK `job.id` ON DELETE CASCADE | |
| `kind` | `varchar(32)` not null | `generate_video` for now |
| `status` | `varchar(16)` not null | same check as `job.status` |
| `attempt` | `int` not null default 0 | incremented by each claim |
| `lease_owner` | `varchar(100)` null | worker id `"{hostname}:{pid}:{uuid4 hex[:8]}"` |
| `lease_expires_at` | `timestamptz` null | |
| `backend` | `varchar(32)` null | adapter name that ran it |
| `last_error` | `text` null | internal detail, never shown to users |
| `created_at`, `updated_at` | `timestamptz` not null default now() | |
| `started_at`, `finished_at` | `timestamptz` null | |

- `uq_job_step_job_kind` UNIQUE (`job_id`, `kind`).
- **`ix_job_step_claimable` ON (`created_at`) WHERE `status = 'queued'`** (partial index for claiming).
- `ix_job_step_lease_expiry` ON (`lease_expires_at`) WHERE `status = 'running'` (partial index for the reaper).

### `ledger_entry`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` not null FK `app_user.id` | |
| `kind` | `varchar(16)` not null | check in (`GRANT`, `HOLD`, `SETTLE`, `RELEASE`, `TOPUP`) |
| `amount` | `int` not null | signed; see sign check |
| `job_id` | `uuid` null FK `job.id` | |
| `created_at` | `timestamptz` not null default now() | |

- **Sign check `ck_ledger_entry_amount_sign`:** `(kind = 'HOLD' AND amount < 0) OR (kind = 'SETTLE' AND amount = 0) OR (kind IN ('GRANT','TOPUP','RELEASE') AND amount > 0)`.
- **Job link check `ck_ledger_entry_job_link`:** `(kind IN ('HOLD','SETTLE','RELEASE')) = (job_id IS NOT NULL)`.
- `uq_ledger_entry_guest_grant` UNIQUE (`user_id`) WHERE `kind = 'GRANT'` (one-time grant).
- `uq_ledger_entry_job_hold` UNIQUE (`job_id`) WHERE `kind = 'HOLD'` (no second hold).
- `uq_ledger_entry_job_resolution` UNIQUE (`job_id`) WHERE `kind IN ('SETTLE','RELEASE')` (a hold resolves exactly once).
- `ix_ledger_entry_user (user_id)`.

**Why SETTLE is 0:** balance = `SUM(amount)` (invariant 2). The HOLD already took −cost, so SETTLE only marks the hold as spent, and RELEASE gives +cost back.

### Credit rules and job states (the "one config place")
- `app/domain/credit_rules.py`: `GUEST_GRANT_CREDITS = 60`, `VIDEO_CREDIT_COST = 20`, `MAX_STEP_ATTEMPTS = 2`, `LedgerKind` literal, and `hold_amount(cost) -> -cost`, `release_amount(cost) -> +cost`.
- `app/domain/job_states.py`: `JobStatus` literal, `TERMINAL_STATUSES`, `ALLOWED_TRANSITIONS = {queued: {running, failed}, running: {succeeded, failed, queued}, succeeded: {}, failed: {}}` (`running → queued` is the reaper's re-queue only), `can_transition(from, to)`, `statuses_allowed_before(to) -> frozenset`. Job and step share these statuses.

## Flow
### 1. Create job (API, ONE transaction; invariant 1)
`services/job_creation.py::create_job(session, user_id, request) -> JobCreation` (JobCreation = the job, or an `InsufficientCredits(balance, required)` result; typed errors `PresetNotFound`, `InputAssetNotFound`, `InputAssetNotReady`).
1. `SELECT id FROM app_user WHERE id = :user_id FOR UPDATE` (`repositories/users.lock_user_row`). This serialises one user's credit changes, so two parallel creates can't both pass the balance check, and a same-key retry waits for the first to commit.
2. `find_job_by_idempotency_key(user_id, key)`. If found: return it (no hold, no insert, no notify).
3. `find_active_preset(slug)` → `PresetNotFound`. `find_user_asset(user_id, input_asset_id)` with `kind = 'input_image'` → `InputAssetNotFound`; `status != 'ready'` → `InputAssetNotReady`.
4. `balance = sum_user_balance(user_id)`. If `balance < preset.credit_cost`: roll back, return `InsufficientCredits` → router sends 402.
5. `insert_job(status='queued', credit_cost=preset.credit_cost)`, `insert_job_step(job_id, 'generate_video', status='queued')`, `insert_ledger_entry(kind='HOLD', amount=-cost, job_id)`.
6. `notify_job_event(job_id)` → `SELECT pg_notify('job_events', :payload)`. Postgres delivers it only on commit.
7. `COMMIT`. If the commit raises `IntegrityError` on `uq_job_user_idempotency_key` (a race that got past the lock), roll back and return the existing job.

### 2. Claim (worker, short transaction)
`repositories/job_steps.claim_next_queued_step(session, worker_id, lease_seconds)`:
```sql
UPDATE job_step
SET status = 'running', attempt = attempt + 1, lease_owner = :worker_id,
    lease_expires_at = now() + make_interval(secs => :lease_seconds),
    started_at = coalesce(started_at, now()), updated_at = now()
WHERE id = (
  SELECT id FROM job_step
  WHERE status = 'queued'
  ORDER BY created_at
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
RETURNING id, job_id, kind, attempt;
```
In the same transaction (`services/step_claiming.py`): `transition_job_status(job_id, 'running', allowed_from={'queued'}, started_at=now())`, `notify_job_event(job_id)`, commit. The lease is `WORKER_LEASE_SECONDS` = 300. An idle worker sleeps `WORKER_POLL_SECONDS` = 1.0 between empty claims.

### 3. Run + heartbeat (worker, no transaction held)
`services/generation_runs.py::run_claimed_step(...)`:
1. Load job + preset + input asset (short read). Download the input to a temp dir with `ObjectStorage.download_to_path`.
2. Start `renew_lease_until_done` as an `asyncio` task: every `lease_seconds / 5` (60s) run
   `UPDATE job_step SET lease_expires_at = now() + make_interval(secs => :lease_seconds), updated_at = now() WHERE id = :step_id AND lease_owner = :worker_id AND status = 'running'`.
   Rowcount 0 means the lease was lost: cancel the adapter call and exit without writing anything.
3. `await adapter.generate_video(GenerationRequest(...))`, bounded by `asyncio.wait_for(…, GENERATION_TIMEOUT_SECONDS = 240)`, so a run always ends before its lease can expire.
4. On success, upload `video.mp4` and `poster.jpg` (`upload_from_path`) to the output keys, then run Flow 4a. On `GenerationError`, Flow 4b with `error.user_message`. On any other exception or timeout, Flow 4b with `"Generation failed. Your credits were refunded."` and log the traceback.

### 4. Finish (worker, ONE transaction each)
Both start with `finish_step(step_id, worker_id, to_status)`: `UPDATE job_step SET status=:to, finished_at=now(), lease_owner=NULL, lease_expires_at=NULL, backend=:backend, last_error=:err WHERE id=:step_id AND lease_owner=:worker_id AND status='running'`. **Rowcount 0: the lease was lost (reaped), so roll back and write nothing.**
- **4a success:** insert 2 `asset` rows (`output_video` `video/mp4`, `output_poster` `image/jpeg`, `ready`, byte sizes) → `transition_job_status(job_id, 'succeeded', allowed_from={'running'}, output ids, finished_at)` → `insert_ledger_entry('SETTLE', 0, job_id)` → notify → commit.
- **4b failure:** `transition_job_status(job_id, 'failed', allowed_from={'running'}, error_message, finished_at)` → `insert_ledger_entry('RELEASE', +job.credit_cost, job_id)` → notify → commit.

### 5. Reaper (worker loop, every `WORKER_REAPER_SECONDS` = 30)
`repositories/job_steps.lock_expired_steps(session, limit=20)`:
```sql
SELECT s.id, s.job_id, s.attempt, j.user_id, j.credit_cost
FROM job_step s JOIN job j ON j.id = s.job_id
WHERE s.status = 'running' AND s.lease_expires_at < now()
ORDER BY s.lease_expires_at
LIMIT :limit
FOR UPDATE OF s SKIP LOCKED;
```
For each row, in the same transaction (`services/lease_reaper.py`):
- **`attempt < MAX_STEP_ATTEMPTS` (first expiry):** `requeue_step` (`status='queued', lease_owner=NULL, lease_expires_at=NULL, last_error='lease expired'`), `transition_job_status(job, 'queued', allowed_from={'running'})`, notify.
- **Otherwise (second expiry):** `fail_step` (`status='failed', finished_at=now(), last_error='lease expired twice'`), `transition_job_status(job, 'failed', allowed_from={'running'}, error_message='Generation timed out. Your credits were refunded.')`, `RELEASE +credit_cost`, notify.

Commit once for the batch. SKIP LOCKED lets two workers reap in parallel without touching the same row.

### 6. NOTIFY and SSE fan-out (API; invariant 4)
- **Channel** `job_events`. **Payload** `{"job_id":"<uuid>"}` (ids only, ~50 bytes, far below the 8000-byte limit). Built by `repositories/jobs.notify_job_event` with `json.dumps`, sent as a bind parameter.
- **`services/job_event_broker.py::JobEventBroker`** (one per API process, created in the `main.py` lifespan and stored on `app.state.job_event_broker`):
  - `start()` opens ONE dedicated connection (`engine.connect()` → `await conn.get_raw_connection()` → `.driver_connection` is the asyncpg connection) and runs `add_listener("job_events", on_notify)`. It isn't taken from request sessions and is never returned to the pool while the process lives.
  - `on_notify` parses `job_id` and, for each subscribed `asyncio.Queue(maxsize=1)` of that job, calls `put_nowait(None)` unless the queue is full (wake-ups coalesce).
  - `subscribe(job_id) -> asyncio.Queue[None]`, `unsubscribe(job_id, queue)` keep `dict[uuid.UUID, set[asyncio.Queue[None]]]`; empty sets are removed.
  - **Connection loss:** `add_termination_listener` triggers a reconnect loop (1s, 2s, 4s … max 30s). After reconnecting, it wakes **every** queue so each stream re-reads its status (nothing missed).
  - `stop()` closes the connection on shutdown.
- **`services/job_event_stream.py::stream_job_status_events(job_id, broker, session_maker) -> AsyncIterator[str]`:**
  1. `queue = broker.subscribe(job_id)` **before** the first read (no gap between read and subscribe).
  2. Yield `retry: 3000\n\n`. Read the status in a short session and yield the first `status` frame. If it's terminal, stop.
  3. Loop: `await asyncio.wait_for(queue.get(), timeout=20)`. On timeout yield `: ping\n\n`. On a wake-up re-read the status, and yield a frame if it changed. Stop after a terminal status.
  4. `finally: broker.unsubscribe(job_id, queue)` (runs on client disconnect too, when Starlette cancels the generator).
- The router checks ownership first (`find_user_job` → 404), then returns `EventStreamResponse(stream_job_status_events(...))` (the class already exists in `routers/jobs.py`).
- The stream uses its own short sessions from `request.app.state.session_maker`, **not** the request's `get_session` session, so no pooled connection is held for the stream's lifetime.

## ModelAdapter (strategy; `app/adapters/model_adapter.py`)
```python
@dataclass(frozen=True)
class GenerationRequest:
    job_id: uuid.UUID
    preset_slug: str
    prompt: str | None
    input_image_path: Path      # local copy downloaded by the worker
    input_image_url: str        # presigned GET, for remote backends
    work_dir: Path              # adapter writes outputs here

@dataclass(frozen=True)
class GenerationResult:
    video_path: Path            # h264 mp4, faststart
    poster_path: Path           # jpeg
    width: int
    height: int
    duration_ms: int

class GenerationError(Exception):
    def __init__(self, user_message: str) -> None: ...   # .user_message is safe to show

class BackendNotConfiguredError(GenerationError): ...

class ModelAdapter(Protocol):
    name: str
    async def generate_video(self, request: GenerationRequest) -> GenerationResult: ...
```
| Backend (`GENERATION_BACKEND`) | Class · file | Behaviour |
|---|---|---|
| `local-motion` (default) | `LocalMotionAdapter` · `adapters/local_motion_adapter.py` | ffprobe the input → pick the canvas → run the preset's recipe with ffmpeg (`asyncio.create_subprocess_exec`, no shell) → poster from frame 0. ffmpeg exit ≠ 0 → `GenerationError("We couldn't animate this image. Try another one.")`; unknown slug → `GenerationError("This preset isn't available.")` |
| `mock` (tests, kill switch) | `MockModelAdapter` · `adapters/mock_model_adapter.py` | copies `adapters/fixtures/mock-video.mp4` (1s, 64×64, h264) and `mock-poster.jpg` into `work_dir`; returns immediately. `MOCK_GENERATION_FAILS=true` → raises `GenerationError("Mock failure")` |
| `modal` | `ModalAdapter` · `adapters/modal_adapter.py` | `MODAL_ENDPOINT_URL` empty → `BackendNotConfiguredError("modal backend not configured: set MODAL_ENDPOINT_URL")`; otherwise `GenerationError("modal backend not implemented yet")`. No network calls |
| `openrouter` | `OpenRouterAdapter` · `adapters/openrouter_adapter.py` | `OPENROUTER_API_KEY` empty → `BackendNotConfiguredError("openrouter backend not configured: set OPENROUTER_API_KEY")`; otherwise `GenerationError("openrouter backend not implemented yet")`. No network calls |

`adapters/backend_selection.py::select_model_adapter(settings) -> ModelAdapter` maps the setting to a class. `worker.py` calls it once at startup and logs the chosen name.
The modal → openrouter fallback and the `PAID_BUDGET_CENTS` guard (invariant 5) arrive with the real remote adapters; they aren't part of this spec.

## Presets catalog (12) and local-motion recipes
`app/domain/preset_catalog.py` holds `PresetDefinition(slug, name, description, category, credit_cost=VIDEO_CREDIT_COST, sort_order)`. `app/adapters/motion_recipes.py` holds `MotionRecipe(zoom, x, y, margin=1.0, rotate=None, blur_frames=None)` keyed by slug. A test asserts both have exactly the same slugs.

**Canvas:** from the input's `w/h`: `> 1.2` → 1280×720; `< 1/1.2` → 720×1280; otherwise 720×720 (≤720p).
**Constants:** `SUPERSAMPLE = 4`, `FRAMES = 120`, `FPS = 24` (5.000s). `E` = smoothstep `(on/119)*(on/119)*(3-2*(on/119))`. `CX = iw/2-(iw/zoom/2)`, `CY = ih/2-(ih/zoom/2)`.

**Filter chain** (one `-vf` argv element; expressions are single-quoted inside the filter string so their commas survive). With `ZW = even(W*margin)`, `ZH = even(H*margin)`:
```
scale={ZW*4}:{ZH*4}:force_original_aspect_ratio=increase,crop={ZW*4}:{ZH*4},setsar=1,
zoompan=z='{zoom}':x='{x}':y='{y}':d=120:s={ZW}x{ZH}:fps=24,
[rotate=a='{rotate}':ow=iw:oh=ih:c=black,crop={W}:{H},]      # only when rotate is set
[tmix=frames={blur_frames},]                                  # only when blur_frames is set
format=yuv420p
```
**Commands:**
```
ffmpeg -y -loglevel error -i input -vf "<chain>" -frames:v 120 -r 24 -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -movflags +faststart -an video.mp4
ffmpeg -y -loglevel error -i video.mp4 -frames:v 1 -q:v 3 poster.jpg
```
| # | slug | name | category | zoom | x | y | extra |
|---|---|---|---|---|---|---|---|
| 1 | `dolly-in` | Dolly In | camera | `1+0.35*E` | `CX` | `CY` | |
| 2 | `dolly-out` | Dolly Out | camera | `1.35-0.35*E` | `CX` | `CY` | |
| 3 | `pan-left` | Pan Left | camera | `1.2` | `(iw-iw/zoom)*(1-E)` | `CY` | |
| 4 | `pan-right` | Pan Right | camera | `1.2` | `(iw-iw/zoom)*E` | `CY` | |
| 5 | `tilt-up` | Tilt Up | camera | `1.2` | `CX` | `(ih-ih/zoom)*(1-E)` | |
| 6 | `ken-burns` | Ken Burns | cinematic | `1.1+0.2*E` | `(iw-iw/zoom)*(0.2+0.6*E)` | `(ih-ih/zoom)*(0.2+0.6*E)` | |
| 7 | `orbit-push` | Orbit Push | cinematic | `1.05+0.25*E` | `CX` | `CY` | margin 1.1, rotate `-0.035+0.07*n/119` |
| 8 | `slow-drift` | Slow Drift | cinematic | `1.08+0.08*E` | `(iw-iw/zoom)*(0.3+0.4*E)` | `(ih-ih/zoom)*(0.6-0.2*E)` | |
| 9 | `crash-zoom` | Crash Zoom | dynamic | `1+0.5*(1-pow(1-min(on/30,1),3))+0.1*on/119` | `CX` | `CY` | |
| 10 | `whip-pan` | Whip Pan | dynamic | `1.25` | `(iw-iw/zoom)/(1+exp(-(on-60)/5))` | `CY` | blur_frames 4 |
| 11 | `handheld` | Handheld | dynamic | `1.1` | `(iw-iw/zoom)*(0.5+0.15*sin(on/6.3)+0.08*sin(on/2.9+1.3))` | `(ih-ih/zoom)*(0.5+0.15*sin(on/7.7+0.5)+0.08*sin(on/3.7))` | |
| 12 | `spiral-in` | Spiral In | dynamic | `1+0.4*E` | `CX` | `CY` | margin 1.25, rotate `0.105*E` with `on` → `n` |

**Descriptions** (≤240 chars, shown in 004): 1 "Glide toward the subject for a slow, cinematic reveal." · 2 "Pull back to reveal the whole scene." · 3 "Sweep the frame smoothly to the left." · 4 "Sweep the frame smoothly to the right." · 5 "Rise from the bottom of the frame to the top." · 6 "Slow push across the image, the classic documentary move." · 7 "Push in while the camera arcs slightly around the subject." · 8 "A barely-there diagonal float that brings stills to life." · 9 "A punchy snap zoom straight into the subject." · 10 "A fast, motion-blurred swing across the frame." · 11 "Subtle shake, like a camera held by hand." · 12 "Twist inward while zooming for a dramatic entrance."

**Checked by T-003-0 on ffmpeg 7.1.4** (1600×1000 jpg and 900×1400 png, `testsrc2`): all 24 renders are h264, 120 frames, 24 fps, 5.000s, `moov` before `mdat`, 0.7–2.8s each on 12 cores. Rotated presets have no black corners on any frame (lowest corner luma max 76).

## Storage (`app/adapters/object_storage.py`; S3-compatible: MinIO locally, R2 later)
```python
class ObjectStorage(Protocol):
    def create_upload_url(self, key: str, content_type: str, expires_seconds: int) -> str: ...
    def create_download_url(self, key: str, expires_seconds: int) -> str: ...
    async def read_object_size(self, key: str) -> int | None: ...      # None when missing
    async def download_to_path(self, key: str, path: Path) -> None: ...
    async def upload_from_path(self, key: str, path: Path, content_type: str) -> None: ...
    async def delete_object(self, key: str) -> None: ...
```
- **`S3ObjectStorage`** (`adapters/s3_object_storage.py`): boto3 `s3` client (`endpoint_url`, keys, `region_name=S3_REGION`, `signature_version="s3v4"`, path-style addressing). Presigning is local CPU work; network calls go through `asyncio.to_thread`. Presigned PUT signs `ContentType`, so `upload_headers` = `{"Content-Type": content_type}`.
- **`InMemoryObjectStorage`** (`tests/fakes/in_memory_object_storage.py`): the test double used by every API/worker test via `app.dependency_overrides[get_object_storage]`. Upload URLs are `memory://{key}`; tests call `put_bytes(key, data)` to simulate the browser PUT.
- **URL helper:** `adapters/object_storage.py::build_asset_url(storage, key, public_base_url, expires_seconds) -> str` returns `{public_base_url}/{key}` when the base is set, otherwise a presigned GET. Used by uploads (T-003-3) and job views (T-003-4), so it lives in the T-003-1 file both import.
- **Dependency:** `app/storage_dependencies.py::get_object_storage() -> ObjectStorage`, `lru_cache`d like `get_settings`, which builds `S3ObjectStorage(get_settings())`. The worker calls the same function.
- **Key layout:** `users/{user_id}/inputs/{asset_id}.{jpg|png|webp}`, `users/{user_id}/jobs/{job_id}/video.mp4`, `users/{user_id}/jobs/{job_id}/poster.jpg`. Output keys are deterministic, so a re-queued run overwrites rather than leaks.
- **TTLs:** `UPLOAD_URL_TTL_SECONDS` = 900, `DOWNLOAD_URL_TTL_SECONDS` = 3600.
- **Local:** `docker-compose.yml` gets a MinIO healthcheck (`mc ready local`) and a one-shot `minio-init` service (`minio/mc`) that runs `mc mb --ignore-existing local/media` and `mc anonymous set none local/media`.

## Settings added (`app/settings.py`; names also in `.env.example`)
`generation_backend: Literal["local-motion","mock","modal","openrouter"] = "local-motion"`, `s3_endpoint_url = "http://localhost:9000"`, `s3_bucket = "media"`, `s3_access_key_id = "minioadmin"`, `s3_secret_access_key = "minioadmin"`, `s3_region = "us-east-1"`, `s3_public_base_url = ""`, `upload_url_ttl_seconds = 900`, `download_url_ttl_seconds = 3600`, `worker_lease_seconds = 300`, `worker_poll_seconds = 1.0`, `worker_reaper_seconds = 30`, `generation_timeout_seconds = 240`, `mock_generation_fails = False`, `modal_endpoint_url = ""`, `modal_webhook_secret = ""`, `openrouter_api_key = ""`, `paid_budget_cents = 500`.
`tests/conftest.py` sets `GENERATION_BACKEND=mock` in `os.environ` before settings load.

## Test plan (AC-9; all against compose Postgres, never paid backends)
| Test | Proves | Task |
|---|---|---|
| `test_migrations.py` | upgrade → downgrade to 0001 → upgrade; 12 presets seeded; partial indexes exist in `pg_indexes` | T-003-1 |
| `test_s3_object_storage.py` | presigned PUT with the signed Content-Type works against MinIO; size read; download; delete | T-003-1 |
| `test_job_step_repository.py` | **double-claim:** two sessions claim concurrently with 1 queued step → exactly one gets it; lease renewal and guarded finish return False for a wrong owner | T-003-2 |
| `test_ledger_repository.py` | balance = SUM; second GRANT/HOLD/resolution violates the unique indexes; sign check | T-003-2 |
| `test_presets_api.py`, `test_uploads_api.py`, `test_credits_api.py` | AC-1, AC-2 (422 type/size, 409 missing object, owner 404), AC-7 (new guest = 60) | T-003-3 |
| `test_job_creation_api.py` | **idempotency** (same key → same id, one HOLD); **insufficient credits** 402 body; 404/409 inputs; balance drops by 20 | T-003-4 |
| `test_job_reading_api.py` | **owner-only access** 404 for another guest on GET and on `/events` | T-003-4 |
| `test_job_events_api.py` | **SSE status sequence** queued → running → succeeded, each within 1s of the NOTIFY; stream closes after terminal | T-003-4 |
| `test_step_completion.py` | success → SETTLE + `succeeded` + 2 assets; **failure release** → RELEASE, balance restored, `error_message` set; lost lease → nothing written | T-003-5 |
| `test_lease_reaper.py` | **lease expiry:** first expiry re-queues (attempt 1), second fails + RELEASE | T-003-5 |
| `test_local_motion_adapter.py` | real mp4 from a generated jpg: h264, ≤720p, 120 frames, faststart; catalog slugs == recipe slugs | T-003-6 |
| `test_backend_selection.py` | each `GENERATION_BACKEND` value → the right class; modal/openrouter raise `BackendNotConfiguredError` | T-003-6 |

## Files (each ≤200 lines; layer rules from STANDARDS)
| File | New/Edit | Task | Responsibility |
|---|---|---|---|
| `apps/api/app/schemas/{presets,uploads,jobs,credits}.py` | New | T-003-0 | the contract (frozen) |
| `apps/api/app/routers/{presets,uploads,jobs,credits}.py` | New | T-003-0 stubs → T-003-3 / T-003-4 | thin HTTP handlers |
| `apps/api/app/main.py` | Edit | T-003-0 (routers) → T-003-4 (lifespan broker) | app factory, lifespan |
| `apps/api/app/settings.py` | Edit | T-003-1 | new settings above |
| `apps/api/pyproject.toml`, `apps/api/uv.lock` | Edit | T-003-1 | add `boto3`; mypy `files` += `app/adapters`, `app/domain` |
| `.env.example`, `docker-compose.yml` | Edit | T-003-1 | env names; MinIO healthcheck + bucket init |
| `apps/api/app/models/{preset,asset,job,job_step,ledger_entry}.py` | New | T-003-1 | SQLAlchemy mapped classes, one table each |
| `apps/api/migrations/env.py` | Edit | T-003-1 | import the new models |
| `apps/api/migrations/versions/0002_create_generation_tables.py` | New | T-003-1 | 5 tables + all indexes/checks above |
| `apps/api/migrations/versions/0003_seed_preset_catalog.py` | New | T-003-1 | upsert the 12 presets |
| `apps/api/app/domain/__init__.py`, `domain/job_states.py`, `domain/credit_rules.py`, `domain/preset_catalog.py` | New | T-003-1 | allowed transitions; credit numbers; the 12 preset definitions |
| `apps/api/app/adapters/__init__.py`, `adapters/object_storage.py`, `adapters/model_adapter.py` | New | T-003-1 | the two Protocols + request/result/error types |
| `apps/api/app/adapters/s3_object_storage.py` | New | T-003-1 | boto3 S3/MinIO/R2 implementation |
| `apps/api/app/storage_dependencies.py` | New | T-003-1 | `get_object_storage()` |
| `apps/api/tests/conftest.py` | Edit | T-003-1 | alembic upgrade once per session; `app`, `client`, `guest_client`, `session_maker`, `object_storage` fixtures |
| `apps/api/tests/fakes/__init__.py`, `tests/fakes/in_memory_object_storage.py` | New | T-003-1 | storage test double |
| `apps/api/tests/test_migrations.py`, `test_domain_rules.py`, `test_s3_object_storage.py` | New | T-003-1 | see test plan |
| `apps/api/app/repositories/{presets,assets,ledger,jobs,job_steps}.py` | New | T-003-2 | SQL only, signatures below |
| `apps/api/app/repositories/users.py` | Edit | T-003-2 | add `lock_user_row` |
| `apps/api/tests/test_job_step_repository.py`, `test_ledger_repository.py` | New | T-003-2 | see test plan |
| `apps/api/app/services/presets.py`, `services/uploads.py`, `services/credits.py` | New | T-003-3 | list presets; presign + complete upload; read balance |
| `apps/api/app/services/guest_accounts.py` | Edit | T-003-3 | GRANT 60 in the same transaction as the user insert |
| `apps/api/tests/test_presets_api.py`, `test_uploads_api.py`, `test_credits_api.py` | New | T-003-3 | see test plan |
| `apps/api/app/services/job_creation.py` | New | T-003-4 | Flow 1 |
| `apps/api/app/services/job_views.py` | New | T-003-4 | load an owned job + preset name + presigned URLs → `JobView` dataclass |
| `apps/api/app/services/job_event_broker.py` | New | T-003-4 | LISTEN connection → per-job queues |
| `apps/api/app/services/job_event_stream.py` | New | T-003-4 | SSE frame generator |
| `apps/api/app/job_event_dependencies.py` | New | T-003-4 | `get_job_event_broker(request)` |
| `apps/api/tests/test_job_creation_api.py`, `test_job_reading_api.py`, `test_job_events_api.py` | New | T-003-4 | see test plan |
| `apps/api/app/worker.py` | Edit | T-003-5 | claim loop + reaper cadence (replaces the heartbeat) |
| `apps/api/app/services/step_claiming.py` | New | T-003-5 | Flow 2 transaction |
| `apps/api/app/services/generation_runs.py` | New | T-003-5 | Flow 3: download, lease renewal, adapter call, upload |
| `apps/api/app/services/step_completion.py` | New | T-003-5 | Flow 4a/4b transactions |
| `apps/api/app/services/lease_reaper.py` | New | T-003-5 | Flow 5 |
| `apps/api/tests/fakes/scripted_model_adapter.py` | New | T-003-5 | adapter double: succeed / fail / hang |
| `apps/api/tests/test_step_claiming.py`, `test_step_completion.py`, `test_lease_reaper.py` | New | T-003-5 | see test plan |
| `apps/api/app/adapters/motion_recipes.py` | New | T-003-6 | the 12 recipes + filter-chain builder |
| `apps/api/app/adapters/local_motion_adapter.py` | New | T-003-6 | ffprobe + ffmpeg runner |
| `apps/api/app/adapters/mock_model_adapter.py`, `adapters/fixtures/mock-video.mp4`, `adapters/fixtures/mock-poster.jpg` | New | T-003-6 | instant fixture backend |
| `apps/api/app/adapters/modal_adapter.py`, `adapters/openrouter_adapter.py` | New | T-003-6 | "not configured" placeholders |
| `apps/api/app/adapters/backend_selection.py` | New | T-003-6 | `GENERATION_BACKEND` → adapter |
| `Dockerfile` | Edit | T-003-6 | `apt-get install ffmpeg` in the app stage |
| `apps/api/tests/test_local_motion_adapter.py`, `test_backend_selection.py` | New | T-003-6 | see test plan |
| `scripts/smoke-generation` | New | T-003-7 | end-to-end local run: guest → upload → job → SSE → mp4 check |

### Repository signatures (T-003-2 writes them; T-003-3/4/5 code against them)
All take `session: AsyncSession` first, only `flush()` (never commit), and return ORM objects or small frozen dataclasses.
- `presets.py`: `list_active_presets(session) -> list[Preset]` (by `sort_order`); `find_active_preset(session, slug) -> Preset | None`.
- `assets.py`: `insert_asset(session, *, asset_id, user_id, kind, status, storage_key, content_type, byte_size=None) -> Asset`; `find_user_asset(session, user_id, asset_id) -> Asset | None`; `mark_asset_ready(session, asset, byte_size) -> None`; `find_assets_by_ids(session, ids) -> dict[uuid.UUID, Asset]`.
- `ledger.py`: `insert_ledger_entry(session, *, user_id, kind, amount, job_id=None) -> LedgerEntry`; `sum_user_balance(session, user_id) -> int` (`coalesce(sum, 0)`).
- `jobs.py`: `find_job_by_idempotency_key(session, user_id, key) -> Job | None`; `insert_job(session, *, user_id, preset_slug, input_asset_id, prompt, idempotency_key, credit_cost) -> Job`; `find_user_job(session, user_id, job_id) -> Job | None`; `find_job(session, job_id) -> Job | None`; `read_job_status(session, job_id) -> str | None`; `transition_job_status(session, job_id, to_status, *, allowed_from, error_message=None, output_video_asset_id=None, output_poster_asset_id=None, started_at=None, finished_at=None) -> bool` (guarded `UPDATE … WHERE status IN allowed_from`); `notify_job_event(session, job_id) -> None`.
- `job_steps.py`: `insert_job_step(session, job_id, kind) -> JobStep`; `claim_next_queued_step(session, worker_id, lease_seconds) -> ClaimedStep | None`; `renew_step_lease(session, step_id, worker_id, lease_seconds) -> bool`; `finish_step(session, step_id, worker_id, to_status, *, backend, last_error=None) -> bool`; `lock_expired_steps(session, limit) -> list[ExpiredStep]`; `requeue_step(session, step_id, last_error) -> None`; `fail_step(session, step_id, last_error) -> None`.
- `users.py`: `lock_user_row(session, user_id) -> None`.

## Reused
- `app/db.py`: `Base`, `get_session`, `create_database_engine`, `create_session_maker` (the worker builds its session maker the same way).
- `app/auth_dependencies.py::require_current_user` on every signed-in route.
- The layering of `routers/auth.py` → `services/guest_accounts.py` → `repositories/users.py`.
- `app/schemas/user.py::ErrorResponse` for 401/404/409 bodies.
- The `tests/conftest.py::open_client` pattern (extended, not replaced).
- The `0001_create_app_user.py` migration style.
- No new frameworks: Postgres is the queue and pub/sub (D-001); boto3 is the only new dependency.

## Risks
- **httpx `ASGITransport` buffers streamed bodies**, so an SSE test can't read frames one by one through the `client` fixture. Mitigation: drive the job's transitions in a concurrent task (`asyncio.gather`) and assert the whole body once the stream closes, or iterate `stream_job_status_events` directly with timestamps.
- **The LISTEN connection drops** (Neon idles connections, Railway restarts). Mitigation: termination listener + reconnect + wake all queues; clients also fall back to a 5s poll (spec 004).
- **The dev DB is shared by tests** (no per-test database). Mitigation: tests create their own guest users and never assume empty tables; conftest runs `alembic upgrade head` so `create_all` never races the migrations. Job-creation tests leave queued steps behind, so claim/worker tests first drain the queue (claim until `None`) before creating the one step they assert on.
- **Presigned PUT from the browser needs bucket CORS.** MinIO allows it by default; R2 needs a CORS rule (`PUT`, `GET`, `Content-Type`), to be added to `docs/runbooks/deploy.md` when R2 goes live.
- **The presign host must be reachable by the browser.** Locally `http://localhost:9000` works; on Railway `S3_ENDPOINT_URL` must be the public R2 endpoint, not an internal host.
- **ffmpeg CPU on the Railway worker:** 1–3s per clip on 12 cores here; a shared vCPU may be 5–10× slower, still inside `GENERATION_TIMEOUT_SECONDS` = 240. Supersampling (×4) can drop to ×2 if needed.
- **`local-motion` ignores `prompt`.** It's stored on the job for the remote backends. Spec 004's UI should label the prompt as optional.
- **Idempotency with a different body** returns the original job silently. Acceptable for a UI that makes one key per click.
- **One guest GRANT per user** (unique index) means spec 008's promo grants must use `TOPUP`, not `GRANT`.
