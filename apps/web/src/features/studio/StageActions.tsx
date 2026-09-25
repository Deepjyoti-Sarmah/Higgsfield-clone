import type { LibraryItem } from "../../api/library"

type StageActionsProps = {
  item: LibraryItem
  onAddToSequence: (item: LibraryItem) => void
  onAnimateThis: (item: LibraryItem, imageUrl: string, assetId: string) => void
  sequenceFull: boolean
}

function ActionButton({ label, onClick, disabled }: {
  label: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="h-10 rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text transition-colors hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {label}
    </button>
  )
}

export function StageActions({ item, onAddToSequence, onAnimateThis, sequenceFull }: StageActionsProps) {
  if (item.status !== "succeeded") return null
  const firstImage = item.images[0]
  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      {item.kind === "image" && firstImage && (
        <ActionButton
          label="Animate this"
          onClick={() => onAnimateThis(item, firstImage.url, firstImage.asset_id)}
        />
      )}
      {item.kind === "video" && (
        <ActionButton
          label={sequenceFull ? "Sequence is full" : "Add to sequence"}
          disabled={sequenceFull}
          onClick={() => onAddToSequence(item)}
        />
      )}
      {item.video_url && (
        <a
          href={item.video_url}
          download
          className="inline-flex h-10 items-center rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text hover:border-accent/60"
        >
          Download
        </a>
      )}
      <a
        href={`/v/${item.id}`}
        className="inline-flex h-10 items-center rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text hover:border-accent/60"
      >
        Share
      </a>
    </div>
  )
}
