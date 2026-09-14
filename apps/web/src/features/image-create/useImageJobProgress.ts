import { apiClient } from "../../api/client"
import type { ImageJob } from "../../api/imageJobs"
import type { FetchJobResult } from "../../api/jobStatusWatcher"
import { useJobEvents } from "../../api/useJobEvents"
import type { JobWatch } from "../../api/useJobEvents"

// Parallel to useImageJob's own watcher (api/imageJobs.ts is off-limits, and keeps this
// fetch private): reuses the shared jobStatusWatcher purely for live progress. fetchImageJob
// is duplicated, not imported, since a clean checkout has no imageJobHelpers.ts (uncommitted).
async function fetchImageJob(jobId: string): Promise<FetchJobResult<ImageJob>> {
  try {
    const { data, response } = await apiClient.GET("/api/v1/image-jobs/{job_id}", {
      params: { path: { job_id: jobId } },
    })
    if (response.status === 200 && data) return { kind: "ok", job: data }
    if (response.status === 401 || response.status === 404) return { kind: "missing" }
    return { kind: "network" }
  } catch {
    return { kind: "network" }
  }
}

export function useImageJobProgress(jobId: string | null): JobWatch<ImageJob> {
  return useJobEvents<ImageJob>(jobId, fetchImageJob)
}
