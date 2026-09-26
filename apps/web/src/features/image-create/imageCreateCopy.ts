export function promptCounter(value: number): string {
  return `${value}/500`
}

export function countValue(count: number): string {
  return `${count}`
}

// The design seals the cost label with a middle dot; the escape keeps this file ASCII.
export function withCost(cost: number): string {
  return `Generate \u00b7 ${cost} credits`
}

export function balanceKnown(balance: number): string {
  return `Balance: ${balance} credits`
}

export function insufficient(balance: number, required: number): string {
  return `You have ${balance} credits. This still needs ${required}.`
}

export const imageCreateCopy = {
  page: {
    title: "Make a still",
    subtitle: "Describe the scene, pick its shape, and generate up to four.",
  },
  prompt: {
    label: "Prompt",
    placeholder: "Describe the scene you imagine",
    counter: promptCounter,
  },
  settings: {
    aspectLabel: "Aspect ratio",
    qualityLabel: "Quality",
    countLabel: "Number of images",
    aspectLabels: {
      "1:1": "Square",
      "4:5": "Portrait",
      "3:2": "Landscape",
      "16:9": "Wide",
      "9:16": "Vertical",
    },
    qualityLabels: {
      standard: "Standard",
      high: "High",
    },
    countValue,
  },
  generate: {
    label: "Generate",
    withCost,
    blockedNoPrompt: "Describe the image first.",
    optionsUnavailable: "Wait for the options to load, or retry.",
    submitting: "Starting...",
    balanceKnown,
    balanceLoading: "Checking your credits...",
    balanceError: "Balance unavailable.",
    insufficient,
    sessionError: "Your session ended. Reload to continue.",
    invalid: "That didn't go through. Try again.",
    network: "Couldn't reach the server.",
    limitHit: "That's today's job limit. It resets at midnight UTC.",
    creditsOpened: "Not enough credits. The credits panel is open.",
  },
  states: {
    optionsError: {
      title: "We couldn't load the image options.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
    loading: {
      srText: "Loading image options",
    },
  },
} as const
