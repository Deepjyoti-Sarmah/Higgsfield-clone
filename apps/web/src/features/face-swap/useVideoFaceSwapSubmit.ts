import { useCallback, useRef, useState } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import { submitVideoFaceSwap } from "../../api/videoFaceswapJobs"
import type { VideoFaceSwapInsufficient } from "../../api/videoFaceswapJobs"

type RenderState = {
  isSubmitting: boolean
  insufficient: VideoFaceSwapInsufficient | null
  failure: "limit" | "invalid" | "error" | null
}

type RenderControls = RenderState & {
  submit: (faceAssetId: string, targetAssetId: string, keyframeAssetId: string | null) => void
}

const IDLE: RenderState = { isSubmitting: false, insufficient: null, failure: null }

export function useVideoFaceSwapSubmit(
  run: RunWithGuestSession,
  onAccepted: (jobId: string) => void,
  onInsufficient: () => void,
): RenderControls {
  const [state, setState] = useState<RenderState>(IDLE)
  const isSubmittingRef = useRef(false)
  const refs = useRef({ accepted: onAccepted, insufficient: onInsufficient })
  refs.current = { accepted: onAccepted, insufficient: onInsufficient }

  const submit = useCallback(
    (faceAssetId: string, targetAssetId: string, keyframeAssetId: string | null) => {
      if (isSubmittingRef.current) return
      isSubmittingRef.current = true
      setState({ ...IDLE, isSubmitting: true })
      void submitVideoFaceSwap(run, faceAssetId, targetAssetId, keyframeAssetId).then((outcome) => {
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
