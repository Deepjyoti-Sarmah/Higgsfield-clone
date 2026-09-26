import { useState } from "react"
import type { StudioTab } from "../../api/studioContracts"
import { studioCopy } from "./studioCopy"

type StudioFlowStripProps = {
  activeTab: StudioTab
  onTabChange: (tab: StudioTab) => void
}

function stepClasses(isActive: boolean): string {
  const border = isActive ? "border-accent" : "border-border hover:border-accent/60"
  return `flex items-center gap-2 rounded-[10px] border px-3 py-2 text-left ${border}`
}

export function StudioFlowStrip({ activeTab, onTabChange }: StudioFlowStripProps) {
  const [isDismissed, setIsDismissed] = useState(false)
  if (isDismissed) return null
  const { heading, steps, dismiss } = studioCopy.flowStrip
  return (
    <div className="mx-4 mt-3 rounded-[10px] border border-border bg-surface px-4 py-3 sm:mx-6">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-text">{heading}</p>
        <button type="button" onClick={() => setIsDismissed(true)} className="text-xs text-muted hover:text-text">{dismiss}</button>
      </div>
      <ol className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        {steps.map((step, index) => (
          <li key={step.tab} className="flex items-center gap-2">
            <button type="button" onClick={() => onTabChange(step.tab)} aria-current={step.tab === activeTab ? "step" : undefined} className={stepClasses(step.tab === activeTab)}>
              <span className="font-mono text-[11px] text-muted">{index + 1}</span>
              <span><span className="block text-xs font-semibold text-text">{step.label}</span>
              <span className="block text-[11px] text-muted">{step.caption}</span></span>
            </button>
            {index < steps.length - 1 && <span aria-hidden="true" className="hidden text-muted sm:block">→</span>}
          </li>
        ))}
      </ol>
    </div>
  )
}
