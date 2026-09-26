// Studio guidance copy: per-tool purpose, output, next step, and rail labels.
export const studioCopy = {
  tools: {
    still: {
      step: 1,
      label: "Still",
      purpose: "Make a picture from a written prompt.",
      output: "One still image, saved to your work.",
      next: "Open Clip to animate it.",
    },
    clip: {
      step: 2,
      label: "Clip",
      purpose: "Animate a still with a motion preset.",
      output: "One short clip, saved to your work.",
      next: "Add it to a sequence.",
    },
    sequence: {
      step: 3,
      label: "Sequence",
      purpose: "Cut clips and optional music into one film.",
      output: "One rendered film, saved to your work.",
      next: "Render, then share the link.",
    },
    faceswap: {
      step: 4,
      label: "Face swap",
      purpose: "Put one face into a still or a clip.",
      output: "The swapped still or clip, saved to your work.",
      next: "Animate or cut it like any other take.",
    },
  },
  toolOrder: ["still", "clip", "sequence", "faceswap"],
  guidance: {
    outputLabel: "What you get",
    nextLabel: "Next step",
  },
  stage: {
    empty: {
      title: "Nothing on the stage yet.",
      body: "The stage plays the still, clip, or sequence you select from your work. Start one with a tool in the composer below, or pick an item from the rail.",
      action: "Start with a Still",
    },
  },
  flowStrip: {
    heading: "How this works",
  },
  rail: {
    heading: "Your work",
    count: (total: number) => `${total} ${total === 1 ? "generation" : "generations"}`,
    newAction: "New still",
    filterLabel: "Filter your work by kind",
    filters: {
      all: "All",
      image: "Stills",
      video: "Clips",
      sequence: "Sequences",
      faceswap: "Swaps",
    },
    emptyTitle: "Nothing here yet.",
    emptyBody: "Make a still, or pick a preset from the start page. Your work lands here.",
    emptyAction: "Make a still",
    filteredEmptyTitle: "Nothing of this kind yet.",
    filteredEmptyBody: "Clear the filter to see everything.",
    filteredEmptyAction: "Show all",
  },
} as const
