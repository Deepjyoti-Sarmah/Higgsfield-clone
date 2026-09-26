import { useOutletContext } from "react-router-dom"
import { useCallback, useState } from "react"
import type { SequenceComposerProps } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { useGuestSessionRunner } from "../../api/guestSession"
import { ClipPicker } from "./ClipPicker"
import { MusicDropZone } from "./MusicDropZone"
import { SequenceRenderStep } from "./SequenceRenderStep"
import { SequenceStep } from "./SequenceStep"
import { SequenceStrip } from "./SequenceStrip"
import { sequenceCopy } from "./sequenceCopy"

export function SequenceComposer({ onJobStarted, onTabChange, sequence, libraryItems }: SequenceComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const [isMusicUploading, setIsMusicUploading] = useState(false)
  const [lastJobId, setLastJobId] = useState<string | null>(null)
  const goToClipTab = onTabChange ? () => onTabChange("clip") : undefined
  const handleJobStarted = useCallback((jobId: string) => {
    setLastJobId(jobId)
    onJobStarted(jobId)
  }, [onJobStarted])
  const steps = sequenceCopy.steps

  return (
    <div className="flex flex-col gap-3 p-4 sm:p-6">
      <SequenceStep number={steps.add.number} heading={steps.add.heading} body={steps.add.body}>
        <ClipPicker libraryItems={libraryItems} sequence={sequence} onGoToClipTab={goToClipTab} />
      </SequenceStep>
      <SequenceStep number={steps.arrange.number} heading={steps.arrange.heading} body={steps.arrange.body}>
        <SequenceStrip sequence={sequence} />
      </SequenceStep>
      <SequenceStep number={steps.music.number} heading={steps.music.heading} body={steps.music.body}>
        <MusicDropZone
          session={session}
          sequence={sequence}
          onUploadingChange={setIsMusicUploading}
        />
      </SequenceStep>
      <SequenceStep number={steps.render.number} heading={steps.render.heading} body={steps.render.body}>
        <SequenceRenderStep
          sequence={sequence}
          run={run}
          isMusicUploading={isMusicUploading}
          lastJobId={lastJobId}
          onJobStarted={handleJobStarted}
        />
      </SequenceStep>
    </div>
  )
}
