# 5-minute walkthrough: Reel & Still

First person, read aloud. Timings assume the local stack is up (`docker compose up -d --wait db minio`, the API on :8000, the worker running, `npm --prefix apps/web run dev` on :5173) and the browser is signed out. Every label in quotes is on screen exactly as written.

## 0:00 — Open the start page (30 s)
> "This is Reel & Still, a small studio for short films. Make a still, animate it into a clip, then cut your clips into a sequence — one workspace, one credit ledger.
> The page shows the three steps with real media we generated, and motion-preset chips that deep-link into the studio. One button here: **Open the studio**."

## 0:30 — Make a still (75 s)
> "The studio is one screen: the rail of my generations on the left, the stage in the middle, and the composer underneath with **Still · Clip · Sequence** tabs.
> I'm on the **Still** tab. I type a prompt — 'neon alley after rain' — pick a wide shape, and press **Generate · 10 credits**.
> While it runs, the stage shows the phase with elapsed time over a polite live region. When it lands, the caption shows what actually made it. If the placeholder fallback ran, the page says so plainly."

## 1:45 — Animate this, and a second clip (90 s)
> "Every still has **Animate this**. Clicking it hands the image to the **Clip** tab with no download and no re-upload — the composer shows it labelled **From your still**.
> I pick a motion preset, press **Animate · 20 credits**, and the clip starts on the same ledger. I'll make one more clip from another still so I have two to cut.
> Notice the credits button in the top bar dropped from 60 to 20 as each job held its credits."

## 3:15 — Cut a sequence (75 s)
> "Now the **Sequence** tab. The strip holds two to six clips; I drag to reorder, or use the move and remove buttons — it's all keyboard-operable.
> The chip between the slots cycles **CUT · XFADE · FADE**. I set a crossfade. I drop in a music file, up to ten megabytes, and the readout shows the length — about 0:10.
> Press **Render · 1 credit**. When it lands, the rail shows the sequence with a status dot, and the stage plays it with its shots-and-length caption."

## 4:00 — Where the credits went (30 s)
> "Click the balance. **Add demo credits (100)** — no payment is taken — and below it, the ledger: every job left a **Hold** of −1 or −20 and a **Settled** row linked to the job. If a render had failed, a **Refund** would be here instead. The money is fake; the accounting is real."

## 4:30 — Share it (15 s)
> "One **Share** link gives `/v/<id>` — a quiet viewer that plays the clip or sequence signed out, with one button, **Make your own**."

## 4:45 — How it was built with agents (15 s + closing line)
> "One more thing: this repo was built by agents. A `scripts/task` board hands each agent a task packet — a `brief.md`, a `thread.md` for questions, a `verify.log` with the exact command output, and a `report.md` from a *different* model reviewing the diff. Every prompt and response is captured in `.agent-logs/`, and several models shared the work across harnesses.
> The docs say what the running system does — including the decisions that changed, like D-015 superseding D-014 when images became real. Thank you."

---

**Total: 5:00.** If the model backends aren't configured locally, say at 0:30: "locally this runs against the labelled fallback backend — the UI tells you which one made each result; the deployed stack runs the real models."
