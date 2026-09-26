import { apiClient } from "./client"
import type { FetchJobResult } from "./jobStatusWatcher"

export type ProgressJob = {
  status: "queued" | "running" | "succeeded" | "failed"
  generated_by?: string | null
  error_message?: string | null
}

type JobKind = "video" | "image" | "sequence" | "faceswap"

type FetchOutcome = { data: ProgressJob | undefined; response: Response }

async function readJob(
  call: () => Promise<FetchOutcome>,
): Promise<FetchJobResult<ProgressJob>> {
  try {
    const { data, response } = await call()
    if (response.status === 200 && data) return { kind: "ok", job: data }
    if (response.status === 401 || response.status === 404) return { kind: "missing" }
    return { kind: "network" }
  } catch {
    return { kind: "network" }
  }
}

// Pure helper: which endpoint each kind reads, exported for the unit test.
export function progressPathFor(kind: JobKind): string {
  if (kind === "image") return "/api/v1/image-jobs/{job_id}"
  if (kind === "sequence") return "/api/v1/sequence-jobs/{job_id}"
  if (kind === "faceswap") return "/api/v1/faceswap-jobs/{job_id}"
  return "/api/v1/jobs/{job_id}"
}

export function fetchJobForProgress(kind: JobKind, jobId: string): Promise<FetchJobResult<ProgressJob>> {
  const params = { params: { path: { job_id: jobId } } }
  if (kind === "image") {
    return readJob(async () => {
      const result = await apiClient.GET("/api/v1/image-jobs/{job_id}", params)
      return { data: result.data, response: result.response }
    })
  }
  if (kind === "sequence") {
    return readJob(async () => {
      const result = await apiClient.GET("/api/v1/sequence-jobs/{job_id}", params)
      return { data: result.data, response: result.response }
    })
  }
  if (kind === "faceswap") {
    return readJob(async () => {
      const result = await apiClient.GET("/api/v1/faceswap-jobs/{job_id}", params)
      return { data: result.data, response: result.response }
    })
  }
  return readJob(async () => {
    const result = await apiClient.GET("/api/v1/jobs/{job_id}", params)
    return { data: result.data, response: result.response }
  })
}
