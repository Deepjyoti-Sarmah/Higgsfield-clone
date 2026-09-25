import { apiClient } from "../../api/client"
import type { RunWithGuestSession } from "../../api/guestSession"
import type { ImageInsufficient } from "../../api/imageJobs"
import type { ImageSettings } from "./imageCreateTypes"

export type StillSubmitSettings = {
  prompt: string
  aspect_ratio: ImageSettings["aspectRatio"]
  quality: ImageSettings["quality"]
  count: number
}

export type StillSubmitOutcome =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient"; insufficient: ImageInsufficient }
  | { kind: "limit" }
  | { kind: "error" }

export function stillJobBody(
  settings: StillSubmitSettings,
  idempotencyKey: string,
): { prompt: string; aspect_ratio: ImageSettings["aspectRatio"]; quality: ImageSettings["quality"]; count: number; idempotency_key: string } {
  return { ...settings, idempotency_key: idempotencyKey }
}

const STATUS_KINDS = { 402: "insufficient", 429: "limit" } as const

function insufficientOf(error: unknown): ImageInsufficient {
  const detail = (error ?? {}) as Partial<ImageInsufficient>
  return { balance: detail.balance ?? 0, required: detail.required ?? 0 }
}

export async function submitStill(
  run: RunWithGuestSession,
  settings: StillSubmitSettings,
): Promise<StillSubmitOutcome> {
  try {
    const outcome = await run(() =>
      apiClient.POST("/api/v1/image-jobs", { body: stillJobBody(settings, crypto.randomUUID()) }),
    )
    if (outcome.outcome === "session-failed") return { kind: "error" }
    const { data, response, error } = outcome.result
    if (response.status === 202 && data) return { kind: "accepted", jobId: data.id }
    if (response.status === 402) {
      return { kind: "insufficient", insufficient: insufficientOf(error) }
    }
    const kind = STATUS_KINDS[response.status as 402 | 429] ?? "error"
    return { kind } as StillSubmitOutcome
  } catch {
    return { kind: "error" }
  }
}

// Disabled reason from the pure blocked rules plus the options state.
export function stillBlockedReason(
  prompt: string,
  hasOptions: boolean,
): "no-prompt" | "options-unavailable" | null {
  if (!hasOptions) return "options-unavailable"
  return prompt.trim() === "" ? "no-prompt" : null
}
