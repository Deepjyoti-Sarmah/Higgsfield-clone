# T-010-14 live click-through: Reel & Still

Site: https://api-production-8afc.up.railway.app. Bundle under test: `index-C-L3mFa5.js`. Playwright + Chromium, 1440x900, light theme unless noted. No code changed.

**Overall: FAIL.** One new blocker: after Render, the stage never shows the sequence (progress or result) until a reload. Everything else works after the fixes.

## Steps

| # | Step | Before fix | After fix | Evidence / ids |
|---|---|---|---|---|
| 1 | Start page: one "Open the studio", real media, preset chips | PASS | PASS (1 button, 4 media, chips Dolly In .. Spiral In, no "Higgsfield" text) | `01-start.png` |
| 2 | Still: prompt, Square, Standard, 1, Generate | FAIL: job succeeded but the stage stayed on "Queued" (294 s), and the API returned `images: []` | PASS: still appears by itself with "Animate this" | still `59b0df1b-dca7-4dc0-ad87-56b732b88b7f`; `before-fix-02-still-stuck-queued.png`, `02-still-result.png` |
| 2b | Guest session race | FAIL: one "Continue as guest" click fired POST /auth/guest twice; Generate within ~5 s made an orphaned job (202, rail empty, job not in the jobs list) in 2 of 3 runs | PASS: 1 guest POST; Generate ~1 s after session start shows the job in the rail | `after-fix-attempt1/2-empty-rail.png`, `after-fix-race-quick-generate.png` |
| 2c | Balance drops on Generate | stayed 60 | PASS: 60 -> 50 right after Generate | `after-fix-race-quick-generate.png` |
| 3 | "Animate this" -> Clip tab "From your still" -> preset -> clip | BLOCKED (no button); then FAIL: Clip tab opened with the empty "Add an image" zone, no "From your still" | PASS: "From your still" shown, Dolly In, clip on stage, caption `modal` / `AI video` | clip1 `94435f45-6494-45dc-868c-3c820b068b59`; `03-clip-seeded.png`, `03-clip1-result.png` |
| 4 | Second clip from an uploaded 640x360 JPG | not run | PASS: uploaded, Dolly In, `modal`, succeeded | clip2 `85b671b9-4474-4ff3-b93a-ff429d653520` |
| 5 | Add both to sequence, 2 slots, XFADE, music, Render | not run | PARTIAL: 2 slots, XFADE chip, music.wav attached, "about 0:10", Render enabled; sequence succeeded on the backend (`ffmpeg`, 2 clips, 9583 ms) but the stage did NOT show it (see P1) | seq `630c2eb2-ec5e-477d-9376-ef71f41d6b46`, second render `0801359c-2b70-493d-b390-0289ece16967`; `05-seq-2slots.png`, `05-seq-ready.png`, `05-seq-render-watch.png`, `05-seq-result.png` (after reload) |
| 6 | Credits popover ledger | not run | PASS with wording note: rows Welcome grant +60, Hold -10/-20/-20/-1, Settled 0 for each job | `06-credits.png` |
| 7 | Share, signed-out context | not run | PASS: /v/630c2eb2... plays a video, shows "2 shots · 0:10", no credits or guest UI | `07-share.png` |
| 8 | 390x844 dark, start + studio | not run | PASS: no horizontal overflow on either | `08-start-mobile-dark.png`, `08-studio-mobile-dark.png` |

Credit path for the guest: 60 grant, still 10, clip 20, clip 20, sequence 1 (twice, second is the P1 repro), ending at about 5 after the extra repro renders.

## Problems

- **P1 (blocker, open): the stage ignores a freshly rendered sequence.** After "Render · 1 credit" the URL gets `item=0801359c-...` and the rail shows the item, but the stage stays "Pick something from the rail. Your work shows up here while it renders." for 2+ minutes, with 0 videos. A reload of `/studio?item=630c2eb2-...` shows the stage correctly: "2 shots · 0:10 · ffmpeg", "Stitched", Download, Share. Same class as the fixed still bug. Not an id mix-up: 0801359c... was my second render and 630c2eb2... the first; the URL item always equalled the API job id (checked on 3 renders: 0801359c, 17f2d13a, 87eeb37e). `onJobStarted` receives the 202 `data.id` (`apps/web/src/api/sequenceJobs.ts`). Also seen on each render: the Sequence draft (2 clips, XFADE, music) is not cleared, the new rail row is not highlighted, no console/page errors, and no `/jobs` refetch after the navigation. Screenshot: `05-seq-render-watch.png`.
- **P2 (fixed, see table):** empty `images` for stills, stuck "Rendering", "Describe the image first." hint, seed lost on "Animate this", double guest POST, stale balance.
- **P3 (minor):** ledger rows read "Hold" / "Settled" / "Welcome grant", not HOLD / SETTLE / TOPUP as in AC-7. Cosmetic.
- **P4 (minor):** share page top bar still shows a "Studio" link ("Reel & Still | Studio | Sequence | 2 shots · 0:10 | Make your own"). AC-18 asks for no studio UI.
- **P5 (note):** the 2-clip sequence with a 0.5 s crossfade reads "0:10" (API 9583 ms); rounding, not a bug.

## Console and network errors

Only `GET /api/v1/me` 401 (logged-out probe on a cold visit) and the matching "Failed to load resource" line, in each context. No other console errors.

## Deviations from the brief

- Not one single context: the run was split across contexts because of the fixes and script timeouts (the guest cookie was reused for steps 5-6). Steps 7 and 8 used new signed-out contexts as asked.
- The sequence was rendered four times (1 credit each) while diagnosing P1.
