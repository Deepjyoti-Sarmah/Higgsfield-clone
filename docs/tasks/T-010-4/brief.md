# Brief T-010-4: API additions (still → clip input, audio uploads, ledger read, Library and share fields)

**Role:** implementer · **Suggested model:** medium · **Depends on:** T-010-3 merged · **Wave:** W3

## Start here (any harness)
1. `scripts/task claim T-010-4 --as <model>@<harness>`, then `cd` into the printed worktree.
2. Read `AGENTS.md` (Hard rules), `docs/STANDARDS.md`, and `docs/specs/010-reel-and-still/spec.md` AC-10, AC-17, AC-18, AC-19 and AC-20, plus design.md § API contract.
3. Read every file you'll edit before editing it. `services/job_views.py` is 179 lines, so you **must** move code out before adding any (step 5).
4. Questions: `scripts/task say T-010-4 QUESTION "…"`.

## Goal
Five small, independent backend additions that the new UI needs. Each one is covered by a test.

## Allowed files (touch nothing else)
- `apps/api/app/services/job_creation.py`
- `apps/api/app/services/uploads.py`
- `apps/api/app/services/credits.py`, `apps/api/app/repositories/ledger.py`, `apps/api/app/routers/credits.py` (fill the T-010-1 stub)
- `apps/api/app/services/job_views.py`, `apps/api/app/services/library_media.py` (new)
- `apps/api/app/repositories/sequence_jobs.py` (**add** `count_clips_by_job(session, job_ids) -> dict[uuid.UUID, int]` only; change nothing else in it)
- `apps/api/app/services/share_views.py`, `apps/api/app/services/share_html.py`
- `apps/api/tests/test_api_additions_010.py` (new; split if over 200 lines)
- `docs/tasks/T-010-4/report.md`

## The changes
1. **Still → clip (AC-10):** in `create_job`, accept `asset.kind in ("input_image", "output_image")`. Put that tuple in a module constant with a one-line *why*. The owner and `ready` checks stay as they are.
   - Tests: the user's own `output_image` → 202; another user's `output_image` → 404; an `output_video` asset → 404.
2. **Audio uploads (AC-17):**
   - Extend `EXTENSIONS_BY_CONTENT_TYPE` with `audio/mpeg → mp3`, `audio/mp4 → m4a` and `audio/wav → wav`.
   - The asset `kind` is `input_audio` for audio types and `input_image` otherwise. Use a small pure function, `asset_kind_for_content_type`.
   - The size limit stays 10 MB.
   - Tests: an audio upload creates a `pending` `input_audio` asset with a `.mp3` key; `text/plain` → 422 (schema).
3. **Ledger read (AC-20):**
   - `repositories/ledger.py`: `list_user_ledger_entries(session, user_id, limit)`, newest first (`created_at DESC, id DESC`).
   - `services/credits.py`: `read_ledger(...)`.
   - The router body returns `LedgerListResponse`.
   - Tests: after a top-up and a job create, `GET /credits/ledger?limit=10` lists `HOLD` then `TOPUP` then `GRANT`, newest first, and returns another user's entries never.
4. **Library fields (AC-19):**
   - First move `_find_image_urls_by_job` and the related asset-url code out of `job_views.py` into `services/library_media.py`, unchanged in behaviour.
   - Then fill `images: [{asset_id, url}]` for image jobs (keep `image_urls` identical), plus `clip_count` (from `count_clips_by_job`) and `duration_ms` for sequence jobs. `kind` passes `sequence` through.
   - Tests: the Library returns an image job with matching `images[].url` and `image_urls`, and a sequence job with `clip_count=2`.
5. **Share (AC-18):**
   - `read_public_job` handles all three kinds. It fills `kind` and `image_urls` (stills), plus `clip_count` and `duration_ms` (sequences), with the preset fields `None` when there's no preset.
   - `share_html.py`: the OG/meta title and site name say **Reel & Still** (no "Higgsfield").
   - Tests: the public read of a sequence job has `kind="sequence"` and `clip_count`; the public read of an image job has `image_urls`; the share HTML contains "Reel & Still" and not "Higgsfield".

## Acceptance checks
- [ ] Every existing API test is still green (no behaviour change for existing clients)
- [ ] `job_views.py` and `library_media.py` are each ≤ 200 lines; no logic is duplicated between them
- [ ] `openapi.json` unchanged (the schemas are from T-010-1)
- [ ] ruff, mypy, pytest and check-standards pass

## Verify command
```
docker compose up -d --wait db && uv --directory apps/api run alembic upgrade head && uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q && scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json && ! grep -ri higgsfield apps/api/app/services/share_html.py
```

## Out of scope
- The worker, sequence create/read (T-010-3), web code.

## Finish
Write `report.md`. Then:
1. `scripts/task verify T-010-4`
2. `scripts/task submit T-010-4 --as <you> [--transcript <file>]`
