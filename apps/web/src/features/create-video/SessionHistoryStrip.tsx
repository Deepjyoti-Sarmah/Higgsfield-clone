import { useState } from "react"
import { createVideoCopy } from "./createVideoCopy"
import type { HistoryEntry, JobStatus } from "./createVideoTypes"

type SessionHistoryStripProps = {
  entries: HistoryEntry[]
  activeJobId: string | null
  onOpen: (jobId: string) => void
}

const statusLabels: Record<JobStatus, string> = {
  queued: createVideoCopy.status.queued,
  running: createVideoCopy.status.generating,
  succeeded: createVideoCopy.status.done,
  failed: createVideoCopy.status.failed,
}

const dotClasses: Record<JobStatus, string> = {
  queued: "bg-muted",
  running: "bg-accent",
  succeeded: "",
  failed: "bg-red-400",
}

function HistoryTile({
  entry,
  isActive,
  onOpen,
}: {
  entry: HistoryEntry
  isActive: boolean
  onOpen: (jobId: string) => void
}) {
  const [hasImageError, setHasImageError] = useState(false)
  const border = isActive ? "border-accent" : "border-transparent"
  const showImage = entry.thumbnailUrl !== null && !hasImageError
  return (
    <button
      type="button"
      aria-current={isActive ? "true" : undefined}
      aria-label={createVideoCopy.history.tile(entry.presetName, statusLabels[entry.status])}
      onClick={() => onOpen(entry.jobId)}
      className="flex w-24 shrink-0 flex-col gap-1 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <span className={`relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border-2 bg-bg ${border}`}>
        {showImage && entry.thumbnailUrl !== null ? (
          <img src={entry.thumbnailUrl} alt="" onError={() => setHasImageError(true)} className="h-full w-full object-cover" />
        ) : (
          <span className="text-lg font-semibold text-muted">{entry.presetName.charAt(0)}</span>
        )}
        {entry.status !== "succeeded" && (
          <span aria-hidden="true" className={`absolute right-1 top-1 h-2 w-2 rounded-full ${dotClasses[entry.status]}`} />
        )}
      </span>
      <span className="truncate text-xs text-muted">{entry.presetName}</span>
    </button>
  )
}

export function SessionHistoryStrip({
  entries,
  activeJobId,
  onOpen,
}: SessionHistoryStripProps) {
  if (entries.length === 0) return null
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
        {createVideoCopy.history.label}
      </h2>
      <ul className="flex gap-2 overflow-x-auto pb-1">
        {entries.map((entry) => (
          <li key={entry.jobId}>
            <HistoryTile entry={entry} isActive={entry.jobId === activeJobId} onOpen={onOpen} />
          </li>
        ))}
      </ul>
    </section>
  )
}
