import { useCallback, useState } from "react"
import { useSearchParams } from "react-router-dom"
import type {
  PresetCategoryFilter,
  PresetSelection,
  PresetsState,
} from "./createVideoTypes"

type SetSearchParams = ReturnType<typeof useSearchParams>[1]

function updatePresetParam(setSearchParams: SetSearchParams, slug: string | null) {
  setSearchParams(
    (params) => {
      if (slug === null) params.delete("preset")
      else params.set("preset", slug)
      return params
    },
    { replace: true },
  )
}

export function usePresetSelection(presets: PresetsState): PresetSelection {
  const [searchParams, setSearchParams] = useSearchParams()
  const [categoryFilter, setCategoryFilter] = useState<PresetCategoryFilter>("all")

  const selectedSlug = searchParams.get("preset")
  const selectedPreset = presets.presets.find((preset) => preset.slug === selectedSlug) ?? null
  const isUnknownSlug =
    presets.status === "ready" && selectedSlug !== null && selectedPreset === null

  const selectPreset = useCallback(
    (slug: string) => updatePresetParam(setSearchParams, slug),
    [setSearchParams],
  )
  const clearPreset = useCallback(
    () => updatePresetParam(setSearchParams, null),
    [setSearchParams],
  )

  return {
    selectedSlug,
    selectedPreset,
    isUnknownSlug,
    categoryFilter,
    setCategoryFilter,
    selectPreset,
    clearPreset,
  }
}
