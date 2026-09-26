import { Button } from "../../ui/Button"
import { faceSwapCopy } from "./faceSwapCopy"
import type { WellControls, WellErrorKind } from "./faceSwapTypes"

const errorMessage: Record<WellErrorKind, string> = {
  network: faceSwapCopy.image.networkError,
  session: faceSwapCopy.image.sessionError,
  "not-finished": faceSwapCopy.image.notFinishedError,
}

export function SeededPreview({ url, onReplace }: { url: string; onReplace: () => void }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-sunken p-2">
      <img src={url} alt={faceSwapCopy.image.alt} className="h-14 w-14 rounded-lg object-cover" />
      <button type="button" onClick={onReplace} className="text-xs text-muted underline hover:text-text">
        {faceSwapCopy.image.seededRemove}
      </button>
    </div>
  )
}

function IdleWell({ onBrowse }: { onBrowse: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 py-4 text-center">
      <p className="text-xs text-muted">{faceSwapCopy.image.idleTitle}</p>
      <Button variant="secondary" onClick={onBrowse}>
        {faceSwapCopy.image.browse}
      </Button>
    </div>
  )
}

function ErrorWell({ kind, onRetry }: { kind: WellErrorKind; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 py-4 text-center">
      <p role="alert" className="text-xs text-danger">
        {errorMessage[kind]}
      </p>
      <Button variant="secondary" onClick={onRetry}>
        {faceSwapCopy.image.retry}
      </Button>
    </div>
  )
}

function FilledWell({ url, isUploading, progress, onRemove }: {
  url: string
  isUploading: boolean
  progress: number
  onRemove: () => void
}) {
  return (
    <div className="flex items-center gap-3 p-2">
      <img src={url} alt={faceSwapCopy.image.alt} className="h-14 w-14 rounded-lg object-cover" />
      {isUploading ? (
        <span className="font-mono text-[13px] text-muted">{Math.round(progress * 100)}%</span>
      ) : (
        <button type="button" onClick={onRemove} className="text-xs text-muted underline hover:text-text">
          {faceSwapCopy.image.seededRemove}
        </button>
      )}
    </div>
  )
}

export function WellPreview({ upload, onBrowse }: { upload: WellControls; onBrowse: () => void }) {
  const state = upload.state
  if (state.status === "idle") return <IdleWell onBrowse={onBrowse} />
  if (state.status === "error") return <ErrorWell kind={state.errorKind} onRetry={upload.retryUpload} />
  return (
    <FilledWell
      url={state.previewUrl}
      isUploading={state.status === "uploading"}
      progress={state.status === "uploading" ? state.progress : 1}
      onRemove={upload.clearImage}
    />
  )
}
