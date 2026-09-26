// §9 voice: film-editing words, short and concrete, no exclamations.
export const startCopy = {
  headline: "Stills that move. Clips that cut together.",
  pitch:
    "Make stills, animate them with a motion preset, cut them into a sequence, and swap a face into a photo or a clip.",
  cta: "Open the studio",
  steps: {
    still: { label: "Still", caption: "Prompt to picture: describe a scene and get a still." },
    clip: {
      label: "Clip",
      caption: "Still to video: add a motion preset and render a 5 second clip.",
    },
    sequence: { label: "Sequence", caption: "Cut clips into one film with transitions." },
    faceSwap: { label: "Face swap", caption: "Put a face into a photo or a clip." },
  },
  galleryHeading: "Preset previews",
  galleryIntro:
    "Every motion preset we ship, rendered on our own stills, with the four stills they start from.",
  chipsHeading: "Motion presets",
} as const

export type StepTool = keyof typeof startCopy.steps
