import type { LibraryItem } from "../../api/library"

// Title: the prompt, the preset name, or the sequence shot count (DESIGN.md §4).
export function railItemTitle(item: LibraryItem): string {
  if (item.kind === "sequence") {
    return `Sequence · ${item.clip_count ?? 0} shots`
  }
  if (item.kind === "faceswap") return "Face swap"
  if (item.prompt) return item.prompt
  if (item.preset_name) return item.preset_name
  return "Untitled"
}

export function railItemMeta(item: LibraryItem): string {
  const parts: string[] = [item.kind]
  if (item.duration_ms !== null && item.duration_ms !== undefined) {
    const seconds = Math.round(item.duration_ms / 1000)
    parts.push(`0:${String(seconds).padStart(2, "0")}`)
  }
  return parts.join(" · ")
}
