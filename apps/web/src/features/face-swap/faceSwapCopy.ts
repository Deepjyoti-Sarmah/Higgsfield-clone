export function withCost(cost: number): string {
  return `Swap face · ${cost} credits`
}

export function renderWithCost(cost: number): string {
  return `Render video · ${cost} credits`
}

export function insufficient(balance: number, required: number): string {
  return `You have ${balance} credits. This swap needs ${required}.`
}

export const faceSwapCopy = {
  face: {
    label: "1 · Face: who to put in",
    hint: "Clear, front-facing photo, evenly lit.",
  },
  target: {
    label: "2 · Target: where to put them",
    hint: "Photo with a clearly visible face.",
    seedHint: "Tip: open a still on the stage and choose Use as face swap target.",
  },
  videoTarget: {
    label: "2 · Target video: what to swap into",
    hint: "A rail clip, or an mp4 up to 30 seconds / 50MB.",
    seedHint: "Tip: open a clip on the stage and choose Use as swap video.",
    dropTitle: "Drop an mp4",
    browse: "Browse",
    replace: "Replace",
    invalidType: "That file isn't an mp4. Pick a .mp4 file.",
    tooBig: "That video is over 50MB. Pick a shorter clip.",
    tooLong: "That video runs over 30 seconds. Pick a shorter clip.",
    readingDuration: "Reading video length…",
    renderNeedsRail: "Rendering needs a rail clip. Open one on the stage and choose Use as swap video.",
  },
  videoPreview: {
    title: "Check the face on one frame",
    body: "Runs the photo swap on the target's first frame, so you can check the face before paying for the full video.",
    action: "Preview keyframe · 8 credits",
    retry: "Preview again",
    working: "Making the preview…",
    ready: "Preview ready. Like the face? Render the full video below.",
    failed: "The preview didn't work. Try another face photo or target video.",
    insufficient: (cost: number) => `You need ${cost} credits for the preview.`,
  },
  videoRender: {
    renderWithCost,
    submitting: "Starting…",
    ready: "Ready to render the full video.",
    previewNote: "The keyframe preview is charged separately, 8 credits.",
    blockedNoFace: "Add a face image first.",
    blockedNoTarget: "Pick a target video first.",
    blockedTooLong: "This video is over the 30-second limit.",
    insufficient,
    limitHit: "That's today's job limit. It resets at midnight UTC.",
    invalid: "That video can't be swapped. It may be missing, over the limits, or from another account.",
    networkToast: "Couldn't reach the server.",
    creditsOpened: "Not enough credits. The credits panel is open.",
  },
  guidance: {
    title: "What makes a good swap",
    points: [
      "Use a clear, front-facing face photo, evenly lit.",
      "Pick a target with a clearly visible face.",
      "The result keeps the target's lighting and expression.",
    ],
  },
  image: {
    idleTitle: "Drop an image",
    idleBody: "or",
    draggingTitle: "Drop it here",
    browse: "Browse",
    retry: "Retry",
    hint: "JPEG, PNG or WebP, up to 10MB.",
    alt: "",
    networkError: "Couldn't reach the server. Try again.",
    sessionError: "Your session ended. Reload to continue.",
    notFinishedError: "Upload didn't finish, so this photo wasn't saved. Wait a moment, then retry.",
    seededLabel: "From the stage",
    seededRemove: "Replace",
  },
  submit: {
    withCost,
    label: "Swap face",
    submitting: "Starting…",
    ready: "Ready to swap the face.",
    blockedNoFace: "Add a face image first.",
    blockedNoTarget: "Add a target image first.",
    blockedUploading: "Wait for the upload to finish.",
    insufficient,
    limitHit: "That's today's job limit. It resets at midnight UTC.",
    invalid: "No face found in one of these photos. Try a front-facing photo with the face clearly visible.",
    networkToast: "Couldn't reach the server.",
    creditsOpened: "Not enough credits. The credits panel is open.",
  },
} as const
