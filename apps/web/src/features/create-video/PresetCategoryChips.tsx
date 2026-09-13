import { createVideoCopy } from "./createVideoCopy"
import type { PresetCategoryFilter } from "./createVideoTypes"

type PresetCategoryChipsProps = {
  value: PresetCategoryFilter
  onChange: (value: PresetCategoryFilter) => void
}

const filterOrder: PresetCategoryFilter[] = ["all", "camera", "cinematic", "dynamic"]

function chipClasses(isActive: boolean): string {
  const base =
    "rounded-full border px-3 py-1 text-xs font-semibold transition-colors " +
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
  return isActive
    ? `${base} border-accent bg-accent text-accent-ink`
    : `${base} border-border text-muted hover:border-accent/60 hover:text-text`
}

export function PresetCategoryChips({ value, onChange }: PresetCategoryChipsProps) {
  return (
    <div
      role="group"
      aria-label={createVideoCopy.preset.categoriesLabel}
      className="flex flex-wrap gap-2"
    >
      {filterOrder.map((filter) => (
        <button
          key={filter}
          type="button"
          aria-pressed={value === filter}
          onClick={() => onChange(filter)}
          className={chipClasses(value === filter)}
        >
          {createVideoCopy.preset.categories[filter]}
        </button>
      ))}
    </div>
  )
}
