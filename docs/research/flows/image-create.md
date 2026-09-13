# Flow: Image create (text → image)

**Source:** screenshot `15`, signed in, empty state only.
**Observation only.**

## Entry point
- Top nav "Image" (active item highlighted in accent colour).
- Footer links also point here: "AI Image", and "Image Models" for specific models.

## Layout (empty state)
- **Centre:**
  - A fanned stack of 4 sample photos.
  - Heading "Start creating with" + a model name in accent colour ("Higgsfield Soul Cinema").
  - Subline: "Describe a scene, character, mood, or style — and watch it come to life".
- **Top right:** a slider control, probably grid/thumbnail size for results. Its purpose isn't confirmed.
- **Bottom right:** a collapsible toast, "Get personal 55% OFF · Expires in 01h 42m 11s".

## Composer (docked bottom bar, full width)
| Control | Observed value | Notes |
|---|---|---|
| `+` button | — | probably attaches reference image(s) |
| Prompt input | placeholder "Describe the scene you imagine" | single line |
| Model picker | "GPT Image 2" with a `>` chevron | the model name here differs from the heading's model name |
| Aspect ratio | "Auto" | frame icon |
| Quality | "High" | |
| Resolution | "2K" | |
| Unknown | "Auto" | icon suggests a style or camera option; not confirmed |
| Count stepper | `− 1/4 +` | number of images per generation, max 4 |
| Generate | "Generate ✦ ~~8.5~~ 6.5" | credit cost shown on the button, with a discounted price next to the struck-through original |

## UI states
- **Observed:** empty.
- **Not observed:** typing, generating/progress, results grid, error, out of credits, history.

## Credits / cost
- The cost is shown **before** generating, on the button itself, and changes with the settings (presumably).

## Friction noticed
- The heading promotes one model while the composer defaults to a different one, which is confusing.
- Four icon-plus-word chips ("Auto", "High", "2K", "Auto") have no labels, and two of them both read "Auto".
- A discount timer toast overlaps the working area.
