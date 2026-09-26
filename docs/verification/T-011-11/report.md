# T-011-11 final re-check of the T-011-8 findings

Site https://api-production-8afc.up.railway.app, bundle `index-R-EkZHcQ.js`, fresh guest (60 credits), Playwright + Chromium. No code changed. **Overall: PASS, 7 of 7.**

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | F1: Portrait still is 832x1216, job aspect `4:5` | PASS | still `de0f8114-045a-4fb0-a9aa-df6b463c2a3f`: downloaded PNG is 832x1216 (ffprobe); `GET /api/v1/image-jobs/{id}` has `aspect_ratio: "4:5"`. `01-still-stage.png` |
| 2 | F2: face swap result shows "Animate this" | PASS | swap `37919e75-6b59-4b11-8ba6-51afbb812f29` (`modal-faceswap`, target = the still, face = uploaded man photo): the stage shows "Animate this" (1 button). `02-swap-stage.png` |
| 3 | F4: credits popover closes on Escape, focus returns to the credits button | PASS | after Escape the dialog was gone and `document.activeElement` had `aria-label="Credits"`. `03-popover-open.png` |
| 4 | F5: single-still share page says "1 still" | PASS | `/v/de0f8114…` signed out: "Still | 1 still". `04-share-still.png` |
| 5 | Trim UI: steppers, total readout, Render sends trims, duration matches | PASS | two uploaded clips (`c41f07e2-68d7-4810-804a-2f6526519f65`, `179a5cc9-355d-4a03-92cb-d3040d5d86d9`) with XFADE. Before: each `0:00.0–0:05.0`, total `about 0:10`. After start later once and end earlier twice on each shot: `0:00.5–0:04.0`, total `about 0:07`. POST body: `trim_start_ms":500,"trim_end_ms":4000` on both clips. Result `664df57b-b8ba-426f-8044-55a672f93ea4`: `duration_ms` 6500, plays on the stage. `05-trim-before.png`, `05-trim-after.png`, `05-seq-result.png` |
| 6 | Start page showcase and top-bar links | PASS | 4 showcase cells with captions "still", "clip · dolly in · 0:05", "face swap", "2 shots · 0:07" (real media, not test patterns); header links "Studio" -> `/studio`, "Face swap" -> `/studio?tab=faceswap`. `06-start.png` |
| 7 | 390px dark, no horizontal scroll | PASS | `/` and `/studio`: `scrollWidth` 390 = `innerWidth` 390. `07-mobile-start.png`, `07-mobile-studio.png` |

Console: only the cold-visit `GET /api/v1/me` 401. Credits: 60 -> 42 after still and swap; two clips and one sequence left 1 credit.
