import type { LibraryItem } from "../../api/library"

export type RailKindFilter = "all" | "image" | "video" | "sequence" | "faceswap"

export type RailKindCounts = Record<RailKindFilter, number>

const EMPTY_COUNTS: RailKindCounts = { all: 0, image: 0, video: 0, sequence: 0, faceswap: 0 }

export function matchesRailKindFilter(item: LibraryItem, filter: RailKindFilter): boolean {
  if (filter === "all") return true
  return item.kind === filter
}

export function countRailKinds(items: LibraryItem[]): RailKindCounts {
  const counts: RailKindCounts = { ...EMPTY_COUNTS, all: items.length }
  for (const item of items) {
    if (item.kind in counts) counts[item.kind as Exclude<RailKindFilter, "all">] += 1
  }
  return counts
}
