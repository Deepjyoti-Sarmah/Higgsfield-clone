import type { SequenceDraftControls } from "../../api/studioContracts"
import type { RunWithGuestSession } from "../../api/guestSession"
import { ExportGuidance } from "./ExportGuidance"
import { RenderButton } from "./RenderButton"
import { approximateTotalSeconds, formatTotal } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"

type SequenceRenderStepProps = {
  sequence: SequenceDraftControls
  run: RunWithGuestSession
  isMusicUploading: boolean
  lastJobId: string | null
  onJobStarted: (jobId: string) => void
}

// Step 4 block: total length, render button, post-render guidance.
export function SequenceRenderStep({ sequence, run, isMusicUploading, lastJobId, onJobStarted }: SequenceRenderStepProps) {
  const total = formatTotal(approximateTotalSeconds(sequence.draft))
  return (
    <div className="flex flex-col items-start gap-2">
      <p className="font-mono text-[13px] text-muted">
        {sequenceCopy.total.label} {total}
      </p>
      <RenderButton
        sequence={sequence}
        run={run}
        isMusicUploading={isMusicUploading}
        onJobStarted={onJobStarted}
      />
      <ExportGuidance jobId={lastJobId} />
    </div>
  )
}
