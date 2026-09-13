import { useEffect, useState } from "react"
import { apiClient } from "../../api/client"
import { createJobStatusWatcher } from "../../api/jobStatusWatcher"
import type { FetchJobResult, WatcherDeps } from "../../api/jobStatusWatcher"
import type { Job, JobStatus, JobWatch } from "./createVideoTypes"

const initialWatch: JobWatch = {
  job: null,
  status: null,
  connection: "idle",
  isMissing: false,
  wasRequeued: false,
}

type WatchState = { jobId: string | null; watch: JobWatch }

async function fetchJob(jobId: string): Promise<FetchJobResult<Job>> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/jobs/{job_id}", {
      params: { path: { job_id: jobId } },
    })
    if (response.status === 200 && data) return { kind: "ok", job: data }
    if (response.status === 401 || response.status === 404) return { kind: "missing" }
    return { kind: "network" }
  } catch {
    return { kind: "network" }
  }
}

const watcherDeps: WatcherDeps<Job> = {
  openEventSource: (url: string) => new EventSource(url),
  fetchJob,
}

function applyJob(current: JobWatch, job: Job): JobWatch {
  return { ...current, job, status: current.status ?? job.status }
}

function applyStatus(current: JobWatch, status: JobStatus): JobWatch {
  if (status === "running") return { ...current, status, wasRequeued: false }
  if (status === "queued" && current.status === "running") {
    return { ...current, status, wasRequeued: true }
  }
  return { ...current, status }
}

export function useJobEvents(jobId: string | null): JobWatch {
  const [state, setState] = useState<WatchState>({ jobId: null, watch: initialWatch })

  useEffect(() => {
    setState({ jobId, watch: initialWatch })
    if (jobId === null) return
    const apply = (change: (watch: JobWatch) => JobWatch) =>
      setState((current) =>
        current.jobId === jobId ? { ...current, watch: change(current.watch) } : current,
      )
    const watcher = createJobStatusWatcher<Job>(jobId, watcherDeps, {
      onJob: (job) => apply((current) => applyJob(current, job)),
      onStatus: (status) => apply((current) => applyStatus(current, status)),
      onConnection: (connection) => apply((current) => ({ ...current, connection })),
      onMissing: () => apply((current) => ({ ...current, isMissing: true })),
    })
    return () => watcher.stop()
  }, [jobId])

  return state.jobId === jobId ? state.watch : initialWatch
}
