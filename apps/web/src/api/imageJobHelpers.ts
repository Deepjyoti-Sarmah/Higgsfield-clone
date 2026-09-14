import { apiClient } from "./client"
import type { components } from "./generated/schema"
import type { RunWithGuestSession } from "./guestSession"
import type { FetchJobResult } from "./jobStatusWatcher"

export type ImageJob = components["schemas"]["ImageJobResponse"]
export type ImageJobRequest = components["schemas"]["ImageJobCreateRequest"]

export type ImageJobSettings = {
  prompt: string
  aspect_ratio: ImageJobRequest["aspect_ratio"]
  quality: ImageJobRequest["quality"]
  count: number
}

export type ImageJobSubmitError = "network" | "session" | "invalid"
export type ImageInsufficient = { balance: number; required: number }

export type SubmitOutcome =
  | { kind: "accepted"; jobId: string; creditCost: number }
  | { kind: "insufficient"; insufficient: ImageInsufficient }
  | { kind: "error"; errorKind: ImageJobSubmitError }

export function readInsufficient(error: unknown): ImageInsufficient {
  const body = (error ?? {}) as Partial<ImageInsufficient>
  return { balance: body.balance ?? 0, required: body.required ?? 0 }
}

export function submitErrorKind(status: number): ImageJobSubmitError {
  if (status === 401) return "session"
  if (status === 422) return "invalid"
  return "network"
}

export async function postImageJob(
  run: RunWithGuestSession,
  settings: ImageJobSettings,
  idempotencyKey: string,
): Promise<SubmitOutcome> {
  const body: ImageJobRequest = { ...settings, idempotency_key: idempotencyKey }
  try {
    const outcome = await run(() => apiClient.POST("/api/v1/image-jobs", { body }))
    if (outcome.outcome === "session-failed") return { kind: "error", errorKind: "session" }
    const { data, response, error } = outcome.result
    if (response.status === 202 && data) {
      return { kind: "accepted", jobId: data.id, creditCost: data.credit_cost }
    }
    if (response.status === 402) {
      return { kind: "insufficient", insufficient: readInsufficient(error) }
    }
    return { kind: "error", errorKind: submitErrorKind(response.status) }
  } catch {
    return { kind: "error", errorKind: "network" }
  }
}

export async function fetchImageJob(jobId: string): Promise<FetchJobResult<ImageJob>> {
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
