import type { PresetsState } from "../../api/presets"
import { exploreCopy } from "./exploreCopy"
import { groupPresetsByCategory } from "./groupPresetsByCategory"
import { PresetGalleryCard } from "./PresetGalleryCard"
import { PresetGalleryStates } from "./PresetGalleryStates"

type PresetGalleryProps = {
  state: PresetsState
}

function categoryHeadingId(category: string): string {
  return `effects-${category}`
}

export function PresetGallery({ state }: PresetGalleryProps) {
  const { title, subtitle, categoryLabel } = exploreCopy.gallery
  const isEmpty = state.status === "ready" && state.presets.length === 0
  const groups = state.status === "ready" ? groupPresetsByCategory(state.presets) : []

  return (
    <section id="effects" aria-labelledby="effects-title" className="mx-auto max-w-6xl py-12">
      <p id="effects-title" className="font-display text-4xl uppercase leading-none text-accent sm:text-5xl">
        {title}
      </p>
      <p className="mt-3 max-w-xl text-muted">{subtitle}</p>
      {state.status === "loading" && (
        <PresetGalleryStates status="loading" onRetry={state.reloadPresets} />
      )}
      {state.status === "error" && (
        <PresetGalleryStates status="error" onRetry={state.reloadPresets} />
      )}
      {isEmpty && <PresetGalleryStates status="empty" onRetry={state.reloadPresets} />}
      {groups.map((group) => (
        <section
          key={group.category}
          aria-labelledby={categoryHeadingId(group.category)}
          className="mt-10"
        >
          <h2 id={categoryHeadingId(group.category)} className="flex items-center gap-2 text-xl uppercase text-text">
            {categoryLabel(group.category)}
            <span className="rounded-full border border-border px-2 py-0.5 text-xs font-body normal-case text-muted">{group.presets.length}</span>
          </h2>
          <ul className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {group.presets.map((preset) => (
              <li key={preset.slug} className="h-full">
                <PresetGalleryCard preset={preset} />
              </li>
            ))}
          </ul>
        </section>
      ))}
    </section>
  )
}
