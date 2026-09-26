import type { components } from "../../api/generated/schema"

type JobKind = components["schemas"]["PublicJobResponse"]["kind"]

// §9 voice for the share viewer; the viewer shows no studio or credits UI.
export function documentTitle(name: string): string {
  return `${name} \u00b7 Reel & Still`
}

export function shareTitle(job: { kind: JobKind; preset_name: string | null }): string {
  if (job.kind === "sequence") return "Sequence"
  // faceswap renders like a still, same as an image job.
  if (job.kind === "image" || job.kind === "faceswap") return "Still"
  return job.preset_name ?? "Clip"
}

export function formatSeconds(ms: number | null): string | null {
  if (ms === null || ms === undefined) return null
  const seconds = Math.max(0, Math.round(ms / 1000))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`
}

// Meta lines: "clip · 0:05", "3 shots · 0:14", "2 stills".
export function shareMeta(job: {
  kind: JobKind
  clip_count?: number | null
  duration_ms?: number | null
  image_urls: string[]
}): string {
  const duration = formatSeconds(job.duration_ms ?? null)
  if (job.kind === "sequence") {
    return [`${job.clip_count ?? 0} shots`, duration].filter(Boolean).join(" \u00b7 ")
  }
  if (job.kind === "image" || job.kind === "faceswap") return `${job.image_urls.length} stills`
  return ["clip", duration].filter(Boolean).join(" \u00b7 ")
}

export const shareCopy = {
  page: {
    cta: "Make your own",
    ctaHref: "/studio",
    documentTitle,
    shareTitle,
    shareMeta,
  },
  states: {
    loading: {
      srText: "Loading this page",
    },
    error: {
      title: "We couldn't load this page.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
    notFound: {
      title: "This page doesn't exist or was removed.",
      body: "Check the link, or make your own.",
      action: "Make your own",
    },
    notReady: {
      title: "Still rendering.",
      body: "This isn't ready yet. Check back in a moment.",
      action: "Refresh",
    },
    failed: {
      title: "This didn't finish.",
      body: "Something went wrong while it was being made.",
      action: "Make your own",
    },
  },
  result: {
    download: "Download",
  },
}
