import type { LibraryItem } from "../../api/library"
import { EmptyState } from "../../ui/EmptyState"
import { Skeleton } from "../../ui/Skeleton"
import type { LibraryState } from "../../api/library"
import { groupRailItemsByDay } from "./groupRailItemsByDay"
import { RailItem } from "./RailItem"

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
          <Skeleton className="h-14 w-14" />
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
      title="Nothing here yet."
      description="Start with a still or drop an image."
      action={
        <button
          type="button"
          onClick={onOpenStudioComposer}
          className="rounded-[10px] bg-accent px-4 text-sm font-medium text-accent-ink h-10 hover:bg-accent/90"
        >
          Make a still
        </button>
      }
    />
  )
}

export function StudioRail({ library, selectedId, onSelect, onOpenStudioComposer }: StudioRailProps) {
  if (library.status === "loading") return <RailSkeletonRows />
  if (library.status === "error") return <RailError onRetry={library.reloadLibrary} />
  if (library.items.length === 0) return <RailEmpty onOpenStudioComposer={onOpenStudioComposer} />

  return (
    <nav aria-label="Library" className="pb-6">
      {groupRailItemsByDay(library.items).map((group) => (
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
  )
}

export type { StudioRailProps }
export type LibraryItems = LibraryItem[]
