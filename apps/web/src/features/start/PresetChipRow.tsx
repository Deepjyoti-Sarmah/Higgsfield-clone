import { Link } from "react-router-dom"
import { groupPresetsByCategory } from "./groupPresetsByCategory"
import type { PresetsState } from "../../api/presets"
import { Skeleton } from "../../ui/Skeleton"
import { startCopy } from "./startCopy"

function presetChipHref(slug: string): string {
  return `/studio?tab=clip&preset=${slug}`
}

type PresetChipRowProps = {
  presetsState: PresetsState
}

export function PresetChipRow({ presetsState }: PresetChipRowProps) {
  if (presetsState.status === "loading") {
    return (
      <div className="flex gap-2" aria-busy="true">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-8 w-24 rounded-full" label="Loading presets" />
        ))}
      </div>
    )
  }
  // On error the row disappears and the steps above still carry the page.
  if (presetsState.status !== "ready") return null
  return (
    <div className="flex flex-col gap-2">
      <p className="text-[13px] font-medium text-muted">{startCopy.chipsHeading}</p>
      {groupPresetsByCategory(presetsState.presets).map((group) => (
        <div key={group.category} className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-wide text-faint">
            {group.category}
          </span>
          {group.presets.map((preset) => (
            <Link
              key={preset.slug}
              to={presetChipHref(preset.slug)}
              className="rounded-full border border-border bg-surface px-3 py-1.5 text-[13px] text-text transition-colors hover:border-accent/60"
            >
              {preset.name}
            </Link>
          ))}
        </div>
      ))}
    </div>
  )
}
