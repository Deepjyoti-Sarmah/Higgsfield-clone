import { useCallback } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import { faceSwapCopy } from "./faceSwapCopy"
import { useVideoFaceSwapSubmit } from "./useVideoFaceSwapSubmit"
import { isVideoTargetTooLong, videoRenderCost } from "./videoFaceSwapCost"

const copy = faceSwapCopy.videoRender

type VideoFaceSwapRenderProps = {
  run: RunWithGuestSession
  faceAssetId: string | null
  targetReady: boolean
  targetAssetId: string | null
  durationMs: number | null
  keyframeAssetId: string | null
  onJobStarted: (jobId: string) => void
  onInsufficient: () => void
}

type RenderBlock = "no-face" | "no-target" | "too-long" | "needs-rail" | "reading" | null

function renderBlock(props: VideoFaceSwapRenderProps): RenderBlock {
  if (props.faceAssetId === null) return "no-face"
  if (!props.targetReady) return "no-target"
  if (props.durationMs === null) return "reading"
  if (isVideoTargetTooLong(props.durationMs)) return "too-long"
  if (props.targetAssetId === null) return "needs-rail"
  return null
}

function blockedMessage(blocked: RenderBlock): string | null {
  if (blocked === "no-face") return copy.blockedNoFace
  if (blocked === "no-target") return copy.blockedNoTarget
  if (blocked === "too-long") return copy.blockedTooLong
  if (blocked === "needs-rail") return faceSwapCopy.videoTarget.renderNeedsRail
  return null
}

function FailureLine({ failure }: { failure: "limit" | "invalid" | "error" | null }) {
  if (failure === "limit") {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {copy.limitHit}
      </p>
    )
  }
  if (failure === "invalid") {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {copy.invalid}
      </p>
    )
  }
  if (failure === "error") {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {copy.networkToast}
      </p>
    )
  }
  return null
}

function renderLabel(isSubmitting: boolean, cost: number | null): string {
  if (isSubmitting) return copy.submitting
  return copy.renderWithCost(cost ?? 0)
}

type RenderNotesProps = {
  blocked: RenderBlock
  insufficient: { balance: number; required: number } | null
  failure: "limit" | "invalid" | "error" | null
}

function RenderNotes({ blocked, insufficient, failure }: RenderNotesProps) {
  const message = blockedMessage(blocked)
  if (message !== null) return <p className="text-[13px] text-faint">{message}</p>
  if (insufficient !== null) {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {copy.insufficient(insufficient.balance, insufficient.required)}
      </p>
    )
  }
  if (failure !== null) return <FailureLine failure={failure} />
  return <p className="text-[13px] text-muted">{copy.previewNote}</p>
}

export function VideoFaceSwapRender(props: VideoFaceSwapRenderProps) {
  const render = useVideoFaceSwapSubmit(props.run, props.onJobStarted, props.onInsufficient)
  const blocked = renderBlock(props)

  const startRender = useCallback(() => {
    if (props.faceAssetId === null || props.targetAssetId === null) return
    render.submit(props.faceAssetId, props.targetAssetId, props.keyframeAssetId)
  }, [props.faceAssetId, props.targetAssetId, props.keyframeAssetId, render])

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={startRender}
        disabled={blocked !== null || render.isSubmitting}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-[10px] bg-accent px-4 font-mono text-sm font-medium text-accent-ink transition-all duration-150 hover:bg-accent/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
      >
        {renderLabel(render.isSubmitting, videoRenderCost(props.durationMs))}
      </button>
      <RenderNotes blocked={blocked} insufficient={render.insufficient} failure={render.failure} />
    </div>
  )
}
