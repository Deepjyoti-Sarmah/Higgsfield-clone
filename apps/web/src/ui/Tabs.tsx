import { useRef, type KeyboardEvent } from "react"
import { nextTabIndex } from "./tabKeys"

export type TabItem<T extends string> = {
  value: T
  label: string
}

type TabsProps<T extends string> = {
  items: readonly TabItem<T>[]
  value: T
  onChange: (value: T) => void
  ariaLabel: string
}

function tabClasses(isSelected: boolean): string {
  const state = isSelected ? "border-accent text-text" : "border-transparent text-muted hover:text-text"
  return `-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${state}`
}

export function Tabs<T extends string>({ items, value, onChange, ariaLabel }: TabsProps<T>) {
  const listRef = useRef<HTMLDivElement>(null)

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const current = items.findIndex((item) => item.value === value)
    const next = nextTabIndex(items.length, current, event.key)
    if (next === current) return
    event.preventDefault()
    onChange(items[next].value)
    const buttons = listRef.current?.querySelectorAll<HTMLButtonElement>("[role='tab']")
    buttons?.[next]?.focus()
  }

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
      className="flex items-center gap-1 border-b border-border"
    >
      {items.map((item) => {
        const isSelected = item.value === value
        return (
          <button
            key={item.value}
            type="button"
            role="tab"
            aria-selected={isSelected}
            tabIndex={isSelected ? 0 : -1}
            onClick={() => onChange(item.value)}
            className={tabClasses(isSelected)}
          >
            {item.label}
          </button>
        )
      })}
    </div>
  )
}
