import type { PresetsState } from "../../api/presets"
import { exploreCopy } from "./exploreCopy"
import type { PresetGroup } from "./groupPresetsByCategory"
import { groupPresetsByCategory } from "./groupPresetsByCategory"
import { PresetGalleryCard } from "./PresetGalleryCard"
import { PresetGalleryStates } from "./PresetGalleryStates"

type PresetGalleryProps = {
  state: PresetsState
}

function categoryHeadingId(category: string): string {
  return `effects-${category}`
}

function PresetGroupSection({ group, label }: { group: PresetGroup; label: string }) {
  return (
    <section aria-labelledby={categoryHeadingId(group.category)} className="mt-4">
      <h2
        id={categoryHeadingId(group.category)}
        className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-text"
      >
        {label}
        <span className="rounded-full border border-border px-1.5 py-0.5 text-[10px] font-normal normal-case text-muted">
          {group.presets.length}
        </span>
      </h2>
      <ul className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5">
        {group.presets.map((preset) => (
          <li key={preset.slug}>
            <PresetGalleryCard preset={preset} />
          </li>
        ))}
      </ul>
    </section>
  )
}

export function PresetGallery({ state }: PresetGalleryProps) {
  const { title, subtitle, categoryLabel } = exploreCopy.gallery
  const groups = state.status === "ready" ? groupPresetsByCategory(state.presets) : []
  return (
    <section id="effects" aria-labelledby="effects-title" className="mx-auto w-full max-w-6xl pb-10">
      <p id="effects-title" className="font-display text-2xl uppercase leading-none text-accent sm:text-3xl">
        {title}
      </p>
      <p className="mt-1 max-w-xl text-sm text-muted">{subtitle}</p>
      {state.status !== "ready" && (
        <PresetGalleryStates status={state.status} onRetry={state.reloadPresets} />
      )}
      {state.status === "ready" && groups.length === 0 && (
        <PresetGalleryStates status="empty" onRetry={state.reloadPresets} />
      )}
      {groups.map((group) => (
        <PresetGroupSection key={group.category} group={group} label={categoryLabel(group.category)} />
      ))}
    </section>
  )
}
