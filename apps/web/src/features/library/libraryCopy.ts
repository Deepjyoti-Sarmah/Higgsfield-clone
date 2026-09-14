import type { LibraryItem } from "../../api/library"
import { formatCreatedAt } from "./formatCreatedAt"

export function openLabel(name: string): string {
  return `Open ${name}`
}

// Video items show their preset name; image items have no preset, so the prompt is the label.
export function itemLabel(item: LibraryItem): string {
  if (item.kind === "image") return item.prompt ?? "Image"
  return item.preset_name ?? item.preset_slug ?? "Video"
}

const statusLabels: Record<LibraryItem["status"], string> = {
  queued: "Queued",
  running: "Generating",
  succeeded: "Ready",
  failed: "Failed",
}

export const libraryCopy = {
  page: {
    title: "Library",
    subtitle: "Everything you have generated.",
  },
  states: {
    loading: {
      skeletonCount: 4,
      srText: "Loading your library",
    },
    error: {
      title: "We couldn't load your library.",
      body: "Check your connection and try again.",
      action: "Retry",
    },
    empty: {
      title: "No generations yet.",
      body: "Generate your first video and it will show up here.",
      action: "Create video",
    },
  },
  item: {
    status: statusLabels,
    failedFallback: "This generation failed and its credits were refunded.",
    missing: "This generation is no longer available.",
    openLabel,
    label: itemLabel,
    viewing: "Viewing",
  },
  result: {
    download: "Download",
    makeAnother: "Make another",
    close: "Close",
    fallbackHeading: "Generation",
  },
  time: {
    label: formatCreatedAt,
  },
}
