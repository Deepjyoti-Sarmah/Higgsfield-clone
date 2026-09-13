import type { LibraryItem as LibraryItemData } from "../../api/library"
import { LibraryItem } from "./LibraryItem"

type LibraryListProps = {
  items: LibraryItemData[]
  selectedJobId: string | null
  onSelect: (id: string) => void
}

export function LibraryList({ items, selectedJobId, onSelect }: LibraryListProps) {
  return (
    <ul className="flex flex-col gap-3">
      {items.map((item) => (
        <li key={item.id}>
          <LibraryItem
            item={item}
            isSelected={item.id === selectedJobId}
            onSelect={() => onSelect(item.id)}
          />
        </li>
      ))}
    </ul>
  )
}
