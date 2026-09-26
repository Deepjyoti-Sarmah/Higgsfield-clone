export function withCost(cost: number): string {
  return `Swap face · ${cost} credits`
}

export function insufficient(balance: number, required: number): string {
  return `You have ${balance} credits. This swap needs ${required}.`
}

export const faceSwapCopy = {
  face: {
    label: "Face",
    hint: "The face to use",
  },
  target: {
    label: "Target",
    hint: "The picture to put it in",
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
    notFinishedError: "Upload didn't finish. Try again.",
    seededLabel: "From the stage",
    seededRemove: "Replace",
  },
  submit: {
    withCost,
    label: "Swap face",
    submitting: "Starting...",
    blockedNoFace: "Add a face image first.",
    blockedNoTarget: "Add a target image first.",
    blockedUploading: "Wait for the upload to finish.",
    insufficient,
    limitHit: "That's today's job limit. It resets at midnight UTC.",
    invalid: "That combination didn't work. Try different images.",
    networkToast: "Couldn't reach the server.",
    creditsOpened: "Not enough credits — the credits panel is open.",
  },
} as const
