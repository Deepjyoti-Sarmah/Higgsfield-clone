// Studio composer guidance copy: per-tab explainer + first-run flow strip.
export const studioCopy = {
  explainer: {
    still: {
      title: "Still — make a picture",
      body: "Make a picture from a prompt — then animate it in Clip.",
    },
    clip: {
      title: "Clip — animate a still",
      body: "Animate a still with a motion preset — then cut clips in Sequence.",
    },
    sequence: {
      title: "Sequence — cut one film",
      body: "Cut 2–6 clips + optional music into one film — then Render & share.",
    },
    faceswap: {
      title: "Face swap — swap one face",
      body: "Put one face into a target photo — result lands in your rail.",
    },
  },
  rail: {
    filterLabel: "Filter generations by kind",
    filters: {
      all: "All",
      image: "Stills",
      video: "Clips",
      sequence: "Sequences",
      faceswap: "Swaps",
    },
    emptyTitle: "No generations yet.",
    emptyBody: "Make your first still — then animate it in Clip.",
    emptyAction: "Make a still",
    filteredEmptyTitle: "Nothing of this kind yet.",
    filteredEmptyAction: "Show everything",
  },
  flowStrip: {
    heading: "Make your first film in three steps",
    steps: [
      { tab: "still", label: "Still", caption: "Prompt to picture" },
      { tab: "clip", label: "Clip", caption: "Still to 5s clip" },
      { tab: "sequence", label: "Sequence", caption: "Clips to one film" },
    ],
    dismiss: "Dismiss",
  },
} as const
