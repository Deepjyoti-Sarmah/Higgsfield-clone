import { ProgressBar } from "../../ui/ProgressBar"
import { imageCreateCopy } from "./imageCreateCopy"
import type { ImageProgressPhase as ProgressPhase } from "./imageSettings"

type ImageProgressViewProps = {
  phase: ProgressPhase
  prompt: string
  elapsedSeconds: number
  wasRequeued: boolean
  connection: "idle" | "live" | "polling"
}

const subCopy: Record<ProgressPhase, string> = {
  submitting: imageCreateCopy.generate.submitting,
  queued: imageCreateCopy.progress.queuedSub,
  running: imageCreateCopy.progress.generatingSub,
}

const stepLabel: Record<ProgressPhase, string> = {
  submitting: imageCreateCopy.progress.queued,
  queued: imageCreateCopy.progress.queued,
  running: imageCreateCopy.progress.running,
}

function formatElapsed(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(safeSeconds / 60)
  const remainder = safeSeconds % 60
  return `${minutes}:${String(remainder).padStart(2, "0")}`
}

export function ImageProgressView({
  phase,
  prompt,
  elapsedSeconds,
  wasRequeued,
  connection,
}: ImageProgressViewProps) {
  const sub = phase === "queued" && wasRequeued ? imageCreateCopy.progress.requeuedSub : subCopy[phase]
  return (
    <div
      role="status"
      className="flex w-full flex-col items-center gap-4 rounded-2xl border border-border bg-surface px-6 py-10 text-center"
    >
      <p className="text-sm font-semibold text-text">{stepLabel[phase]}</p>
      {prompt !== "" && <p className="max-w-sm truncate text-xs text-muted">"{prompt}"</p>}
      <p className="text-center text-xs text-muted">{sub}</p>
      <p className="text-xs text-muted">{imageCreateCopy.progress.elapsed(formatElapsed(elapsedSeconds))}</p>
      <div className="w-full max-w-xs">
        <ProgressBar value={null} label={imageCreateCopy.progress.barLabel} />
      </div>
      {connection === "polling" && (
        <p className="text-xs text-muted">{imageCreateCopy.progress.polling}</p>
      )}
    </div>
  )
}
