import { FACESWAP_CREDIT_COST } from "./faceSwapCost"
import { faceSwapCopy } from "./faceSwapCopy"
import { useKeyframePreview } from "./useKeyframePreview"
import type { KeyframePhase } from "./useKeyframePreview"
import type { RunWithGuestSession } from "../../api/guestSession"

const copy = faceSwapCopy.videoPreview

type VideoFaceSwapPreviewProps = {
  run: RunWithGuestSession
  faceAssetId: string | null
  targetUrl: string | null
  onKeyframeReady: (assetId: string) => void
}

function PreviewStatus({ phase }: { phase: KeyframePhase }) {
  if (phase === "ready") return <p className="text-xs text-muted">{copy.ready}</p>
  if (phase === "failed") {
    return (
      <p role="alert" className="text-xs text-danger">
        {copy.failed}
      </p>
    )
  }
  if (phase === "insufficient") {
    return (
      <p role="alert" className="text-xs text-danger">
        {copy.insufficient(FACESWAP_CREDIT_COST)}
      </p>
    )
  }
  return null
}

export function VideoFaceSwapPreview({ run, faceAssetId, targetUrl, onKeyframeReady }: VideoFaceSwapPreviewProps) {
  const preview = useKeyframePreview(run, faceAssetId, targetUrl, onKeyframeReady)
  const label = preview.phase === "working"
    ? copy.working
    : preview.imageUrl !== null
      ? copy.retry
      : copy.action
  return (
    <div className="space-y-2 rounded-xl border border-border bg-sunken p-3">
      <p className="text-sm font-medium text-text">{copy.title}</p>
      <p className="text-xs text-muted">{copy.body}</p>
      {preview.imageUrl !== null && (
        <img src={preview.imageUrl} alt="" className="max-h-48 rounded-xl border border-border object-contain" />
      )}
      <PreviewStatus phase={preview.phase} />
      <button
        type="button"
        onClick={preview.startPreview}
        disabled={!preview.canPreview}
        className="h-9 rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text transition-colors hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {label}
      </button>
    </div>
  )
}
