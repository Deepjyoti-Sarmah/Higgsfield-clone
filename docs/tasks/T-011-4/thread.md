# Thread T-011-4

Append-only. Write with `scripts/task say`.

### 2026-09-26T01:35:50Z · sonnet-5@claude-code · QUESTION

Adding JobKind='faceswap' to the contract breaks apps/web typecheck: src/features/share/shareCopy.ts, src/features/share/ShareResult.tsx, and src/features/studio/StudioStage.tsx hardcode the union 'video'|'image'|'sequence' for job.kind (not derived from the generated schema). These files are outside my brief's allowed list (only apps/web/src/api/generated/schema.d.ts is listed for web). Fixing them is UI wiring that looks like T-011-5's job (face swap tab, web). I left them untouched. The API/worker/migration/contract slice is fully green (271 pytest passed, ruff, mypy, alembic up/down/up clean, openapi diff adds only the two faceswap-jobs paths + JobKind). 'npm run typecheck' fails only because of this pre-existing narrowing in web components; recommend T-011-5 (or a follow-up) widen those three unions to include 'faceswap' with a sane fallback.
