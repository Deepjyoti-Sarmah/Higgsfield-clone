import { useState } from "react"
import type { LibraryItem } from "../../api/library"
import { EmptyState } from "../../ui/EmptyState"
import { Skeleton } from "../../ui/Skeleton"
import type { LibraryState } from "../../api/library"
import { groupRailItemsByDay } from "./groupRailItemsByDay"
import { RailItem } from "./RailItem"
import { RailKindFilter } from "./RailKindFilter"
import { countRailKinds, matchesRailKindFilter } from "./railKindFilter"
import type { RailKindFilter as RailKindFilterValue } from "./railKindFilter"
import { studioCopy } from "./studioCopy"

type StudioRailProps = {
  library: LibraryState
  selectedId: string | null
  onSelect: (jobId: string) => void
  onOpenStudioComposer: () => void
}

function RailSkeletonRows() {
  return (
    <div className="space-y-2 p-3" aria-busy="true">
      {[0, 1, 2, 3, 4].map((row) => (
        <div key={row} className="flex items-center gap-3">
          <Skeleton className="h-16 w-16" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}

function RailError({ onRetry }: { onRetry: () => void }) {
  return (
    <EmptyState
      title="The rail could not load."
      description="Your generations are not showing right now. Check the connection and try again."
      action={
        <button
          type="button"
          onClick={onRetry}
          className="rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text h-10 hover:border-accent/60"
        >
          Retry
        </button>
      }
    />
  )
}

function RailEmpty({ onOpenStudioComposer }: { onOpenStudioComposer: () => void }) {
  return (
    <EmptyState
      title={studioCopy.rail.emptyTitle}
      description={studioCopy.rail.emptyBody}
      action={
        <button
          type="button"
          onClick={onOpenStudioComposer}
          className="rounded-[10px] bg-accent px-4 text-sm font-medium text-accent-ink h-10 hover:bg-accent/90"
        >
          {studioCopy.rail.emptyAction}
        </button>
      }
    />
  )
}

function RailFilteredEmpty({ onClear }: { onClear: () => void }) {
  return (
    <EmptyState
      title={studioCopy.rail.filteredEmptyTitle}
      description={studioCopy.rail.emptyBody}
      action={
        <button
          type="button"
          onClick={onClear}
          className="rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text h-10 hover:border-accent/60"
        >
          {studioCopy.rail.filteredEmptyAction}
        </button>
      }
    />
  )
}

export function StudioRail({ library, selectedId, onSelect, onOpenStudioComposer }: StudioRailProps) {
  const [filter, setFilter] = useState<RailKindFilterValue>("all")
  if (library.status === "loading") return <RailSkeletonRows />
  if (library.status === "error") return <RailError onRetry={library.reloadLibrary} />
  if (library.items.length === 0) return <RailEmpty onOpenStudioComposer={onOpenStudioComposer} />

  const counts = countRailKinds(library.items)
  const visible = library.items.filter((item) => matchesRailKindFilter(item, filter))

  return (
    <div>
      <div className="sticky top-0 z-10 border-b border-border bg-surface p-2">
        <RailKindFilter active={filter} counts={counts} onChange={setFilter} />
      </div>
      {visible.length === 0 ? (
        <RailFilteredEmpty onClear={() => setFilter("all")} />
      ) : (
        <nav aria-label="Library" className="pb-6">
          {groupRailItemsByDay(visible).map((group) => (
            <section key={group.heading}>
              <h3 className="px-3 pb-1 pt-4 font-mono text-[11px] uppercase tracking-wide text-muted">
                {group.heading}
              </h3>
              {group.items.map((item) => (
                <RailItem
                  key={item.id}
                  item={item}
                  isSelected={item.id === selectedId}
                  onSelect={onSelect}
                />
              ))}
            </section>
          ))}
        </nav>
      )}
    </div>
  )
}

export type { StudioRailProps }
export type LibraryItems = LibraryItem[]
