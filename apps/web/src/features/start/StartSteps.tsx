import type { ReactNode } from "react"
import { startCopy } from "./startCopy"
import type { StepTool } from "./startCopy"
import { ToolStepMedia } from "./StartStepMedia"

const STEP_TOOLS: readonly StepTool[] = ["still", "clip", "sequence", "faceSwap"]

function StepRow({ label, caption, children }: {
  label: string
  caption: string
  children: ReactNode
}) {
  return (
    <div className="grid grid-cols-1 gap-3 border-b border-border pb-6 last:border-b-0 sm:grid-cols-[7rem_1fr] sm:items-center">
      <div>
        <p className="text-sm font-semibold text-text">{label}</p>
        <p className="text-[0.8125rem] leading-snug text-muted">{caption}</p>
      </div>
      {children}
    </div>
  )
}

export function StartSteps() {
  return (
    <div className="flex flex-col gap-6">
      {STEP_TOOLS.map((tool) => (
        <StepRow
          key={tool}
          label={startCopy.steps[tool].label}
          caption={startCopy.steps[tool].caption}
        >
          <ToolStepMedia tool={tool} />
        </StepRow>
      ))}
    </div>
  )
}
