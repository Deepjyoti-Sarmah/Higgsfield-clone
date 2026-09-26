# Spec 011: Output quality, face swap, clip trimming

**Status:** DONE (live, verified 2026-09-26) · was APPROVED (user, 2026-09-26: "make the images and videos that can be used and the face swap and video editing feature work … take inspiration from pixovid")  ·  **Priority:** P0 (resubmission day)
**Research refs:** the live audit on 2026-09-26 (below); Pixovid (`pixovid/`, ideas only, no code: separate tool entry points for Video / Image / Face swap, FaceFusion-style swap with a GFPGAN enhancer pass).

## Problem (measured, not guessed)
The latest real production clip (`kind=video`, `generated_by=modal`, 960×544) **ignores its input image**. Frame 0 matches the input; by frame 60 the model has invented an unrelated cartoon scene. Causes, confirmed in the code:
1. **Empty prompt.** `ModalAdapter` sends `request.prompt or ""`. When the user leaves the prompt blank, the chosen motion preset (e.g. `dolly-in`) is never described to the model.
2. **No input fitting.** `apps/gpu/ltx_spike.py` passes the raw image (e.g. 640×360) into a fixed 960×544 render, with no crop to the target aspect and no portrait output.
3. **Cold model on every call.** The endpoint runs `from_pretrained` per request, so a clip takes about 122 s.

Stills (FLUX.1-schnell, 1024², 4 steps) are acceptable, and they're the input to Animate this, so the clip pipeline is what must improve.

**Face swap doesn't exist in the product.** Sequences work, but "editing" is only reorder and transitions: there's no trim.

## Acceptance criteria
- **AC-1 Clip fidelity:** for a real photo input, the clip keeps the input's subject and scene for the whole clip. Checked by frame similarity between the input and frames 0, 60 and last (SSIM ≥ 0.45 against the fitted input, no hard scene cut). The motion matches the preset's description.
- **AC-2 Prompt always present:** the model always receives a non-empty prompt, built from the preset's motion description plus the user's text (if any) plus a fixed "keep the scene" and quality clause. Unit-tested.
- **AC-3 Orientation and fit:** the input is center-cropped to the output aspect. Landscape inputs render landscape and portrait inputs render portrait (dimensions multiples of 32).
- **AC-4 Warm model:** the pipeline loads once per container (`@modal.enter`). A warm clip is noticeably faster than 122 s (report the measured times).
- **AC-5 Face swap:** a user picks a **face** image and a **target** image (upload, or a still from the rail), pays the shown cost, and gets one image where the target's face is replaced by the source face. It uses a real swap model plus a face-restoration pass, on Modal. The job appears in the rail, on the stage, and on its share page. Failures (for example no face found) refund the credits with a clear message.
- **AC-6 Trim:** in the Sequence tab each clip has an in and out trim (0.5 s steps, at least 1 s kept). The stitcher honours it, and the total length readout uses it.
- **AC-7 Start page shows the real product:** the start page's step media and a small showcase use real outputs from the fixed pipeline, not test patterns. The top bar gets direct tool links (Studio · Face swap), in the spirit of Pixovid's tool entry points, keeping DESIGN.md's look.
- **AC-8 Verified live:** a browser pass on the public URL covers still → Animate this → clip (the AC-1 check), face swap, and a trimmed sequence, with screenshots and job ids.

## Out of scope
- Paid third-party APIs (no keys available), video face swap, avatars and templates, audio lip-sync.

## Risks
- **Model licences:** the face-swap weights (inswapper/hyperswap family) are non-commercial research licences. That's acceptable for an assignment demo; record it in DECISIONS.
- **GPU cost:** keep live test renders to what each brief needs.
