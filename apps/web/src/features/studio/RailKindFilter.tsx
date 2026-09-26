import { studioCopy } from "./studioCopy"
import type { RailKindCounts, RailKindFilter } from "./railKindFilter"

type RailKindFilterProps = {
  active: RailKindFilter
  counts: RailKindCounts
  onChange: (next: RailKindFilter) => void
}

const FILTER_ORDER: RailKindFilter[] = ["all", "image", "video", "sequence", "faceswap"]

export function RailKindFilter({ active, counts, onChange }: RailKindFilterProps) {
  return (
    <div role="group" aria-label={studioCopy.rail.filterLabel} className="flex flex-wrap gap-1.5">
      {FILTER_ORDER.map((value) => {
        const isActive = value === active
        return (
          <button
            key={value}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(value)}
            className={`h-8 rounded-full border px-3 font-mono text-xs tabular-nums transition-colors ${
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
