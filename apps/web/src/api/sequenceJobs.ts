import { apiClient } from "./client"
import type { components } from "./generated/schema"
import type { RunWithGuestSession } from "./guestSession"

export type SequenceClipIn = components["schemas"]["SequenceClipIn"]
export type SequenceCreateBody = components["schemas"]["SequenceJobCreateRequest"]
export type SequenceJobCreated = components["schemas"]["SequenceJobCreatedResponse"]

export type SequenceSubmitOutcome =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient" }
  | { kind: "clip-invalid" }
  | { kind: "limit" }
  | { kind: "session" }
  | { kind: "network" }

export function sequenceRequestBody(
  clips: SequenceClipIn[],
  audioAssetId: string | null,
  idempotencyKey: string,
): SequenceCreateBody {
  return {
    clips,
    audio_asset_id: audioAssetId ?? undefined,
    idempotency_key: idempotencyKey,
  }
}

const STATUS_KINDS: Record<number, SequenceSubmitOutcome["kind"]> = {
  402: "insufficient",
  404: "clip-invalid",
  422: "clip-invalid",
  429: "limit",
  401: "session",
}

// Maps the router's status codes (202/402/404/422/429) onto UI outcomes.
export async function createSequenceJob(
  run: RunWithGuestSession,
  body: SequenceCreateBody,
): Promise<SequenceSubmitOutcome> {
  let result
  try {
    const outcome = await run(() => apiClient.POST("/api/v1/sequence-jobs", { body }))
    if (outcome.outcome === "session-failed") return { kind: "session" }
    result = outcome.result
  } catch {
    return { kind: "network" }
  }
  const { data, response } = result
  if (response.status === 202 && data) return { kind: "accepted", jobId: data.id }
  const kind = STATUS_KINDS[response.status] ?? "network"
  return { kind } as SequenceSubmitOutcome
}
