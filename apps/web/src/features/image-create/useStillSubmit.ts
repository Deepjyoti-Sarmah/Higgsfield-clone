import { useCallback, useRef, useState } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import type { ImageInsufficient } from "../../api/imageJobs"
import type { ImageSettings } from "./imageCreateTypes"
import { submitStill } from "./stillSubmit"

type SubmitState = {
  isSubmitting: boolean
  insufficient: ImageInsufficient | null
  failure: "limit" | "error" | null
}

type SubmitControls = SubmitState & {
  submit(prompt: string, settings: ImageSettings): void
}

const IDLE: SubmitState = { isSubmitting: false, insufficient: null, failure: null }

function applyOutcome(
  outcome: Awaited<ReturnType<typeof submitStill>>,
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

export function useStillSubmit(
  run: RunWithGuestSession,
  onAccepted: (jobId: string) => void,
  onInsufficient: () => void,
): SubmitControls {
  const [state, setState] = useState<SubmitState>(IDLE)
  const isSubmittingRef = useRef(false)
  const refs = useRef({ accepted: onAccepted, insufficient: onInsufficient })
  refs.current = { accepted: onAccepted, insufficient: onInsufficient }

  const submit = useCallback(
    (prompt: string, settings: ImageSettings) => {
      if (isSubmittingRef.current) return
      isSubmittingRef.current = true
      setState({ ...IDLE, isSubmitting: true })
      void submitStill(run, {
        prompt,
        aspect_ratio: settings.aspectRatio,
        quality: settings.quality,
        count: settings.count,
      }).then((outcome) => {
        isSubmittingRef.current = false
        setState(applyOutcome(outcome, refs.current))
      })
    },
    [run],
  )

  return { ...state, submit }
}
