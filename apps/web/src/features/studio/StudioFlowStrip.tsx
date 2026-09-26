import { useRef, type KeyboardEvent, type RefObject } from "react"
import type { StudioTab } from "../../api/studioContracts"
import { nextTabIndex } from "../../ui/tabKeys"
import { studioCopy } from "./studioCopy"

type StudioFlowStripProps = {
  activeTab: StudioTab
  onTabChange: (tab: StudioTab) => void
}

const STEPS = studioCopy.toolOrder

function stepClasses(isActive: boolean): string {
  const state = isActive
    ? "border-accent bg-accent/10 text-text"
    : "border-border bg-surface text-muted hover:border-accent/60 hover:text-text"
  return `flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium transition-colors pointer-coarse:min-h-11 ${state}`
}

function FlowStep({ tab, isActive, onSelect }: {
  tab: StudioTab
  isActive: boolean
  onSelect: (tab: StudioTab) => void
}) {
  const tool = studioCopy.tools[tab]
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      tabIndex={isActive ? 0 : -1}
      onClick={() => onSelect(tab)}
      className={stepClasses(isActive)}
    >
      <span className={`font-mono text-[11px] ${isActive ? "text-accent" : "text-muted"}`}>{tool.step}</span>
      <span>{tool.label}</span>
    </button>
  )
}

function FlowSteps({ activeTab, onSelect, listRef, onKeyDown }: {
  activeTab: StudioTab
  onSelect: (tab: StudioTab) => void
  listRef: RefObject<HTMLDivElement | null>
  onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => void
}) {
  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={studioCopy.flowStrip.heading}
      onKeyDown={onKeyDown}
      className="flex min-w-0 flex-1 items-center gap-1.5 overflow-x-auto"
    >
      {STEPS.map((tab, index) => (
        <span key={tab} role="presentation" className="flex shrink-0 items-center gap-1.5">
          <FlowStep tab={tab} isActive={tab === activeTab} onSelect={onSelect} />
          {index < STEPS.length - 1 && (
            <span aria-hidden="true" className="hidden text-faint sm:inline">→</span>
          )}
        </span>
      ))}
    </div>
  )
}

export function StudioFlowStrip({ activeTab, onTabChange }: StudioFlowStripProps) {
  const listRef = useRef<HTMLDivElement>(null)

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const current = STEPS.indexOf(activeTab)
    const next = nextTabIndex(STEPS.length, current, event.key)
    if (next === current) return
    event.preventDefault()
    onTabChange(STEPS[next])
    listRef.current?.querySelectorAll<HTMLButtonElement>("[role='tab']")[next]?.focus()
  }

  return (
    <div className="flex items-center gap-2 border-b border-border px-3 py-2 sm:px-4">
      <p className="shrink-0 font-mono text-[11px] uppercase tracking-wide text-muted">
        {studioCopy.flowStrip.heading}
      </p>
      <FlowSteps activeTab={activeTab} onSelect={onTabChange} listRef={listRef} onKeyDown={handleKeyDown} />
    </div>
  )
}
