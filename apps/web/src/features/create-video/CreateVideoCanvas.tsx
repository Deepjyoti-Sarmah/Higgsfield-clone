import type { RefObject } from "react"
import { CanvasHeading } from "./CanvasHeading"
import { FailureView } from "./FailureView"
import { HowItWorks } from "./HowItWorks"
import { JobProgressView } from "./JobProgressView"
import { ResultView } from "./ResultView"
import { createVideoCopy } from "./createVideoCopy"
import type { CanvasPhase, CanvasView, JobWatch } from "./createVideoTypes"

type CreateVideoCanvasProps = {
  phase: CanvasPhase
  canvas: CanvasView
  connection: JobWatch["connection"]
  headingRef: RefObject<HTMLHeadingElement | null>
  onMakeAnother: () => void
  onRetry: () => void
  onDismissMissing: () => void
}

const headingByPhase: Record<CanvasPhase, string> = {
  empty: createVideoCopy.howItWorks.heading,
  uploading: createVideoCopy.howItWorks.heading,
  ready: createVideoCopy.howItWorks.heading,
  submitting: createVideoCopy.progress.submittingHeading,
  queued: createVideoCopy.progress.queuedHeading,
  generating: createVideoCopy.progress.generatingHeading,
  succeeded: createVideoCopy.result.heading,
  failed: createVideoCopy.failure.heading,
}

type CanvasBodyProps = Omit<CreateVideoCanvasProps, "headingRef">

function CanvasBody(props: CanvasBodyProps) {
  const { phase, canvas, connection } = props
  if (phase === "succeeded") {
    if (canvas.job === null) return null
    return (
      <ResultView
        job={canvas.job}
        elapsedSeconds={canvas.elapsedSeconds}
        onMakeAnother={props.onMakeAnother}
      />
    )
  }
  if (phase === "failed") {
    return (
      <FailureView
        variant={canvas.isMissing ? "missing" : "failed"}
        job={canvas.job}
        onRetry={props.onRetry}
        onMakeAnother={props.onMakeAnother}
        onDismissMissing={props.onDismissMissing}
      />
    )
  }
  if (phase === "empty" || phase === "uploading" || phase === "ready") {
    return (
      <HowItWorks phase={phase} hasPreset={canvas.hasPreset} presetCount={canvas.presetCount} />
    )
  }
  return (
    <JobProgressView
      phase={phase}
      connection={connection}
      inputImageUrl={canvas.inputImageUrl}
      presetName={canvas.presetName}
      elapsedSeconds={canvas.elapsedSeconds}
      wasRequeued={canvas.wasRequeued}
    />
  )
}

export function CreateVideoCanvas({
  phase,
  canvas,
  connection,
  headingRef,
  onMakeAnother,
  onRetry,
  onDismissMissing,
}: CreateVideoCanvasProps) {
  const isMissingJob = phase === "failed" && canvas.isMissing
  const heading = isMissingJob ? createVideoCopy.failure.missingHeading : headingByPhase[phase]
  return (
    <section className="flex min-h-[320px] flex-col items-center justify-center gap-5 rounded-2xl border border-border bg-surface p-5 md:min-h-[420px]">
      <CanvasHeading text={heading} headingRef={headingRef} />
      <CanvasBody
        phase={phase}
        canvas={canvas}
        connection={connection}
        onMakeAnother={onMakeAnother}
        onRetry={onRetry}
        onDismissMissing={onDismissMissing}
      />
    </section>
  )
}
