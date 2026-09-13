# Report T-003-7

**Agent / model / tool:** reviewer · deepseek-flash (DeepSeek Harness) · direct tool calls in the DSH Web GUI
**Result:** DONE
**Verify chain exit code:** 0 (smoke exit 0, pytest exit 0, check-standards exit 0)

## Reviewer independence (read first)
The brief asks the reviewer to be a **different model** from the T-003-4/T-003-5 implementers. That was
**not possible in this session**: T-003-4 and T-003-5 were both implemented by **deepseek-flash (DSH)**, and
I am the same model (deepseek-flash via DSH). The other backends are unavailable (Claude Code account-quota-limited
until 05:50 UTC, Codex out until 2026-09-30, no gemini/aider/OpenRouter key). **This review is therefore
self-review and does not satisfy AGENTS.md "don't mark your own work reviewed".** It is recorded as an open
issue; an independent model must re-run the smoke before the milestone is called reviewed. To compensate I ran
the adversarial probes in "Running behaviour vs spec/design" below against the live stack rather than trusting
the earlier reports.

## Files changed
- `scripts/smoke-generation` (new, executable, 197 lines): the 9-step end-to-end smoke. Python 3 stdlib only
  (`argparse`, `http.cookiejar`, `json`, `subprocess`, `time`, `urllib`, `uuid`); one `ok N <label> …` line per
  step; exits 1 on the first failure; `--base-url`, `--work-dir`. AC-2 rules are checked by the server (step 4
  only asserts `ready`); step 7 ffprobes the downloaded mp4 (h264, 1280×720, 120 frames, 5.000 s).
- `docs/tasks/T-003-7/report.md`: this file.
- DoD state files: `docs/specs/003-generation-core/tasks.md` (T-003-7 ticked), `docs/PLAN.md` (T-003-7 row),
  `docs/STATUS.md` (AC-1…AC-8 lines), `docs/WORKLOG.md` (one appended line).

No application file (`apps/**`) was touched. The file that failed the smoke (none) is not fixed here.

## Reused
- The API exactly as the browser uses it: `POST /auth/guest`, `GET /presets`, `POST /uploads` + presigned PUT +
  `POST /uploads/{id}/complete`, `POST /jobs` (idempotency), `GET /jobs/{id}/events` (SSE), `GET /jobs/{id}`,
  `GET /credits`. No internal Python import of `app.*`.
- `packages/contracts/openapi.json` fields read verbatim (`presets[].credit_cost`, `JobCreatedResponse`,
  `InsufficientCreditsResponse {detail,balance,required}`, `UploadCreateResponse.upload_url/upload_headers`).
- `docs/specs/003-generation-core/design.md` for the SSE frame shape (`retry: 3000`, `event: status`, `: ping`)
  and the `GENERATION_BACKEND=local-motion` command line.
- The brief's verify chain, run as-is (only the process cleanup was PID-based, because `pkill -f "python -m app.worker"`
  matches its own shell command line and killed the shell mid-run — see Open issues).

## Verify output (full paste, no summarising)
The chain below is the brief's verify command with `pkill -f` replaced by a PID-based cleanup loop so the shell
survives; everything else is verbatim. `/tmp/T-003-7-verify.log` holds the raw capture.

```
$ docker compose up -d --wait db minio && docker compose run --rm minio-init
 Container higgsfield-db-1 Running
 Container higgsfield-minio-1 Running
 Container higgsfield-db-1 Waiting
 Container higgsfield-minio-1 Waiting
 Container higgsfield-minio-1 Healthy
 Container higgsfield-db-1 Healthy
 Container higgsfield-minio-1 Running
 Container higgsfield-minio-1 Waiting
 Container higgsfield-minio-1 Healthy
 Container higgsfield-minio-init-run-980a9d799fee Creating
 Container higgsfield-minio-init-run-980a9d799fee Created
Added `local` successfully.
Bucket created successfully `local/media`.
Access permission for `local/media` is set to `private`

$ uv --directory apps/api run alembic upgrade head
(no output)

$ (cd apps/api && GENERATION_BACKEND=local-motion uv run uvicorn app.main:app --port 8000 > /tmp/api.log 2>&1 &)
$ (cd apps/api && GENERATION_BACKEND=local-motion APP_ROLE=worker uv run python -m app.worker > /tmp/worker.log 2>&1 &)
$ sleep 3

$ scripts/smoke-generation --base-url http://localhost:8000
smoke-generation: base_url=http://localhost:8000
ok 1 presets: 12 presets, every credit_cost=20
ok 2 guest: guest 427df17f-5b11-4a16-9374-c31cc400f7b5 balance=60
ok 3 test image: 1600x1000 jpg at /tmp/smoke-input.jpg
ok 4 upload: asset 157afe25-017d-42ac-9af8-9a27203db96b ready (63497B)
ok 5 create job + idempotency: job 63d448c2-0a1f-4b10-8c33-1dff4a9d45ed queued, repeat idempotent, balance=40
ok 6 sse statuses: statuses queued -> running -> succeeded
ok 7 outputs: mp4 446882B 1280x720 120f 5.000s h264; poster 52365B
ok 8 credits: balance=0, 4th job 402 required=20
ok 9 owner only: guest 856846e7-c29a-43e9-bed4-bf7f61128064 got 404 on the job and its events
smoke-generation: PASS (9/9 steps)
[smoke exit code: 0]

$ uv --directory apps/api run pytest -q
........................................................................ [ 66%]
....................................                                     [100%]
=============================== warnings summary ===============================
tests/test_uploads_api.py::test_complete_with_a_declared_size_mismatch_deletes_the_object
tests/test_uploads_api.py::test_complete_with_an_oversized_object_is_rejected
  /home/deepjyoti/Documents/Assigment/Higgsfield/apps/api/.venv/lib/python3.12/site-packages/fastapi/routing.py:352: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
108 passed, 2 warnings in 42.95s
[pytest exit code: 0]

$ scripts/check-standards
check-standards: ok (0 violations)
[check-standards exit code: 0]

$ # cleanup
[port 8000 listeners after cleanup: 0]
```

The smoke was run **three** times end to end (two standalone, one inside the chain); every run printed the same
9 `ok` lines. Wall time of the smoke itself: ~7 s (script-level), with ffmpeg renders ~1.2 s each.

### `/tmp/api.log` (tail 08:58, the chain run)
```
INFO:     127.0.0.1:53310 - "GET /api/v1/credits HTTP/1.1" 200 OK
INFO:     127.0.0.1:53316 - "POST /api/v1/jobs HTTP/1.1" 402 Payment Required
INFO:     127.0.0.1:53320 - "POST /api/v1/auth/guest HTTP/1.1" 201 Created
INFO:     127.0.0.1:53326 - "GET /api/v1/jobs/9c8e7518-5031-42af-bb3f-b6352715968d HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:53336 - "GET /api/v1/jobs/9c8e7518-5031-42af-bb3f-b6352715968d/events HTTP/1.1" 404 Not Found
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [270625]
```
No errors or tracebacks in the API log on any run; startup was clean
(`Application startup complete` then `Uvicorn running on http://127.0.0.1:8000`).

### `/tmp/worker.log` (the chain run)
```
2026-09-13 08:58:04,679 worker worker fedora:270626:fdbde603 backend=local-motion lease=300s poll=1.0s
2026-09-13 08:58:07,756 worker claimed step f9a15e5e-… job=63d448c2-… attempt=1
2026-09-13 08:58:08,939 worker finished step f9a15e5e-…
2026-09-13 08:58:09,966 worker claimed step 3828bd14-… job=b95590c2-… attempt=1
2026-09-13 08:58:11,183 worker finished step 3828bd14-…
2026-09-13 08:58:12,202 worker claimed step 380cb89b-… job=9c8e7518-… attempt=1
2026-09-13 08:58:13,460 worker finished step 380cb89b-…
… (one claim/finish pair per job the smoke's steps 8 produced; each attempt=1)
2026-09-13 08:58:53,937 worker worker loop error; retrying after the poll interval
2026-09-13 08:58:56,961 worker claimed step 79735c5f-… job=23831f1f-… attempt=2
2026-09-13 08:58:56,978 worker finished step 79735c5f-…
```
The `worker loop error` + `attempt=2` pair is inside the pytest window and comes from the tests' own
`POST /jobs` rows being claimed by this worker (shared dev DB); the job was failed + refunded, and pytest still
passed. At startup the reaper also logged `reaper returned 2 expired step(s) to the queue or failed them` — those
were leftover `running` leases from the 03:19 UTC test session whose input objects no longer exist in MinIO
(`HeadObject 404`), i.e. exactly the lease-expiry path working. Full traceback is in `/tmp/worker.log`.

## Acceptance checks (brief)
- [x] The script passes end to end against the local stack — 9/9 `ok`, exit 0, three runs.
- [x] Each AC-1 … AC-8 has a STATUS line citing a file path and this verify command (or a pytest file) — see below.
- [x] Any mismatch between the running code and design/contract is written up — see "Running behaviour vs spec/design".

## AC-1…AC-8 evidence
| AC | Running evidence (this run) | Code path |
|---|---|---|
| AC-1 presets | smoke step 1: `12 presets, every credit_cost=20`, signed out | `apps/api/app/routers/presets.py`, `services/presets.py` |
| AC-2 uploads | smoke step 4: `POST /uploads` → presigned PUT → `complete` → `ready`; probes: gif → 422, >10 MB → 422 | `routers/uploads.py`, `services/uploads.py` |
| AC-3 create job | smoke step 5: 202 `{queued, 20}`, same `idempotency_key` → same `id`, balance 40; step 8: 402 top-level `balance=0 required=20` | `routers/jobs.py`, `services/job_creation.py` |
| AC-4 worker | smoke steps 6–7; worker log: `backend=local-motion`, one claim per job, `attempt=1`, `finished` → real mp4 + poster + balance settled to 40 then 0 | `worker.py`, `services/{step_claiming,generation_runs,step_completion}.py` |
| AC-5 reaper | worker log at startup: `reaper returned 2 expired step(s)…` (leftover 03:19 session leases, `HeadObject 404` → job failed + refunded) | `services/lease_reaper.py` |
| AC-6 progress | smoke step 6: SSE `queued -> running -> succeeded`, stream closed; wire trace measured 0.012 s / 0.808 s / 2.095 s after connect; headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`; non-owner `/events` 404 JSON | `services/job_event_stream.py`, `job_event_broker.py`, `routers/jobs.py` |
| AC-7 credits | smoke steps 2/5/8: new guest 60 → 40 after the create → 0 after 3 videos; ledger `GRANT 60, HOLD −20, SETTLE 0` | `services/{credits,guest_accounts}.py`, `repositories/ledger.py` |
| AC-8 backends | smoke step 7 ffprobe: h264, 1280×720, 120 frames, 5.000 s (`dolly-in` from a 1600×1000 jpg); faststart probe: atom order `ftyp, moov, free, mdat` | `adapters/{local_motion_adapter,motion_recipes}.py`, `GENERATION_BACKEND=local-motion` |
| AC-9 tests | `uv --directory apps/api run pytest -q` → 108 passed | `apps/api/tests/` (double-claim, idempotency, 402, release, lease expiry, SSE sequence, owner-only) |

AC-6's `: ping` is only unit-proven (`test_job_events_api.py::test_stream_pings_while_the_status_does_not_change`
with `ping_seconds=0.15`); the live run never reaches the 20 s mark, so the live 20 s ping is a **gap**, not a pass.

## Running behaviour vs spec/design (adversarial probes, not trusting the earlier reports)
Ran `/tmp/adversarial-probe.py` against the live API (all `PASS`):
```
PASS AC-2 gif -> 422: 422 {"detail":[{"type":"literal_error","loc":["body","content_type"],…}]}
PASS AC-2 >10MB -> 422: 422 {"detail":[{"type":"less_than_equal",…10485760…}]}
PASS AC-7 /credits unsigned -> 401 {detail}: 401 {"detail":"Not signed in"}
PASS AC-3 402 top-level balance/required + detail: 402 {'detail': 'Not enough credits', 'balance': 0, 'required': 20}
PASS AC-6 first status frame < 1s (terminal job): 0.023s first=b'retry: 3000\n'
PASS AC-6 stream closes after terminal
PASS AC-6 Cache-Control: no-cache; X-Accel-Buffering: no
PASS AC-6 non-owner /events -> 404 JSON (Content-Type absent, not text/event-stream)
PASS AC-8 faststart (moov before mdat): ['ftyp', 'moov', 'free', 'mdat']
ALL PROBES PASS
```
Full SSE wire trace of one live job (fresh guest, `dolly-in`):
```
 0.010s  retry: 3000
 0.012s  event: status / data: {"job_id":"ef03b00e-…","status":"queued"}
 0.808s  event: status / data: {"job_id":"ef03b00e-…","status":"running"}
 2.095s  event: status / data: {"job_id":"ef03b00e-…","status":"succeeded"}   (stream closes)
```
That is the design's frame shape exactly, and `/tmp/api.log` shows the ownership checks happening before the
stream (`GET …/events 404` for a non-owner with no SSE body).

## Mismatches found (code wins; lower source must be fixed)
1. **`GET /jobs/{job_id}` omits `credit_cost` while `design.md` says polling returns "the same data".**
   Design (line 43) promises the GET "returns the same data for polling", and spec 004's UI shows the cost of a
   completed clip; but `packages/contracts/openapi.json::JobResponse` has no `credit_cost` field and the running
   handler does not send one (checked live). `POST /jobs` does return it. The running code and the contract agree
   with each other and both disagree with design's prose, so the design sentence is the lower source: either
   relax the design wording or add `credit_cost` to `JobResponse` (a contract change, T-003-0/orchestrator —
   not mine to make). Consumer at risk: spec 004's poll fallback cannot show the cost without extra state.
2. **`openapi.json` documents the non-owner `/jobs/{id}/events` 404 as `application/json` `ErrorResponse`, which
   the live server matches, but the 404 carries no `Content-Type` header at all** (FastAPI default for the plain
   `HTTPException` body here). Cosmetic for `fetch`/the web client, which parses the body regardless; no code
   change requested.
3. **Reaper timing:** a `running` step whose worker died waits up to `WORKER_REAPER_SECONDS=30` before the reaper
   re-queues it, and the first re-queue does not refund; the design says exactly this, and I confirmed the
   re-queue/fail+release behaviour on startup, so this is a note, not a defect.
4. **`local-motion` ignores `prompt`** (design risk list). Confirmed implicitly: step 5 stores/serves the prompt
   but the render is preset-only. Expected and already documented.

## Standards check
```
$ scripts/check-standards
check-standards: ok (0 violations)
```
`scripts/smoke-generation` is 197 lines (≤200). It is extensionless but `check-standards` scans `scripts/`, so it
was compressed onto the 200-line budget rather than split (the brief's allowed-files list has no room for a
helper module).

## Open issues / guesses / things skipped
- **Reviewer independence:** self-review by the same model as T-003-4/T-003-5 (see top). An independent model
  must re-run `scripts/smoke-generation --base-url http://localhost:8000` before this task counts as reviewed.
- The brief's verify chain uses `pkill -f "uvicorn app.main:app"; pkill -f "python -m app.worker"`. The second
  pattern matches the shell running the chain itself, so the chain died with SIGTERM after the smoke (I lost one
  run to it). I replaced only the cleanup with a PID loop; the brief's cleanup should be fixed (e.g.
  `pkill -f "app\.worker"` or PID files) so the orchestrator's re-run does not self-terminate.
- The worker and `pytest` run **concurrently against the same dev Postgres**. During the chain, the worker
  claimed one-line jobs (1 ms claim→finish, `attempt=1`) at the exact timestamps of the API test window, i.e.
  jobs created by the tests, and one of them hit `worker loop error` / `attempt=2` / refunded. pytest still
  reported 108 passed, but the tests do not own the queue while the worker is alive — a flake risk. No test
  failed, so it is reported, not fixed.
- AC-6's live 20 s `: ping` is not exercised (90 s smoke would need a hung job); only the unit test with a
  shortened interval proves it.
- AC-2's 422 rules are proven by the probing above and by `test_uploads_api.py`; the smoke itself only asserts
  the happy path to stay inside the brief's 9 steps.
- The smoke leaves guest users, jobs, assets and ledger rows in the dev DB (it needs a fresh guest per run, by
  design). No cleanup endpoint exists; the reaper drains stale steps.
- `.agent-logs/` is not included here: this DSH run is captured by the harness, and the brief's allowed-files
  list does not include `.agent-logs/`. The orchestrator should add the capture when it commits.

## Proposed STATUS.md lines
| What | Where | Verified by | When (UTC) |
|---|---|---|---|
| AC-1/AC-7 presets, guest grant, credits | `apps/api/app/routers/presets.py`, `services/{presets,credits,guest_accounts}.py` | `scripts/smoke-generation --base-url http://localhost:8000` steps 1–2, 5, 8 on local compose (api + worker, `GENERATION_BACKEND=local-motion`) | 2026-09-13 03:27 |
| AC-2 uploads | `apps/api/app/routers/uploads.py`, `services/uploads.py` | smoke step 4 + probes (gif/oversize → 422); `apps/api/tests/test_uploads_api.py` | 2026-09-13 03:27 |
| AC-3 create job (one transaction, idempotent, 402) | `apps/api/app/services/job_creation.py`, `routers/jobs.py` | smoke steps 5, 8; `apps/api/tests/test_job_creation_api.py` | 2026-09-13 03:27 |
| AC-4 worker end to end (real motion mp4 + poster) | `apps/api/app/worker.py`, `services/{step_claiming,generation_runs,step_completion}.py`, `adapters/local_motion_adapter.py` | smoke steps 6–7 (h264 1280×720 120f 5.000 s) + worker log claims | 2026-09-13 03:27 |
| AC-5 reaper | `apps/api/app/services/lease_reaper.py` | worker startup reaped 2 expired leases (`/tmp/worker.log`); `apps/api/tests/test_lease_reaper.py` | 2026-09-13 03:27 |
| AC-6 SSE progress + owner-only reads | `apps/api/app/services/job_event_stream.py`, `routers/jobs.py` | smoke steps 6, 9 (wire trace 0.012/0.808/2.095 s, close after terminal); `test_job_events_api.py`, `test_job_reading_api.py` | 2026-09-13 03:27 |
| AC-8 local-motion backend | `apps/api/app/adapters/{local_motion_adapter,motion_recipes}.py` | smoke step 7 ffprobe + faststart probe; `test_local_motion_adapter.py` | 2026-09-13 03:27 |
| Spec 003 end-to-end smoke on local compose | `scripts/smoke-generation` | `scripts/smoke-generation --base-url http://localhost:8000` → 9/9 `ok`, exit 0; `uv --directory apps/api run pytest -q` → 108 passed; `scripts/check-standards` → ok | 2026-09-13 03:27 |
