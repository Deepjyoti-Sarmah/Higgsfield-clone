# T-050 studio UX and sequence flow: verification report

Date: 2026-09-26 (UTC). Orchestrator: deepseek-flash. Workers: two background subagents (T1, T2).

## What was asked

The start page demo media repeated the same few subjects; the studio did not say what each
section does; the generations rail was hard to read; face swap felt rough; and the Sequence
editor did not let you add video, swap a face into a clip, and export.

## Tasks, in order

| Task | Scope | Result |
|---|---|---|
| T3a (API) | A sequence could only cut plain `video` jobs, so a face-swapped video could never be used. Allowed `video_faceswap` in `ELIGIBLE_CLIP_KINDS` and added an API test. | PASS |
| T1 | Rebuilt the start page into a four-tool tour and a demo gallery over all 12 motion previews plus the 4 real stills, grouped by source subject. | PASS |
| T2 | Each studio tool now shows its step, purpose, what you get, and next step. Persistent "How this works" switcher. Rail gets a "Your work" header, count, "New still", and fixes the Swaps filter to include video swaps. | PASS |
| T3b | Rebuilt the Sequence composer: a film timeline with per-shot Swap, trim, reorder, transitions; an "Add a shot" panel that accepts clips and swapped videos; music; render + export guidance. | PASS |
| T3c | Wired the per-shot Swap to seed the Face swap tool with that clip and open the Video target tab. | PASS |
| T4 | No-slop pass on face-swap and sequence copy; removed every em dash from the copy modules. | PASS |

## Verification (orchestrator re-ran everything)

- API: `uv --directory apps/api run pytest -q` -> **298 passed**.
- New API test `test_face_swapped_video_can_join_a_sequence` passes; 10/10 in `test_sequence_jobs_api.py`.
- Web: `npm --prefix apps/web run lint` -> clean; `typecheck` -> clean; `test` -> **133 passed**; `build` -> ok.
- `scripts/check-standards` -> **ok (0 violations)**.
- Playwright (`docs/verification/T-050/capture.py`) on `http://127.0.0.1:8000` with a mocked library:
  full-page and viewport shots at 1440 light + dark and 390 light + dark.
  The handoff check printed `HANDOFF face-swap selected: true | video target selected: true`.

Screenshots: `start-{light,dark}-1440.png`, `studio-still-*-1440.png`, `studio-sequence-*-1440.png`,
`studio-faceswap-*-1440.png`, `studio-sequence-*-390.png`, `swap-handoff-light-1440.png`.

## Live deployment and end-to-end (2026-09-26)

Deployed from `main` (commit `8423144`): Railway `api` + `worker` built and pushed, live bundle
`index-z49uLk9P.js` matches a clean local build byte for byte. The video face-swap Modal app
`higgsfield-video-face-swap` was deployed and `MODAL_VIDEO_FACESWAP_ENDPOINT_URL` set on both
services. `/api/health/deep` is 5/5 ok and live `/openapi.json` exposes `video-faceswap-jobs`.

The first live run caught a real bug: `complete_run` dropped `GenerationResult.duration_ms`, so
every real clip stored a null length and video face swap rejected it with `target duration unknown`.
Fixed in `generation_runs.py`; a one-off backfill (`apps/api/scripts/backfill_clip_durations.py`)
set the real duration on **36 existing clips** (1 orphan object skipped).

The second live run passed end to end (guest `07fc95e8...`, 43 credits):
- source face: FLUX image `d608463f`
- target clip: LTX `e3e4c9ab` (modal)
- **video face swap: `797a94e0`, `generated_by=modal-video-faceswap`, 704x704 h264 + aac, 5.01s**
- **sequence with the swapped video: `2b350261`, 1280x720 h264, 9.54s**
- credits settled: balance 17, spent 43

Evidence: `live/target-clip-poster.jpg` vs `live/swap-poster.jpg` (the face changes; the target's
pose, clothing and light stay), `live/sequence-poster.jpg`, and the live screenshots in `live/`.

## Honest limits

1. **No new demo imagery was generated.** The gallery now shows the 4 real FLUX stills with their
   12 motion previews grouped by source, so it reads as "four stills, twelve moves" instead of
   one repeated face. Genuinely new subjects need a paid FLUX run; this machine has no Modal
   credentials (`/api/health/deep` reports the video backend unconfigured), so no spend happened.
2. **Face-swap output quality is backend.** The Modal `face_swap` model was not touched. What
   changed is the flow around it (guidance, copy, seeding a clip from a sequence shot).
3. **Deployed and live-tested, but with a fresh guest.** The user's own rail clips were backfilled
   to real durations; a re-run with their account would be the last confirmation.
4. **Screenshots use a mocked rail.** Local generation backends are placeholder/local, so the
   library list was intercepted in the browser. The Sequence editor, per-shot Swap, and face-swap
   seeding are the real app code paths.
5. T1's gallery autoplays up to 12 muted preview videos. It matches the existing preset-picker
   pattern but is heavier than a still-only grid on low-end devices.
