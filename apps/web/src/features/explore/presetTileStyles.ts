import type { PresetCategory } from "../../api/presets"

export const presetTileStyles: Record<PresetCategory, string> = {
  camera: "bg-gradient-to-br from-accent/30 to-bg",
  cinematic: "bg-gradient-to-tr from-accent/20 to-bg",
  dynamic: "bg-gradient-to-bl from-accent/10 to-bg",
}

export const DEFAULT_TILE_CLASSES = "bg-gradient-to-br from-border to-bg"
