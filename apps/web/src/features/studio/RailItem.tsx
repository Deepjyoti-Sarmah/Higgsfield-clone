import type { LibraryItem } from "../../api/library"
import { formatCreatedTime } from "./formatCreatedAt"
import { formatDuration } from "./formatDuration"
import { railItemTitle } from "./railItemTitle"
import { RailKindBadge } from "./RailKindBadge"

type RailItemProps = {
  item: LibraryItem
  isSelected: boolean
  onSelect: (jobId: string) => void
}

const DOT_CLASSES: Record<string, string> = {
  queued: "bg-faint",
  running: "bg-accent motion-safe:animate-status-pulse",
  succeeded: "bg-success",
  failed: "bg-danger",
}

function StatusDot({ status }: { status: string }) {
  return (
    <span
      aria-label={`Status: ${status}`}
      className={`h-2 w-2 shrink-0 rounded-full ${DOT_CLASSES[status] ?? "bg-faint"}`}
    />
  )
}

function railItemDetail(item: LibraryItem): string {
  const parts: string[] = []
  if (item.kind === "sequence" && item.clip_count !== null && item.clip_count !== undefined) {
    parts.push(`${item.clip_count} shots`)
  }
  const duration = formatDuration(item.duration_ms)
  if (duration !== null) parts.push(duration)
  const created = formatCreatedTime(item.created_at)
  if (created) parts.push(created)
  return parts.join(" · ")
}

export function RailItem({ item, isSelected, onSelect }: RailItemProps) {
  const thumbnail = item.thumbnail_url
  return (
    <button
      type="button"
      onClick={() => onSelect(item.id)}
      aria-current={isSelected ? "true" : undefined}
      className={`flex w-full items-center gap-3 border-l-2 px-4 py-2 text-left transition-colors ${
        isSelected
          ? "border-accent bg-accent/10 hover:bg-accent/15"
          : "border-transparent hover:border-accent/40 hover:bg-sunken/60"
      }`}
    >
      {thumbnail ? (
        <img
          src={thumbnail}
          alt=""
          className="h-14 w-14 shrink-0 rounded-lg border border-border object-cover"
        />
      ) : (
        <span className="h-14 w-14 shrink-0 rounded-lg border border-border bg-sunken" />
      )}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm leading-5 text-text">{railItemTitle(item)}</span>
        <span className="mt-0.5 flex min-w-0 items-center gap-2">
          <RailKindBadge kind={item.kind} />
          <span className="block min-w-0 truncate font-mono text-xs leading-4 text-muted">
            {railItemDetail(item)}
          </span>
        </span>
      </span>
      <StatusDot status={item.status} />
    </button>
  )
}
