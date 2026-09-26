import { useCallback, useEffect, useState } from "react"
import { fetchJobForProgress } from "../../api/jobProgress"
import { isTerminalJobStatus } from "../../api/jobStatus"
import { useJobEvents } from "../../api/useJobEvents"
import { ProgressBar } from "../../ui/ProgressBar"

type StageProgressProps = {
  kind: "video" | "image" | "sequence" | "faceswap"
  jobId: string
  status: "queued" | "running" | "succeeded" | "failed" | null
  onSettled: () => void
}

function useElapsedSeconds(): number {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    const timer = window.setInterval(() => setSeconds((current) => current + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])
  return seconds
}

// The Library row is a snapshot; watch the job itself and refresh the Library once it ends.
function useLiveStatus(kind: StageProgressProps["kind"], jobId: string, onSettled: () => void) {
  const fetchJob = useCallback((id: string) => fetchJobForProgress(kind, id), [kind])
  const watch = useJobEvents(jobId, fetchJob)
  const live = watch.status
  useEffect(() => {
    if (live !== null && isTerminalJobStatus(live)) onSettled()
  }, [live, onSettled])
  return live
}

export function StageProgress({ kind, jobId, status, onSettled }: StageProgressProps) {
  const elapsed = useElapsedSeconds()
  const live = useLiveStatus(kind, jobId, onSettled)
  const phase = live ?? status ?? "queued"
  return (
    <div className="w-full max-w-md space-y-3 text-center">
      <p className="font-display text-2xl text-text">
        {phase === "running" ? "Rendering" : "Queued"}
      </p>
      <p className="font-mono text-[13px] text-muted" aria-live="polite">
        {elapsed}s elapsed
      </p>
      <ProgressBar value={null} label={`${kind} render progress`} />
    </div>
  )
}
