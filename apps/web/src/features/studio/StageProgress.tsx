import { useEffect, useState } from "react"
import { ProgressBar } from "../../ui/ProgressBar"

type StageProgressProps = {
  kind: "video" | "image" | "sequence"
  jobId: string
  status: "queued" | "running" | "succeeded" | "failed" | null
}

function useElapsedSeconds(): number {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    const timer = window.setInterval(() => setSeconds((current) => current + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])
  return seconds
}

export function StageProgress({ kind, status }: StageProgressProps) {
  const elapsed = useElapsedSeconds()
  const phase = status ?? "queued"
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
