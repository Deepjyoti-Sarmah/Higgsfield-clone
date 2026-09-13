# Product map: higgsfield.ai surfaces and verdicts

Filled in by `docs/playbooks/research-flow.md`. Verdicts follow the priorities in `docs/PLAN.md`.

**Status:** DRAFT. It needs the user's approval (the M1 exit gate). Evidence so far covers 16 screenshots and 3 flows.

## Observed surfaces
| Surface | Flow doc | Signed out? | Verdict | Reason |
|---|---|---|---|---|
| Explore: hero + tool cards | `flows/explore.md` (01) | unknown | **P0** (simplified) | It's the first impression and the signed-out landing page. We keep the hero + tool cards and drop the promos |
| Explore: effects/preset gallery with hover "Recreate" | `flows/explore.md` (03) | unknown | **P0** | The main entry into creation. "Recreate" opens Video create with that preset selected. We show names without needing hover (works on touch) |
| Explore: model galleries (video, image) | `flows/explore.md` (05, 08, 12) | unknown | **P1** | Showcase only. One gallery of our own sample outputs is enough |
| Video create: image + preset + prompt → video | `flows/video-create.md` (16) | no | **P0** | The core product loop. One upload entry point instead of two |
| Video create: preset picker ("Change", 250+ presets) | `flows/video-create.md` (16) | no | **P0** (~12 presets) | Presets are what set Higgsfield apart. A curated set of prompt/camera templates covers the demo |
| Video create: model picker | `flows/video-create.md` (16) | no | **P2** | One default model (LTX-2.5 on Modal) keeps the budget and the UI simple |
| Video create: History panel | `flows/video-create.md` (16) | no | **P0** | Needed to see progress and results; becomes the "My generations" library |
| Generate button shows the credit cost up front | `flows/image-create.md`, `flows/video-create.md` | no | **P0** | Cheap to build, builds trust, and ties into the credit ledger. No fake strikethrough discounts |
| Assets (top nav) | — (not captured) | no | **P0** (merged with History) | One library for every output |
| Image create: prompt + aspect/quality/count → images | `flows/image-create.md` (15) | no | **P1** | Second creation mode. Images can also be generated and fed into Video create |
| Pricing page | — (not captured) | yes | **P1** | Credits with a fake top-up covers the money flow (D-007) |
| AI Face Swap (footer link) | — (not captured) | — | **P1** | Image-only, via an edit model (D-004) |
| Community projects / profiles / likes | `flows/explore.md` (06, 10) | unknown | **P2** | A social layer isn't needed for the core loop. Share pages (`/v/{id}`) cover the growth loop |
| Search | global chrome | — | **P2** | Only needed once there's a lot of content |
| Edit Video, Motion Control, Extend Video, references (video/audio), `@Elements` | `flows/video-create.md` (16) | no | **CUT** | Advanced modes that need heavier models |
| Genjutsu (video character replacement) | `flows/explore.md` (04) | — | **CUT** | Needs Viggle-class 33B models (D-002) |
| Audio, Lipsync Studio | nav, footer | — | **CUT** | Different modality, not needed for the core loop |
| MCP / ChatGPT Plugin / Supercomputer agent | nav, 02, 07 | — | **CUT** | Platform and integration plays, not the product loop |
| Cinema Studio, Marketing Studio, Canvas, Photodump, Fashion/UGC Factory | nav, 09, 11 | — | **CUT** | Specialised studios built on the same generation core |
| Promo tasks, countdown timers, discount toasts | 01, 15, 16 | — | **CUT** | Dark patterns that crowd the creation UI. Leaving them out is part of "better than the original" |
| Notifications bell, Enterprise | nav | — | **CUT** | Not needed for a single-user demo |
| Upscale, Inpaint, Edit Image | footer, 13 | — | **P2** | Nice follow-ups once images exist |

## Not yet observed (needed before specs; please capture)
1. **Sign-up / sign-in** screens and the first-run experience (free credits?).
2. **Video create in action:**
   - the preset picker after clicking "Change"
   - upload done
   - generating / progress
   - result view
   - History list
3. **Image create in action:** generating, results grid, image detail.
4. **Effects "Recreate"** click-through: where it lands and what's pre-filled.
5. **Assets** page, **Pricing** page, and an out-of-credits state.
6. **Share / public view** of a generation: the page someone opens from a link.
7. Explore **signed out** (what a new visitor sees).

## "Better than the original" themes (from friction noticed)
- One clear primary action per screen, instead of stacked promos and countdowns.
- 5 nav items at most: Explore, Create video, Create image, Library, Credits.
- Preset names visible without hover, and a single upload entry point.
- Honest pricing on the Generate button (the real cost, no strikethroughs).
- Settings chips with labels (no two unlabelled "Auto" chips).
