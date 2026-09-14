import type { LibraryItem as LibraryItemData } from "../../api/library"
import { GenerationBadge } from "../../ui/GenerationBadge"
import { libraryCopy } from "./libraryCopy"

type LibraryItemProps = {
  item: LibraryItemData
  isSelected: boolean
  onSelect: () => void
}

function PlayGlyph() {
  return (
    <span
      aria-hidden="true"
      className="absolute bottom-1.5 right-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 backdrop-blur-sm"
    >
      <svg viewBox="0 0 12 12" className="ml-0.5 h-3 w-3 fill-white">
        <path d="M2 1.5v9l8-4.5-8-4.5z" />
      </svg>
    </span>
  )
}

function ItemThumbnail({ item }: { item: LibraryItemData }) {
  if (item.thumbnail_url === null) {
    return <span aria-hidden="true" className="block h-full w-full bg-border" />
  }
  return (
    <>
      <img src={item.thumbnail_url} alt="" loading="lazy" className="h-full w-full object-cover" />
      {item.kind === "video" && <PlayGlyph />}
    </>
  )
}

function ViewingChip() {
  return (
    <span className="inline-flex w-fit items-center rounded-full bg-accent px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-accent-ink">
      {libraryCopy.item.viewing}
    </span>
  )
}

export function LibraryItem({ item, isSelected, onSelect }: LibraryItemProps) {
  const rowClasses = isSelected
    ? "border-l-4 border-l-accent border-accent/30 bg-accent/10"
    : "border-l-4 border-l-transparent border-border bg-surface hover:border-accent/40"
  const label = libraryCopy.item.label(item)
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={isSelected ? "true" : undefined}
      aria-label={libraryCopy.item.openLabel(label)}
      className={`flex w-full items-center gap-4 rounded-2xl border p-3 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${rowClasses}`}
    >
      <span className="relative aspect-square w-36 shrink-0 overflow-hidden rounded-xl border border-border">
        <ItemThumbnail item={item} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        {isSelected && <ViewingChip />}
        <span className="truncate text-sm font-semibold text-text">{label}</span>
        <span className="text-xs text-muted">{libraryCopy.time.label(item.created_at)}</span>
        <span className="flex items-center gap-2 text-xs text-muted">
          {libraryCopy.item.status[item.status]}
          <GenerationBadge generatedBy={item.generated_by} kind={item.kind} />
        </span>
      </span>
    </button>
  )
}
