import { ProgressBar } from "../../ui/ProgressBar"
import { createVideoCopy } from "./createVideoCopy"
import type { JobWatch } from "./createVideoTypes"
import { formatElapsed } from "./elapsedTime"
import { StatusSteps } from "./StatusSteps"

type ProgressPhase = "submitting" | "queued" | "generating"

type JobProgressViewProps = {
  phase: ProgressPhase
  inputImageUrl: string | null
  presetName: string
  elapsedSeconds: number
  wasRequeued: boolean
  connection: JobWatch["connection"]
}

const subCopy: Record<ProgressPhase, string> = {
  submitting: createVideoCopy.progress.submittingSub,
  queued: createVideoCopy.progress.queuedSub,
  generating: createVideoCopy.progress.generatingSub,
}

function currentStep(phase: ProgressPhase): "queued" | "generating" | "done" {
  return phase === "generating" ? "generating" : "queued"
}

export function JobProgressView({
  phase,
  inputImageUrl,
  presetName,
  elapsedSeconds,
  wasRequeued,
  connection,
}: JobProgressViewProps) {
  const sub = phase === "queued" && wasRequeued ? createVideoCopy.progress.requeuedSub : subCopy[phase]
  return (
    <div className="flex w-full flex-col items-center gap-4">
      {inputImageUrl !== null && (
        <img
          src={inputImageUrl}
          alt=""
          className="aspect-video w-full max-w-xs rounded-xl border border-border object-cover"
        />
      )}
      <p className="text-sm font-semibold text-text">{presetName}</p>
      <p className="text-center text-xs text-muted">{sub}</p>
      <p className="text-xs text-muted">
        {createVideoCopy.progress.elapsed(formatElapsed(elapsedSeconds))}
      </p>
      <StatusSteps current={currentStep(phase)} />
      <div className="w-full max-w-xs">
        <ProgressBar value={null} label={createVideoCopy.progress.barLabel} />
      </div>
      {connection === "polling" && (
        <p className="text-xs text-muted">{createVideoCopy.progress.polling}</p>
      )}
    </div>
  )
}
