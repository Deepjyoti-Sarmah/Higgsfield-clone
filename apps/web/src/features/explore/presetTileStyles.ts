import type { PresetCategory } from "../../api/presets"

export const presetTileStyles: Record<PresetCategory, string> = {
  camera: "bg-gradient-to-br from-accent/40 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
  cinematic: "bg-gradient-to-tr from-accent/30 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
  dynamic: "bg-gradient-to-bl from-accent/20 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
}

export const DEFAULT_TILE_CLASSES = "bg-gradient-to-br from-border via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none"

export const TILE_ASPECTS = ["aspect-[3/4]", "aspect-[9/16]", "aspect-[4/5]"] as const

// Fixed 12-pattern, not index % 3: columns fill sequentially, so a round-robin
// repeats the same stack in every column (banded wall). This order keeps flat
// neighbours unequal and every 2/3/4-column chunk varied and distinct.
export const TILE_ASPECT_PATTERN = [0, 1, 2, 1, 2, 0, 2, 0, 1, 0, 2, 1] as const
