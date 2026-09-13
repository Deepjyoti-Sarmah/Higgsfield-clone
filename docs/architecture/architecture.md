# Architecture (text; kept current, and it wins over the .excalidraw drawings)

Drawings: `architecture-mvp.excalidraw` (target MVP) and `architecture.excalidraw` (earlier full target).
The deltas from the drawings are recorded in `docs/DECISIONS.md` (D-001 to D-007).

## Runtime
```
Browser (React SPA, EventSource)
   │  same origin
   ▼
Railway: api  (FastAPI)
   /api/*        REST + SSE, guest JWT in httpOnly cookie
   /v/{id}       Jinja2 OG share page (for crawlers)
   /*            built SPA static files
   /hooks/modal  generation callback
   │
   ├── Neon Postgres: user · asset · preset · job · job_step (queue) · ledger · LISTEN/NOTIFY
   ├── R2: media via presigned URLs (browser <-> R2 directly)
   ▼
Railway: worker  (same image)
   claim job_step FOR UPDATE SKIP LOCKED · lease + reaper · submit -> release -> wait for callback
   │
   ▼
ModelAdapter (strategy: modal -> openrouter while budget remains; mock in tests)
   Modal: LTX-2.5 distilled (video) · LLaDA-Image Turbo (image)
   OpenRouter: Seedance 2.0 Mini (video) · Seedream 4.5 (image) · Nano Banana 2 Lite (face swap edit)
```

## Invariants (do not break)
1. `POST /api/v1/jobs` does everything in ONE transaction: validate, HOLD credits, insert job + step, NOTIFY. It returns 202.
2. Credit balance = `SUM(ledger)`; it's never stored on the user. A step settles its HOLD on success and releases it on failure or reaper expiry.
3. Every job has an `idempotency_key` with a unique index.
4. Each API replica holds ONE dedicated LISTEN connection and fans out to per-job `asyncio.Queue`s.
   - SSE sends ids, not objects.
   - `: ping` every 20s.
   - The client falls back to a 5s poll.
5. Paid generation is refused once `PAID_BUDGET_CENTS` is spent.
