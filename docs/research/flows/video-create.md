# Flow: Video create (image + preset → video)

**Source:** screenshot `16`, signed in, empty state only.
**Observation only.**

## Entry point
- Top nav "Video".
- It's probably also reached from Explore: "Recreate" on an effect tile, and the tool cards. That link isn't confirmed.

## Layout
### Left panel (control column, ~400px)
- **Tabs:** `Create Video` (active) · `Edit Video` · `Motion Control`.
- **Preset card:**
  - A thumbnail image with the preset name in accent caps ("GENERAL") and the model underneath ("Seedance 2.5").
  - A "✎ Change" button in the corner.
- **Segmented toggle:** `References` (active) · `Extend Video`.
- **Drop zone:** 3 icons (image, video, audio), "Add references", "Image, Video or Audio".
- **Prompt box:**
  - Placeholder asks for the visual change you want, gives short examples, and mentions adding references with `@`.
  - Chips below it: `@ Elements`, and `🔊 On` (audio toggle).
- **Model row:** "Model · Seedance 2.5" with a signal-bars icon and a `>` chevron.
- More settings rows are partly hidden below the model row, likely duration, resolution and aspect ratio. Not confirmed.
- **Sticky Generate button:** "Generate ✦ ~~80~~ 45", a credit cost with a discounted price.

### Right panel (canvas)
- **Top:** `History` (folder icon) and `How it works` (book icon, active).
- **"How it works" empty state:**
  - Heading "Make videos in one click".
  - Subline: 250+ presets for camera control, framing and VFX, or the general preset for manual control.
  - **3 step cards:**
    1. **Add image:** an upload tile with "Upload image" and "Paste from clipboard". Copy: upload or generate an image to start.
    2. **Choose preset:** a horizontal carousel of preset tiles, each with a looping preview and a name overlay ("…ACKING", "MINIMALISM CORPORATE"). The selected tile has an accent border.
    3. **Get video:** a playing result preview. Copy: click generate to create the final animated video.
- **Bottom right:** the same "Get personal 55% OFF" countdown toast.

## Core concepts observed
- **Preset:**
  - A named motion/VFX template, 250+ of them, previewed as a looping video.
  - Selecting one changes the preset card at the top left.
  - "General" is the free-form, manual-control preset.
- **Model:** chosen separately from the preset (Seedance 2.5 shown).
- **References:** image, video or audio inputs, which can be tagged into the prompt with `@`.
- **History:** past generations live in the right panel, next to "How it works".

## UI states
- **Observed:** empty / onboarding ("How it works").
- **Not observed:** preset picker opened via "Change", uploading, generating/progress, result, history list, error, out of credits.

## Credits / cost
- About 5–10× the cost of an image generation (45 vs 6.5 discounted).
- Shown on the Generate button before submitting.

## Friction noticed
- **Two overlapping upload entry points:** the "Add references" drop zone on the left and "Upload image" in the onboarding cards on the right. Which one the generation uses isn't clear.
- **Crowded left column:** 3 tabs + a segmented toggle + references + prompt + chips + model, before any settings are visible.
- **Two sticky promos at once:** discount toast, strikethrough prices.
