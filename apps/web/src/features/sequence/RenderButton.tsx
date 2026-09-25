import { useCallback, useRef, useState } from "react"
import type { SequenceDraftControls } from "../../api/studioContracts"
import type { SequenceSubmitOutcome } from "../../api/sequenceJobs"
import { createSequenceJob, sequenceRequestBody } from "../../api/sequenceJobs"
import type { RunWithGuestSession } from "../../api/guestSession"
import { Button } from "../../ui/Button"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import { renderBlocker, renderReason, toPayloadClips } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"

type RenderButtonProps = {
  sequence: SequenceDraftControls
  run: RunWithGuestSession
  isMusicUploading: boolean
  onJobStarted: (jobId: string) => void
}

const FAILURE_MESSAGES: Record<string, string> = {
  insufficient: sequenceCopy.render.button,
  "clip-invalid": sequenceCopy.render.clipInvalid,
  limit: sequenceCopy.render.limit,
  session: sequenceCopy.render.failed,
  network: sequenceCopy.render.failed,
}

function applyOutcome(
  outcome: SequenceSubmitOutcome,
  actions: { onJobStarted: (jobId: string) => void; clearDraft: () => void; openCredits: () => void },
): string | null {
  if (outcome.kind === "accepted") {
    actions.onJobStarted(outcome.jobId)
    actions.clearDraft()
    return null
  }
  if (outcome.kind === "insufficient") {
    actions.openCredits()
    return null
  }
  return FAILURE_MESSAGES[outcome.kind] ?? sequenceCopy.render.failed
}

export function RenderButton({ sequence, run, isMusicUploading, onJobStarted }: RenderButtonProps) {
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { openCredits } = useCreditsPopover()
  const isSubmittingRef = useRef(false)
  const blocker = renderBlocker(sequence.draft, isMusicUploading)
  const reason = renderReason(blocker)
  const handleSubmit = useCallback(() => {
    if (isSubmittingRef.current || blocker !== null) return
    isSubmittingRef.current = true
    setIsSubmitting(true)
    setSubmitError(null)
    const body = sequenceRequestBody(
      toPayloadClips(sequence.draft),
      sequence.draft.audio?.assetId ?? null,
      crypto.randomUUID(),
    )
    void createSequenceJob(run, body).then((outcome) => {
      isSubmittingRef.current = false
      setIsSubmitting(false)
      setSubmitError(applyOutcome(outcome, {
        onJobStarted,
        clearDraft: sequence.clearDraft,
        openCredits,
      }))
    })
  }, [blocker, onJobStarted, openCredits, run, sequence])
  return (
    <div className="flex flex-col items-end gap-1">
      <Button onClick={handleSubmit} isLoading={isSubmitting} disabled={blocker !== null}>
        {sequenceCopy.render.button}
      </Button>
      {blocker !== null && reason && <p className="text-[13px] text-faint">{reason}</p>}
      {submitError && <p role="alert" className="text-[13px] text-danger">{submitError}</p>}
    </div>
  )
}
