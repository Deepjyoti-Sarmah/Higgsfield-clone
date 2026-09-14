import { apiClient } from "../../api/client"
import type { FetchJobResult } from "../../api/jobStatusWatcher"
import type { Job } from "./createVideoTypes"

export async function fetchVideoJob(jobId: string): Promise<FetchJobResult<Job>> {
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
