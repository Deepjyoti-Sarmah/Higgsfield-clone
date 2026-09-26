import { studioCopy } from "./studioCopy"
import type { RailKindCounts, RailKindFilter } from "./railKindFilter"

type RailKindFilterProps = {
  active: RailKindFilter
  counts: RailKindCounts
  onChange: (next: RailKindFilter) => void
}

const FILTER_ORDER: RailKindFilter[] = ["all", "image", "video", "sequence", "faceswap"]

function filterLabel(value: RailKindFilter, count: number): string {
  const noun = count === 1 ? "item" : "items"
  return `${studioCopy.rail.filters[value]}, ${count} ${noun}`
}

export function RailKindFilter({ active, counts, onChange }: RailKindFilterProps) {
  return (
    <div role="group" aria-label={studioCopy.rail.filterLabel} className="flex flex-wrap gap-1">
      {FILTER_ORDER.map((value) => {
        const isActive = value === active
        return (
          <button
            key={value}
            type="button"
            aria-pressed={isActive}
            aria-label={filterLabel(value, counts[value])}
            onClick={() => onChange(value)}
            className={`h-7 rounded-full border px-2.5 font-mono text-xs tabular-nums transition-colors pointer-coarse:h-11 ${
              isActive
                ? "border-transparent bg-accent text-accent-ink"
                : "border-border bg-surface text-muted hover:border-accent/60 hover:text-text"
            }`}
          >
            {studioCopy.rail.filters[value]} · {counts[value]}
          </button>
        )
      })}
    </div>
  )
}
