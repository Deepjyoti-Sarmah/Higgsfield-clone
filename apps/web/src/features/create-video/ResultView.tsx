import { GenerationBadge } from "../../ui/GenerationBadge"
import { createVideoCopy } from "./createVideoCopy"
import type { Job } from "./createVideoTypes"
import { formatElapsed } from "./elapsedTime"
import { ResultActions } from "./ResultActions"
import { usePrefersReducedMotion } from "./usePrefersReducedMotion"

type ResultViewProps = {
  job: Job
  elapsedSeconds: number
  onMakeAnother: () => void
}

function ResultVideo({ job, hasReducedMotion }: { job: Job; hasReducedMotion: boolean }) {
  if (job.video_url === null) return null
  return (
    <video
      src={job.video_url}
      poster={job.poster_url ?? undefined}
      autoPlay={!hasReducedMotion}
      muted
      loop
      playsInline
      controls
      className="w-full max-w-2xl rounded-xl border border-border"
    />
  )
}

export function ResultView({ job, elapsedSeconds, onMakeAnother }: ResultViewProps) {
  const hasReducedMotion = usePrefersReducedMotion()
  return (
    <div className="flex w-full flex-col items-center gap-4">
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-muted">
        <span>{createVideoCopy.result.meta(job.preset_name, formatElapsed(elapsedSeconds))}</span>
        <GenerationBadge generatedBy={job.generated_by} />
      </div>
      <ResultVideo job={job} hasReducedMotion={hasReducedMotion} />
      <ResultActions job={job} onMakeAnother={onMakeAnother} />
    </div>
  )
}
