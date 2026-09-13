import type { PresetCategory } from "../../api/presets"

export const presetTileStyles: Record<PresetCategory, string> = {
  camera: "bg-gradient-to-br from-accent/40 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
  cinematic: "bg-gradient-to-tr from-accent/30 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
  dynamic: "bg-gradient-to-bl from-accent/20 via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none",
}

export const DEFAULT_TILE_CLASSES = "bg-gradient-to-br from-border via-surface to-bg transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none"
