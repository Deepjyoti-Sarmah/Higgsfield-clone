import { useEffect, useRef } from "react"
import type { RefObject } from "react"
import { createVideoCopy } from "./createVideoCopy"
import type { Preset, PresetsState, PresetSelection } from "./createVideoTypes"
import { PresetCard } from "./PresetCard"
import { PresetCategoryChips } from "./PresetCategoryChips"

type PresetPickerProps = {
  presets: PresetsState
  selection: PresetSelection
  previewImageUrl: string | null
  groupRef: RefObject<HTMLFieldSetElement | null>
}

const SKELETON_KEYS = [0, 1, 2, 3, 4, 5]

function PresetSkeletons() {
  return (
    <>
      <p className="sr-only">{createVideoCopy.preset.loading}</p>
      {SKELETON_KEYS.map((key) => (
        <div key={key} className="aspect-square animate-pulse rounded-xl bg-border/60" />
      ))}
    </>
  )
}

function PresetGrid({
  presets,
  selection,
  previewImageUrl,
  isLoading,
}: {
  presets: Preset[]
  selection: PresetSelection
  previewImageUrl: string | null
  isLoading: boolean
}) {
  const visible =
    selection.categoryFilter === "all"
      ? presets
      : presets.filter((preset) => preset.category === selection.categoryFilter)
  if (isLoading) return <PresetSkeletons />
  if (visible.length === 0) {
    const message =
      presets.length === 0
        ? createVideoCopy.preset.emptyList
        : createVideoCopy.preset.emptyFilter
    return <p className="col-span-3 text-sm text-muted">{message}</p>
  }
  return (
    <>
      {visible.map((preset) => (
        <PresetCard
          key={preset.slug}
          preset={preset}
          isSelected={preset.slug === selection.selectedSlug}
          previewImageUrl={previewImageUrl}
          onSelect={selection.selectPreset}
        />
      ))}
    </>
  )
}

// Deep links get one scroll into view; focus deliberately stays where the visitor put it.
function useScrollToSelectedPreset(
  isReady: boolean,
  slug: string | null,
  groupRef: RefObject<HTMLFieldSetElement | null>,
) {
  const hasScrolledRef = useRef(false)
  useEffect(() => {
    if (!isReady || slug === null || hasScrolledRef.current) return
    const checked = groupRef.current?.querySelector<HTMLInputElement>("input:checked")
    checked?.scrollIntoView({ block: "nearest" })
    hasScrolledRef.current = true
  }, [isReady, slug, groupRef])
}

function PresetDescription({ selectedPreset }: { selectedPreset: Preset | null }) {
  return (
    <p className="text-xs text-muted">
      {selectedPreset === null
        ? createVideoCopy.preset.descriptionIdle
        : createVideoCopy.preset.description(selectedPreset.name, selectedPreset.description)}
    </p>
  )
}

export function PresetPicker({
  presets,
  selection,
  previewImageUrl,
  groupRef,
}: PresetPickerProps) {
  useScrollToSelectedPreset(
    presets.status === "ready",
    selection.selectedPreset?.slug ?? null,
    groupRef,
  )
  return (
    <fieldset ref={groupRef}>
      <legend className="text-xs font-semibold uppercase tracking-wide text-muted">
        {createVideoCopy.page.presetSection}
      </legend>
      <div className="mt-3 flex flex-col gap-3">
        <PresetCategoryChips
          value={selection.categoryFilter}
          onChange={selection.setCategoryFilter}
        />
        {selection.isUnknownSlug && (
          <p className="text-xs text-red-400">{createVideoCopy.preset.unknownSlug}</p>
        )}
        <div className="grid grid-cols-3 gap-2">
          <PresetGrid
            presets={presets.presets}
            selection={selection}
            previewImageUrl={previewImageUrl}
            isLoading={presets.status === "loading"}
          />
        </div>
        {presets.status === "error" && (
          <p className="text-xs text-red-400">{createVideoCopy.preset.errorInline}</p>
        )}
        <PresetDescription selectedPreset={selection.selectedPreset} />
      </div>
    </fieldset>
  )
}
