import type { Preset } from "../../api/presets"

export type PresetGroup = {
  category: string
  presets: Preset[]
}

const CATEGORY_ORDER = ["camera", "cinematic", "dynamic"] as const

function isKnownCategory(category: string): boolean {
  return (CATEGORY_ORDER as readonly string[]).includes(category)
}

function collectByCategory(presets: Preset[]): Map<string, Preset[]> {
  const groups = new Map<string, Preset[]>()
  for (const preset of presets) {
    const bucket = groups.get(preset.category)
    if (bucket) bucket.push(preset)
    else groups.set(preset.category, [preset])
  }
  return groups
}

function toGroup(category: string, groups: Map<string, Preset[]>): PresetGroup {
  return { category, presets: groups.get(category) ?? [] }
}

export function groupPresetsByCategory(presets: Preset[]): PresetGroup[] {
  const groups = collectByCategory(presets)
  const known = CATEGORY_ORDER.filter((category) => groups.has(category)).map((category) =>
    toGroup(category, groups),
  )
  const unknown = [...groups.keys()]
    .filter((category) => !isKnownCategory(category))
    .map((category) => toGroup(category, groups))
  return [...known, ...unknown]
}
