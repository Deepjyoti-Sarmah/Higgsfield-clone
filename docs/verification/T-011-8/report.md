# T-011-8 live verification of spec 011

Site https://api-production-8afc.up.railway.app, bundle `index-C4QPPF_j.js`, fresh guest `62fc7a` (60 credits), Playwright + Chromium 1440x900. No code changed. **Overall: PASS with findings** (no blocker).

| # | Step | Result | Ids / numbers | Evidence |
|---|---|---|---|---|
| 1a | Still "golden hour portrait of a woman in a linen shirt…" (Portrait, Standard, 1) | PASS (image ok), see F1 | still `f2ed03d3-c210-4aa5-85c1-412935faed0d`, `modal`, 83 s | `02-still.png`, `01-still.png` |
| 1b | Animate this, Dolly In, no prompt; "From your still" shown | PASS | clip `739eab6b-df2e-462e-b333-56faeff67a27`, `modal`, 161 s (this clip was the first on this container, cold start likely), 704x704, 24 fps, 121 frames, 5.04 s | `03-clip-form.png`, `03-clip-result.png` |
| 1c | AC-1 fidelity: SSIM of frames 0, 60, last (120) against the still scaled to 704x704 | PASS (>= 0.45, no hard cut) | 0.957, 0.727, 0.615 | `01-frames-tile.png`: same woman, same rooftop and brick wall throughout; a slow dolly-in/zoom |
| 1d | AC-3 orientation | PASS for square input; not testable for portrait, see F1 | still 1024x1024, clip 704x704 | |
| 2a | Second still "portrait photo of a man with short hair smiling…" | PASS | `0e2acc4f-ae68-4c4e-bcb3-0fde76f91f30`, `modal` | `02-still2.png` not captured, see F3; API `images` present |
| 2b | Face swap: "Use as face swap target" on the woman's still, man's still as Face, Swap face · 8 credits | PASS | job `cf9d0ef2-f575-43e5-9627-57598421c642`, `modal-faceswap`, 48 s, on stage and in rail after finishing | `02-swap-seeded.png`, `02-swap-result.png` |
| 2c | Face swap share page signed out | PASS: `/v/cf9d0ef2…` shows the image, no credits UI; caption reads "1 stills" (grammar, F5) | | `05-share-swap.png` |
| 3 | Sequence via API: 2 clips, XFADE, `trim_start_ms` 500 / `trim_end_ms` 4000 each | PASS | POST 202, job `42e05b9f-08be-4876-bdce-1cac0b608ab5`, `duration_ms` 6500, ffprobe 6.500 s, 1280x720, 24 fps, `ffmpeg`, rendered in 16 s; plays on `/v/42e05b9f…` ("2 shots · 0:07") | `04-seq-stage.png`, `05-share-seq.png` |
| 4 | `docs/tasks/T-011-7/showcase.json` | written; URLs are the public `pub-….r2.dev` URLs the API returned (not presigned) | | |

Second clip for step 3: `31f7324b-ef7b-4a7a-999e-df50ebba7054` (Slow Drift, from the man's still, `modal`, 159 s). Clips used: `739eab6b…` and `31f7324b…`.

## Face swap verdict (honest)
`02-swap-tile.png` shows the man's face, the woman's still and the result. The result is a real transplant: the man's eyes, nose, brow and skin tone are in the woman's scene, and the rooftop, light and hair are unchanged. Weaknesses: his smile is lost (neutral mouth), the face is a little soft/plasticky, and a male face on long female hair with a slim neck reads as uncanny. Good enough as a demo of the feature, not flawless; I would show it small.

## Findings
- **F1 (medium):** choosing Portrait in the Still tab gave a 1024x1024 image (both stills square), so the aspect chip is ignored or mapped to 1:1. Please check `image-jobs` aspect handling. AC-3 for portrait input is therefore unverified.
- **F2 (minor):** a face-swap result has no "Animate this" (StageActions shows it for kind `image` only), so the second clip came from the man's still. Fine if intended.
- **F3 (minor):** the first still-2 wait for "Use as face swap target" on the stage timed out after 5 min even though the job had succeeded (API status `succeeded`, 1 image); reloading `?item=<id>` showed the button. Possible stage refresh race after generating a second still; not reproduced further.
- **F4 (minor):** the credits popover did not close on Escape.
- **F5 (nit):** share caption "1 stills".
- **Top-up:** to afford the second clip I used the product's "Add demo credits (100)" once (balance 12 -> 112). That is a demo feature, not a bypass of rate limits.

Console: only the cold-visit `/me` 401. Timings: still 83 s, clip 161 s, swap 48 s, second clip 159 s, sequence 16 s.
