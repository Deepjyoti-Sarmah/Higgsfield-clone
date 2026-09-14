import type { PresetCategory } from "../../api/presets"

export function creditCost(credits: number): string {
  return `${credits} credits`
}

export function recreateAriaLabel(name: string): string {
  return `Recreate ${name}`
}

export function previewAlt(name: string): string {
  return `${name} preview`
}

const categoryLabels: Record<PresetCategory, string> = {
  camera: "Camera",
  cinematic: "Cinematic",
  dynamic: "Dynamic",
}

export function categoryLabel(category: string): string {
  return categoryLabels[category as PresetCategory] ?? category
}

export const exploreCopy = {
  hero: {
    h1: "Make your next video",
    subtitle:
      "Pick an effect, drop in a photo, and generate a 5-second clip. Start free as a guest.",
    primaryCta: "Start creating",
    primaryHref: "/create/video",
    secondaryCta: "Browse effects",
    secondaryHref: "#effects",
  },
  gallery: {
    title: "Effects",
    subtitle: "Every effect is a camera move you can apply to your own photo.",
    headerCta: "Try for free",
    headerCtaHref: "/create/video",
    cardCta: "Recreate",
    categoryLabels,
    categoryLabel,
    creditCost,
    recreateAriaLabel,
    previewAlt,
  },
  states: {
    loading: {
      skeletonCount: 6,
      srText: "Loading effects",
    },
    error: {
      title: "We couldn't load the effects.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
    empty: {
      title: "No effects yet.",
      body: "Effects will appear here as soon as they are published.",
    },
  },
}
