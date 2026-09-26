import { useCallback, useState } from "react"
import { useOutletContext } from "react-router-dom"
import type { SequenceComposerProps } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { useGuestSessionRunner } from "../../api/guestSession"
import { AddShotPanel } from "./AddShotPanel"
import { MusicDropZone } from "./MusicDropZone"
import { SequenceRenderStep } from "./SequenceRenderStep"
import { SequenceStrip } from "./SequenceStrip"
import { sequenceCopy } from "./sequenceCopy"
import { approximateTotalSeconds, formatTotal } from "./sequenceDraftView"

function ComposerHeader({ total }: { total: string }) {
  return (
    <header className="flex flex-wrap items-baseline justify-between gap-2">
      <div>
        <h2 className="text-sm font-semibold text-text">{sequenceCopy.header.title}</h2>
        <p className="text-[13px] text-muted">{sequenceCopy.header.body}</p>
      </div>
      <p className="font-mono text-[13px] text-muted">
        {sequenceCopy.total.label} {total}
      </p>
    </header>
  )
}

export function SequenceComposer({ onJobStarted, onTabChange, sequence, libraryItems, onFaceSwapClip }: SequenceComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const [isMusicUploading, setIsMusicUploading] = useState(false)
  const [lastJobId, setLastJobId] = useState<string | null>(null)
  const goToClip = onTabChange ? () => onTabChange("clip") : undefined
  const goToFaceSwap = onTabChange ? () => onTabChange("faceswap") : undefined
  const handleJobStarted = useCallback((jobId: string) => {
    setLastJobId(jobId)
    onJobStarted(jobId)
  }, [onJobStarted])
  const total = formatTotal(approximateTotalSeconds(sequence.draft))
  return (
    <div className="flex flex-col gap-4 p-4 sm:p-6">
      <ComposerHeader total={total} />
      <SequenceStrip sequence={sequence} libraryItems={libraryItems} onFaceSwapClip={onFaceSwapClip} />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_20rem]">
        <AddShotPanel
          sequence={sequence}
          libraryItems={libraryItems}
          onGoToClip={goToClip}
          onGoToFaceSwap={goToFaceSwap}
        />
        <div className="flex flex-col gap-4">
          <MusicDropZone session={session} sequence={sequence} onUploadingChange={setIsMusicUploading} />
          <SequenceRenderStep
            sequence={sequence}
            run={run}
            isMusicUploading={isMusicUploading}
            lastJobId={lastJobId}
            onJobStarted={handleJobStarted}
          />
        </div>
      </div>
    </div>
  )
}
