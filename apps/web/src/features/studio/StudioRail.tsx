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
    <div className="space-y-1 p-3" aria-busy="true">
      {[0, 1, 2, 3, 4].map((row) => (
        <div key={row} className="flex items-center gap-3 px-1">
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

function ActionButton({ label, onClick, variant }: {
  label: string
  onClick: () => void
  variant: "primary" | "secondary"
}) {
  const styles = variant === "primary"
    ? "bg-accent text-accent-ink hover:bg-accent/90"
    : "border border-border bg-surface text-text hover:border-accent/60"
  return (
    <button type="button" onClick={onClick} className={`h-10 rounded-[10px] px-4 text-sm font-medium pointer-coarse:h-11 ${styles}`}>
      {label}
    </button>
  )
}

function RailError({ onRetry }: { onRetry: () => void }) {
  return (
    <EmptyState
      title="The rail could not load."
      description="Your work is not showing right now. Check the connection and try again."
      action={<ActionButton label="Retry" onClick={onRetry} variant="secondary" />}
    />
  )
}

function RailEmpty({ onOpenStudioComposer }: { onOpenStudioComposer: () => void }) {
  return (
    <EmptyState
      title={studioCopy.rail.emptyTitle}
      description={studioCopy.rail.emptyBody}
      action={
        <ActionButton label={studioCopy.rail.emptyAction} onClick={onOpenStudioComposer} variant="primary" />
      }
    />
  )
}

function RailFilteredEmpty({ onClear }: { onClear: () => void }) {
  return (
    <EmptyState
      title={studioCopy.rail.filteredEmptyTitle}
      description={studioCopy.rail.filteredEmptyBody}
      action={<ActionButton label={studioCopy.rail.filteredEmptyAction} onClick={onClear} variant="secondary" />}
    />
  )
}

function RailHeader({ count, isLoading, onNew }: {
  count: number
  isLoading: boolean
  onNew: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-border bg-surface px-4 py-2.5">
      <div className="min-w-0">
        <h2 className="truncate font-body text-sm font-semibold text-text">{studioCopy.rail.heading}</h2>
        {isLoading ? (
          <Skeleton className="mt-1 h-3 w-20" />
        ) : (
          <p className="font-mono text-xs tabular-nums text-muted">{studioCopy.rail.count(count)}</p>
        )}
      </div>
      <button
        type="button"
        onClick={onNew}
        className="h-10 shrink-0 rounded-[10px] bg-accent px-4 text-sm font-medium text-accent-ink hover:bg-accent/90 pointer-coarse:h-11"
      >
        {studioCopy.rail.newAction}
      </button>
    </div>
  )
}

function RailRows({ items, selectedId, onSelect }: {
  items: LibraryItem[]
  selectedId: string | null
  onSelect: (jobId: string) => void
}) {
  return (
    <nav aria-label="Library" className="pb-6">
      {groupRailItemsByDay(items).map((group) => (
        <section key={group.heading}>
          <h3 className="px-4 pb-1 pt-4 font-mono text-[11px] uppercase tracking-wide text-muted">
            {group.heading}
          </h3>
          {group.items.map((item) => (
            <RailItem key={item.id} item={item} isSelected={item.id === selectedId} onSelect={onSelect} />
          ))}
        </section>
      ))}
    </nav>
  )
}

function RailBody({ library, visible, selectedId, onSelect, onOpenStudioComposer, onClear }: {
  library: LibraryState
  visible: LibraryItem[]
  selectedId: string | null
  onSelect: (jobId: string) => void
  onOpenStudioComposer: () => void
  onClear: () => void
}) {
  if (library.status === "loading") return <RailSkeletonRows />
  if (library.status === "error") return <RailError onRetry={library.reloadLibrary} />
  if (library.items.length === 0) return <RailEmpty onOpenStudioComposer={onOpenStudioComposer} />
  if (visible.length === 0) return <RailFilteredEmpty onClear={onClear} />
  return <RailRows items={visible} selectedId={selectedId} onSelect={onSelect} />
}

export function StudioRail({ library, selectedId, onSelect, onOpenStudioComposer }: StudioRailProps) {
  const [filter, setFilter] = useState<RailKindFilterValue>("all")
  const counts = countRailKinds(library.items)
  const visible = library.items.filter((item) => matchesRailKindFilter(item, filter))
  const hasItems = library.status === "ready" && library.items.length > 0
  return (
    <div className="flex min-h-0 flex-col">
      <RailHeader count={library.items.length} isLoading={library.status === "loading"} onNew={onOpenStudioComposer} />
      {hasItems && (
        <div className="sticky top-0 z-10 border-b border-border bg-surface px-4 py-2.5">
          <RailKindFilter active={filter} counts={counts} onChange={setFilter} />
        </div>
      )}
      <RailBody
        library={library}
        visible={visible}
        selectedId={selectedId}
        onSelect={onSelect}
        onOpenStudioComposer={onOpenStudioComposer}
        onClear={() => setFilter("all")}
      />
    </div>
  )
}

export type { StudioRailProps }
export type LibraryItems = LibraryItem[]
