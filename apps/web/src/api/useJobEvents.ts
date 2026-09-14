import { useEffect, useState } from "react"
import { createJobStatusWatcher } from "./jobStatusWatcher"
import type { FetchJobResult, WatcherDeps } from "./jobStatusWatcher"
import type { JobStatus } from "./jobStatus"

// Shared by create-video and image-create: any job shape with a status can be watched.
export type JobWatch<J> = {
  job: J | null
  status: JobStatus | null
  connection: "idle" | "live" | "polling"
  isMissing: boolean
  wasRequeued: boolean
}

function initialWatch<J>(): JobWatch<J> {
  return { job: null, status: null, connection: "idle", isMissing: false, wasRequeued: false }
}

type WatchState<J> = { jobId: string | null; watch: JobWatch<J> }

function applyJob<J>(current: JobWatch<J>, job: J): JobWatch<J> {
  return { ...current, job, status: current.status ?? (job as { status: JobStatus }).status }
}

function applyStatus<J>(current: JobWatch<J>, status: JobStatus): JobWatch<J> {
  if (status === "running") return { ...current, status, wasRequeued: false }
  if (status === "queued" && current.status === "running") {
    return { ...current, status, wasRequeued: true }
  }
  return { ...current, status }
}

export function useJobEvents<J extends { status: JobStatus }>(
  jobId: string | null,
  fetchJob: (jobId: string) => Promise<FetchJobResult<J>>,
): JobWatch<J> {
  const [state, setState] = useState<WatchState<J>>({ jobId: null, watch: initialWatch<J>() })

  useEffect(() => {
    setState({ jobId, watch: initialWatch<J>() })
    if (jobId === null) return
    const apply = (change: (watch: JobWatch<J>) => JobWatch<J>) =>
      setState((current) =>
        current.jobId === jobId ? { ...current, watch: change(current.watch) } : current,
      )
    const watcherDeps: WatcherDeps<J> = {
      openEventSource: (url: string) => new EventSource(url),
      fetchJob,
    }
    const watcher = createJobStatusWatcher<J>(jobId, watcherDeps, {
      onJob: (job) => apply((current) => applyJob(current, job)),
      onStatus: (status) => apply((current) => applyStatus(current, status)),
      onConnection: (connection) => apply((current) => ({ ...current, connection })),
      onMissing: () => apply((current) => ({ ...current, isMissing: true })),
    })
    return () => watcher.stop()
  }, [jobId, fetchJob])

  return state.jobId === jobId ? state.watch : initialWatch<J>()
}
