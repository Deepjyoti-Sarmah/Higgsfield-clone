import { useCallback, useRef, useState } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import type { InsufficientCredits } from "./createVideoTypes"
import type { ClipInputImage } from "./clipSubmit"
import { clipJobBody, postClipJob } from "./clipSubmit"

type SubmitState = {
  isSubmitting: boolean
  insufficient: InsufficientCredits | null
  failure: "limit" | "error" | null
}

type SubmitControls = SubmitState & {
  submit(input: ClipInputImage, presetSlug: string, prompt: string): void
}

const IDLE: SubmitState = { isSubmitting: false, insufficient: null, failure: null }

function applyOutcome(
  outcome: Awaited<ReturnType<typeof postClipJob>>,
  refs: { accepted: (jobId: string) => void; insufficient: () => void },
): SubmitState {
  if (outcome.kind === "accepted") {
    refs.accepted(outcome.jobId)
    return IDLE
  }
  if (outcome.kind === "insufficient") {
    refs.insufficient()
    return { ...IDLE, insufficient: outcome.insufficient }
  }
  return { ...IDLE, failure: outcome.kind === "limit" ? "limit" : "error" }
}

export function useClipSubmit(
  run: RunWithGuestSession,
  onAccepted: (jobId: string) => void,
  onInsufficient: () => void,
): SubmitControls {
  const [state, setState] = useState<SubmitState>(IDLE)
  const isSubmittingRef = useRef(false)
  const refs = useRef({ accepted: onAccepted, insufficient: onInsufficient })
  refs.current = { accepted: onAccepted, insufficient: onInsufficient }

  const submit = useCallback(
    (input: ClipInputImage, presetSlug: string, prompt: string) => {
      if (isSubmittingRef.current) return
      isSubmittingRef.current = true
      setState({ ...IDLE, isSubmitting: true })
      void postClipJob(run, clipJobBody(input, presetSlug, prompt, crypto.randomUUID())).then(
        (outcome) => {
          isSubmittingRef.current = false
          setState(applyOutcome(outcome, refs.current))
        },
      )
    },
    [run],
  )

  return { ...state, submit }
}
