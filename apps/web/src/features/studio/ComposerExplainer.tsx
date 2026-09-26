import type { StudioTab } from "../../api/studioContracts"
import { studioCopy } from "./studioCopy"

type ComposerExplainerProps = { tab: StudioTab }

function GuidanceLine({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-xs text-muted">
      <span className="font-medium text-text">{label}: </span>
      {value}
    </p>
  )
}

export function ComposerExplainer({ tab }: ComposerExplainerProps) {
  const tool = studioCopy.tools[tab]
  return (
    <div className="px-4 pb-2.5 pt-2.5 sm:px-6" aria-live="polite">
      <p className="text-sm text-text">
        <span className="font-medium">Step {tool.step}: {tool.label}. </span>
        {tool.purpose}
      </p>
      <div className="mt-1 flex flex-col gap-0.5 sm:flex-row sm:gap-4">
        <GuidanceLine label={studioCopy.guidance.outputLabel} value={tool.output} />
        <GuidanceLine label={studioCopy.guidance.nextLabel} value={tool.next} />
      </div>
    </div>
  )
}
