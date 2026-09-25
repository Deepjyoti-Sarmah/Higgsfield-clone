import type { ReactNode } from "react"
import type { Preset } from "../../api/presets"
import { startCopy } from "./startCopy"
import { ClipStepMedia, SequenceStepMedia, StillStepMedia } from "./StartStepMedia"

type StartStepsProps = {
  clipPreset: Preset | null
}

function StepRow({ label, caption, children }: {
  label: string
  caption: string
  children: ReactNode
}) {
  return (
    <div className="grid grid-cols-1 gap-3 border-b border-border pb-6 last:border-b-0 sm:grid-cols-[7rem_1fr] sm:items-center">
      <div>
        <p className="text-sm font-semibold text-text">{label}</p>
        <p className="font-mono text-[11px] text-muted">{caption}</p>
      </div>
      {children}
    </div>
  )
}

export function StartSteps({ clipPreset }: StartStepsProps) {
  return (
    <div className="flex flex-col gap-6">
      <StepRow label={startCopy.steps.still.label} caption={startCopy.steps.still.caption}>
        <StillStepMedia />
      </StepRow>
      <StepRow label={startCopy.steps.clip.label} caption={startCopy.steps.clip.caption}>
        <ClipStepMedia preset={clipPreset} />
      </StepRow>
      <StepRow label={startCopy.steps.sequence.label} caption={startCopy.steps.sequence.caption}>
        <SequenceStepMedia />
      </StepRow>
    </div>
  )
}
