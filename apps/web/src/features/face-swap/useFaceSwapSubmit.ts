import { useCallback, useRef, useState } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import { submitFaceSwap } from "../../api/faceswapJobs"
import type { FaceSwapInsufficient } from "../../api/faceswapJobs"

type SubmitState = {
  isSubmitting: boolean
  insufficient: FaceSwapInsufficient | null
  failure: "limit" | "invalid" | "error" | null
}

type SubmitControls = SubmitState & { submit: (faceAssetId: string, targetAssetId: string) => void }

const IDLE: SubmitState = { isSubmitting: false, insufficient: null, failure: null }

export function useFaceSwapSubmit(
  run: RunWithGuestSession,
  onAccepted: (jobId: string) => void,
  onInsufficient: () => void,
): SubmitControls {
  const [state, setState] = useState<SubmitState>(IDLE)
  const isSubmittingRef = useRef(false)
  const refs = useRef({ accepted: onAccepted, insufficient: onInsufficient })
  refs.current = { accepted: onAccepted, insufficient: onInsufficient }

  const submit = useCallback(
    (faceAssetId: string, targetAssetId: string) => {
      if (isSubmittingRef.current) return
      isSubmittingRef.current = true
      setState({ ...IDLE, isSubmitting: true })
      void submitFaceSwap(run, faceAssetId, targetAssetId).then((outcome) => {
        isSubmittingRef.current = false
        if (outcome.kind === "accepted") {
          refs.current.accepted(outcome.jobId)
          setState(IDLE)
          return
        }
        if (outcome.kind === "insufficient") {
          refs.current.insufficient()
          setState({ ...IDLE, insufficient: outcome.insufficient })
          return
        }
        setState({ ...IDLE, failure: outcome.kind })
      })
    },
    [run],
  )

  return { ...state, submit }
}
