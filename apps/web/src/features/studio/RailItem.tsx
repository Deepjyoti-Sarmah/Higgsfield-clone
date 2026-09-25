import type { LibraryItem } from "../../api/library"
import { formatCreatedAt } from "./formatCreatedAt"
import { railItemMeta, railItemTitle } from "./railItemTitle"

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

export function RailItem({ item, isSelected, onSelect }: RailItemProps) {
  const thumbnail = item.thumbnail_url
  return (
    <button
      type="button"
      onClick={() => onSelect(item.id)}
      aria-current={isSelected ? "true" : undefined}
      className={`flex w-full items-center gap-3 border-l-2 px-3 py-2 text-left transition-colors ${
        isSelected ? "border-accent bg-sunken" : "border-transparent hover:bg-sunken/60"
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
        <span className="block truncate text-sm text-text">{railItemTitle(item)}</span>
        <span className="block truncate font-mono text-[13px] text-muted">
          {railItemMeta(item)} · {formatCreatedAt(item.created_at)}
        </span>
      </span>
      <StatusDot status={item.status} />
    </button>
  )
}
