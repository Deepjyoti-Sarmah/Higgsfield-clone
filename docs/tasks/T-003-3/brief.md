# Brief T-003-3: Presets, uploads and credits endpoints + guest grant

You are the **implementer** for this one task. Your first steps:
1. Read `AGENTS.md` and `docs/STANDARDS.md`.
2. Read the links below.
3. Nothing else is needed.

## Context links
- Spec: `docs/specs/003-generation-core/spec.md` (AC-1, AC-2, AC-7; AC-9 owner access)
- Design: `docs/specs/003-generation-core/design.md` sections **API contract** (rows `/presets`, `/uploads`, `/uploads/{asset_id}/complete`, `/credits`), **Storage** (key layout, TTLs, URLs), **Credit rules**, **Repository signatures**
- Contract: `packages/contracts/openapi.json`, paths `GET /api/v1/presets`, `POST /api/v1/uploads`, `POST /api/v1/uploads/{asset_id}/complete`, `GET /api/v1/credits`
- Pattern: `apps/api/app/routers/auth.py` → `services/guest_accounts.py` → `repositories/users.py`

## Goal
Replace the 501 stubs for presets, uploads and credits with real handlers, and give every new guest a one-time 60-credit GRANT.

## Allowed files (touch nothing else)
- `apps/api/app/services/{presets,uploads,credits}.py`
- `apps/api/app/services/guest_accounts.py` (GRANT in the same transaction as the user insert)
- `apps/api/app/routers/{presets,uploads,credits}.py`
- `apps/api/tests/{test_presets_api,test_uploads_api,test_credits_api}.py`
- `docs/tasks/T-003-3/report.md`

## Behaviour
- **Presets:** `list_active_presets` → `PresetListResponse`. No auth.
- **Create upload:** new `asset_id = uuid4()`, key `users/{user_id}/inputs/{asset_id}.{jpg|png|webp}`, insert `asset(kind=input_image, status=pending)`, commit, return `create_upload_url(key, content_type, UPLOAD_URL_TTL_SECONDS)`, `upload_headers={"Content-Type": content_type}`, `expires_at`.
- **Complete upload:** not the caller's → 404; `read_object_size` is `None` → 409 `"Upload not found in storage"`; size > 10 MB or ≠ declared `byte_size` → delete the object, 422 `"Uploaded file does not match the declared size"`; else `mark_asset_ready`, commit, return `AssetResponse` with a download URL. Already `ready` → 200 again (idempotent).
- **Credits:** `sum_user_balance` → `CreditsResponse`.
- **Guest grant:** `create_guest_account` inserts the user, then `insert_ledger_entry(kind="GRANT", amount=GUEST_GRANT_CREDITS)`, then commits once.
- URLs: use `build_asset_url(storage, key, settings.s3_public_base_url, settings.download_url_ttl_seconds)` from `app/adapters/object_storage.py` (T-003-1). Don't write a second copy.
- Routers stay thin: parse → service → schema. Services never import FastAPI; they raise small typed exceptions that routers map to status codes.

## Must reuse
- `require_current_user`, `get_session`, `get_settings`, `get_object_storage`, `build_asset_url`, `ErrorResponse`, the repositories from T-003-2, `domain/credit_rules.py`, the `client` / `guest_client` / `other_guest_client` / `object_storage` fixtures.

## Acceptance checks
- [ ] AC-1: signed-out `GET /api/v1/presets` → 200 with ≥12 presets, each field present, `credit_cost == 20`
- [ ] AC-2: jpeg/png/webp ≤ 10 MB → 201 with `upload_url`; `image/gif` → 422; `byte_size` 10485761 → 422; signed out → 401
- [ ] AC-2: complete before `object_storage.put_bytes` → 409; after → 200 `status:"ready"` with a `url`; wrong size → 422; `other_guest_client` completing it → 404
- [ ] AC-7: a fresh guest's `GET /api/v1/credits` → `{"balance": 60}`; signed out → 401
- [ ] `openapi.json` is byte-identical after `scripts/export-openapi` (the contract didn't move)

## Verify command (paste its full output in report.md)
```
docker compose up -d --wait db
uv --directory apps/api run alembic upgrade head
uv --directory apps/api run ruff check .
uv --directory apps/api run mypy
uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
scripts/check-standards
```

## Out of scope
- Jobs, SSE, the worker, top-up (spec 008), preview videos (spec 006), `app/schemas/*` changes (report instead).

## Report
Write `docs/tasks/T-003-3/report.md` using `docs/templates/report.md`, then follow the definition of done in `AGENTS.md` (commit per the kickoff prompt, plain message, no trailers, include `.agent-logs/`).
