import type { LibraryItem as LibraryItemData } from "../../api/library"
import { GenerationBadge } from "../../ui/GenerationBadge"
import { libraryCopy } from "./libraryCopy"

type LibraryItemProps = {
  item: LibraryItemData
  isSelected: boolean
  onSelect: () => void
}

function ItemThumbnail({ item }: { item: LibraryItemData }) {
  if (item.thumbnail_url === null) {
    return <span aria-hidden="true" className="block h-full w-full bg-border" />
  }
  return (
    <img src={item.thumbnail_url} alt="" loading="lazy" className="h-full w-full object-cover" />
  )
}

export function LibraryItem({ item, isSelected, onSelect }: LibraryItemProps) {
  const rowClasses = isSelected
    ? "border-accent/60"
    : "border-border hover:border-accent/60"
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={isSelected ? "true" : undefined}
      aria-label={libraryCopy.item.openLabel(item.preset_name)}
      className={`flex w-full items-center gap-4 rounded-2xl border bg-surface p-3 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${rowClasses}`}
    >
      <span className="relative aspect-[4/3] w-28 shrink-0 overflow-hidden rounded-xl border border-border">
        <ItemThumbnail item={item} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="truncate text-sm font-semibold text-text">{item.preset_name}</span>
        <span className="text-xs text-muted">{libraryCopy.time.label(item.created_at)}</span>
        <span className="flex items-center gap-2 text-xs text-muted">
          {libraryCopy.item.status[item.status]}
          <GenerationBadge generatedBy={item.generated_by} />
        </span>
      </span>
    </button>
  )
}
