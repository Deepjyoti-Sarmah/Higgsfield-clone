# Brief T-030: Own preset preview media (remove all hotlinked higgsfield.ai media)

**Role:** implementer (medium/strong model) · **Runs before T-031**

## Problem
Every preset preview currently points at the original product's CDN:
- `apps/api/app/domain/preset_catalog.py` sets `preview_url="https://cdn.higgsfield.ai/card/….mp4"` (5 presets) and `https://d8j0ntlcm91z4.cloudfront.net/user_…/hf_….mp4` (7 presets — those are other people's generations).
- `apps/web/src/features/explore/presetFallbacks.ts` hardcodes the same 12 URLs again as a client-side fallback.

Two failures:
1. **It's other people's media.** This repo is a public demo of our own build. Serving their marketing clips and users' generations as our preview reel is not defensible.
2. **It doesn't even render.** The live API returns `preview_url: null` for all 12 presets, so every Explore and Create-video card shows an empty gradient box. That is the single biggest reason the UI looks unfinished.

## Goal
Twelve preview clips that **we generated**, stored in our own R2 bucket, served from our own domain — each one literally demonstrating that preset's camera move.

## Allowed files
- `scripts/build-preset-previews` (new)
- `apps/api/app/domain/preset_catalog.py`
- `apps/api/app/services/presets.py`
- `apps/api/app/schemas/presets.py`
- `apps/api/migrations/versions/0003_seed_preset_catalog.py`
- `apps/api/tests/test_presets_api.py`
- `apps/web/src/features/explore/presetFallbacks.ts` (**delete**)
- `apps/web/src/features/explore/PresetGalleryCard.tsx`, `apps/web/src/features/create-video/PresetCard.tsx` (import removal only — no layout changes, T-031 owns those)
- `docs/research/preview-sources.md` (new: source image credits)
- `README.md` (one line crediting the preview source images)

## Source images (pick ONE, record which in the report)
1. **Preferred:** 3–4 CC0 / Unsplash-licence stills you download once into `apps/api/app/adapters/fixtures/preview_sources/`. Record photographer + licence + URL in `docs/research/preview-sources.md`.
2. **Fallback:** synthesise them with ffmpeg (gradient + text plate). Ugly but unambiguously ours.

Do **not** use `picsum.photos` (it redistributes third-party photos) and do not pull from any higgsfield.ai or cloudfront.net URL.

## The work
1. **`scripts/build-preset-previews`** (python, ≤200 lines, executable):
   - For each of the 12 presets in `PRESET_CATALOG`, render a preview with the **existing** recipe code — reuse `apps/api/app/adapters/motion_recipes.py` and `local_motion_adapter.py`. Do not re-implement ffmpeg commands.
   - Output: `previews/<slug>.mp4` (5s, ≤720p, h264 + faststart) and `previews/<slug>.jpg` poster.
   - Upload through the existing `S3ObjectStorage` (`apps/api/app/adapters/`), honouring `S3_*` env vars, so it works against MinIO locally and R2 in prod.
   - `--dry-run` renders locally without uploading.
2. **Store keys, not absolute URLs.** Rename the catalog field to `preview_key` (e.g. `"previews/dolly-in.mp4"`). In `services/presets.py`, build the response URL with the existing `build_asset_url(storage, key, settings.s3_public_base_url, settings.download_url_ttl_seconds)` from `apps/api/app/adapters/object_storage.py` — the same helper `job_views.py` and `share_views.py` already use. The API response field stays `preview_url` so the contract does not change.
3. **Migration `0003`** seeds `preview_key` (column rename or new column — your call, but `alembic upgrade head` then `downgrade` must both work).
4. **Delete `presetFallbacks.ts`** and its two imports. A missing preview renders the existing poster/empty state, never a hardcoded URL.
5. **Run the script against R2** with the live `S3_*` credentials and confirm the 12 objects exist.

## Acceptance checks
- [ ] `grep -rn "higgsfield.ai\|cloudfront.net" apps/ packages/ scripts/` returns **nothing**
- [ ] `GET /api/v1/presets` returns a non-null `preview_url` for all 12, each pointing at our own bucket/domain
- [ ] `packages/contracts/openapi.json` is byte-identical (no contract change)
- [ ] `alembic upgrade head` and `alembic downgrade -1` both succeed
- [ ] A preview clip opens in a browser and visibly shows that preset's move

## Verify command (paste full output in report.md)
```
docker compose up -d --wait db minio && docker compose run --rm minio-init
uv --directory apps/api run alembic upgrade head
scripts/build-preset-previews --dry-run
uv --directory apps/api run ruff check . && uv --directory apps/api run mypy && uv --directory apps/api run pytest -q
scripts/export-openapi && git diff --exit-code packages/contracts/openapi.json
npm --prefix apps/web run lint && npm --prefix apps/web run build
grep -rn "higgsfield.ai\|cloudfront.net" apps/ packages/ scripts/ || echo "no hotlinks - ok"
scripts/check-standards
```

## Out of scope
- Any layout, spacing or styling change (T-031 owns that).
- The Modal/AI backend. These previews come from the local-motion recipes.

## Report
`docs/tasks/T-030/report.md` from `docs/templates/report.md`. Commit with a plain message, no attribution trailers, including `.agent-logs/`.
