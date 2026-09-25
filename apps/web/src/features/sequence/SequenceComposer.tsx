import { useOutletContext } from "react-router-dom"
import { useState } from "react"
import type { SequenceComposerProps } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { useGuestSessionRunner } from "../../api/guestSession"
import { ClipPicker } from "./ClipPicker"
import { MusicDropZone } from "./MusicDropZone"
import { RenderButton } from "./RenderButton"
import { SequenceStrip } from "./SequenceStrip"
import { approximateTotalSeconds, formatTotal } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"

export function SequenceComposer({ onJobStarted, sequence, libraryItems }: SequenceComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const [isMusicUploading, setIsMusicUploading] = useState(false)
  const total = formatTotal(approximateTotalSeconds(sequence.draft))

  return (
    <div className="flex flex-col gap-4 p-4 sm:p-6">
      <SequenceStrip sequence={sequence} />
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-1 flex-col gap-4">
          <ClipPicker libraryItems={libraryItems} sequence={sequence} />
          <MusicDropZone
            session={session}
            sequence={sequence}
            onUploadingChange={setIsMusicUploading}
          />
        </div>
        <div className="flex flex-col items-end gap-2">
          <p className="font-mono text-[13px] text-muted">
            {sequenceCopy.total.label} {total}
          </p>
          <RenderButton
            sequence={sequence}
            run={run}
            isMusicUploading={isMusicUploading}
            onJobStarted={onJobStarted}
          />
        </div>
      </div>
    </div>
  )
}
