import { SHOWCASE_STILLS } from "../../api/webMedia"
import { Button } from "../../ui/Button"
import { EmptyState } from "../../ui/EmptyState"
import { ImageFailureView } from "./ImageFailureView"
import { imageCreateCopy } from "./imageCreateCopy"
import type { ImageJobWatch, ImageStagePhase } from "./imageCreateTypes"
import { ImageResultGrid } from "./ImageResultGrid"

type ImageStageProps = {
  phase: ImageStagePhase
  watch: ImageJobWatch
  onRetry: () => void
  onMakeAnother: () => void
}

function OptionsLoading() {
  return (
    <div aria-busy="true" className="flex w-full flex-col gap-3">
      <p className="sr-only">{imageCreateCopy.states.loading.srText}</p>
      <div className="h-24 w-full animate-pulse rounded-2xl border border-border bg-surface" />
    </div>
  )
}

function OptionsError({ onRetry }: { onRetry: () => void }) {
  const copy = imageCreateCopy.states.optionsError
  return (
    <EmptyState
      title={copy.title}
      description={copy.body}
      action={<Button onClick={onRetry}>{copy.action}</Button>}
    />
  )
}

function JobProgress({ phase }: { phase: ImageStagePhase }) {
  const copy = imageCreateCopy
  const message =
    phase === "submitting"
      ? copy.generate.submitting
      : phase === "queued"
        ? copy.progress.queued
        : phase === "running"
          ? copy.progress.running
          : null
  if (message === null) return null
  return (
    <p role="status" className="text-sm text-muted">
      {message}
    </p>
  )
}

function SucceededStage({
  watch,
  onRetry,
  onMakeAnother,
}: {
  watch: ImageJobWatch
  onRetry: () => void
  onMakeAnother: () => void
}) {
  const job = watch.job
  if (job === null || job.image_urls.length === 0) {
    return <ImageFailureView isMissing={false} onRetry={onRetry} onMakeAnother={onMakeAnother} />
  }
  return (
    <div className="flex w-full flex-col items-center gap-3">
      <p role="status" className="text-sm text-muted">
        {imageCreateCopy.progress.succeeded}
      </p>
      <ImageResultGrid
        imageUrls={job.image_urls}
        prompt={job.prompt}
        backend={job.backend}
        onMakeAnother={onMakeAnother}
      />
    </div>
  )
}

function ImageIdleShowcase() {
  return (
    <div className="flex w-full flex-col gap-4 py-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xs uppercase tracking-wider text-muted">
          ✦ Sample Image Generations
        </h2>
        <span className="text-xs font-semibold text-accent">GPT IMAGE 2 · 4K</span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {SHOWCASE_STILLS.map((img) => (
          <div
            key={img.title}
            className="group relative aspect-[3/4] overflow-hidden rounded-2xl border border-border bg-surface shadow-lg transition-transform duration-300 hover:scale-[1.02] hover:border-accent/60"
          >
            <img
              src={img.url}
              alt={img.title}
              loading="lazy"
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/80 via-transparent to-transparent p-3 text-left">
              <span className="text-[10px] font-bold text-accent">{img.aspect}</span>
              <span className="text-xs font-semibold text-text line-clamp-1">{img.title}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ImageStage({ phase, watch, onRetry, onMakeAnother }: ImageStageProps) {
  if (phase === "options-loading") return <OptionsLoading />
  if (phase === "options-error") return <OptionsError onRetry={onRetry} />
  if (phase === "succeeded") {
    return <SucceededStage watch={watch} onRetry={onRetry} onMakeAnother={onMakeAnother} />
  }
  if (phase === "failed" || phase === "missing") {
    return (
      <ImageFailureView
        isMissing={phase === "missing"}
        onRetry={onRetry}
        onMakeAnother={onMakeAnother}
      />
    )
  }
  if (phase === "idle") {
    return <ImageIdleShowcase />
  }
  return <JobProgress phase={phase} />
}
