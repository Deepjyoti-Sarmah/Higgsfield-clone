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
  return `You have ${balance} credits. This image needs ${required}.`
}

export function imageAlt(index: number, prompt: string): string {
  return `Generated image ${index}: ${prompt}`
}

export const imageCreateCopy = {
  page: {
    title: "Create image",
    subtitle: "Describe an image, pick its shape, and generate up to four.",
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
    submitting: "Starting...",
    balanceKnown,
    balanceLoading: "Checking your credits...",
    balanceError: "Balance unavailable.",
    insufficient,
    getCredits: "Get credits",
    getCreditsHref: "/credits",
    sessionError: "Your session ended. Reload to continue.",
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
  progress: {
    queued: "Queued",
    running: "Generating your image...",
    succeeded: "Your images are ready.",
  },
  result: {
    imageAlt,
    download: "Download",
    makeAnother: "Make another",
    placeholderNotice: "Demo placeholder images - a real image model ships later.",
  },
  failure: {
    title: "This generation failed and its credits were refunded.",
    missing: "This generation is no longer available.",
    retry: "Try again",
  },
}
