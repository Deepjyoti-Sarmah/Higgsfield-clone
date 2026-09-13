# 5-Minute Video Walkthrough Script & Beat Sheet

**Title:** Higgsfield AI Clone — 24h Agentic Rebuild  
**Target Duration:** 5:00  
**Presenter Setup:** Camera on, browser open to `https://api-production-8afc.up.railway.app`  

---

## Beat 1: Intro & Signed-Out Explore Landing Page (0:00 – 1:00)
- **Visual:** Open `https://api-production-8afc.up.railway.app` signed out in clean browser window.
- **Script:**
  > "Hi! I'm Deepjyoti Sarmah. This is my 24-hour rebuild of Higgsfield.ai, an AI-native image and video generation platform.
  > Notice the signed-out Explore landing page — top brand header with Higgsfield SVG mark, hero showcase video cards (`MOTION DESIGNER`, `EFFECTS STUDIO`, `CINEMATIC CAMERA`), tool cards, and a gallery of 12 motion presets grouped into Camera, Cinematic, and Dynamic categories.
  > All preset cards feature live autoplaying looping motion previews that we generate ourselves and serve from our own storage."

---

## Beat 2: One-Click Guest Session & Video Creation Flow (1:00 – 2:15)
- **Visual:** Click "Start creating" or "✦ Recreate" on the **Dolly In** preset card.
- **Script:**
  > "Clicking 'Recreate' deep links straight to `/create/video?preset=dolly-in`.
  > Notice that guest authentication is entirely seamless — a one-click guest session is initialized in an httpOnly cookie with a 60-credit grant recorded on an append-only Postgres ledger.
  > On the control panel, we drop an image into the upload box. The presigned upload goes straight to S3/Cloudflare R2 storage without proxying through our API server.
  > We click **Generate (20 credits)**. The API validates idempotency, holds 20 credits, inserts the job + worker step, and streams real-time status updates back over Server-Sent Events (SSE) with a 5-second polling fallback.
  > Once finished, the 720p H.264 faststart MP4 plays in the canvas, and credits settle automatically from 60 → 40."

---

## Beat 3: Text-to-Image Generation & Library (2:15 – 3:30)
- **Visual:** Navigate to `/create/image`, then `/library`.
- **Script:**
  > "Next, let's navigate to `/create/image`. Here creators can select aspect ratios, quality levels, and image counts up to 4. Below the composer sits an interactive sample gallery showcase.
  > Now let's visit `/library`. Every output generated during this session is listed here with thumbnail previews, status tags, creation timestamps, and inline result playback."

---

## Beat 4: Public Share Page & OG Metadata (3:30 – 4:15)
- **Visual:** Click "Share" on a finished generation or open `/v/<job-id>` in a new incognito window.
- **Script:**
  > "When you share a generation, open `/v/<job-id>`.
  > Even with JavaScript disabled or for social crawler bots, our FastAPI backend server-renders Open Graph and Twitter Card meta tags (`og:title`, `og:video`, `og:image`) before the SPA hydrates, allowing rich social previews on Twitter, Discord, and Slack."

---

## Beat 5: Multi-Agent Architecture & Engineering Standards (4:15 – 5:00)
- **Visual:** Switch to code editor / GitHub repo view `Deepjyoti-Sarmah/Higgsfield-clone`.
- **Script:**
  > "Behind the scenes, this entire codebase was engineered using a multi-agent workflow.
  > We enforced a strict truth hierarchy where running code and tests beat specs.
  > Role assignments separated Orchestrator, Implementer, Reviewer, and Scout duties across structured task briefs in `docs/tasks/`.
  > The frontend is Vite + React + TS; the backend is FastAPI + SQLAlchemy + Alembic running on Railway with Neon Postgres (unpooled DSN for SSE LISTEN/NOTIFY) and Cloudflare R2 media storage.
  > All linting, strict TypeScript checks, standards checks (`scripts/check-standards`), and unit test suites pass 100%. Thank you!"
