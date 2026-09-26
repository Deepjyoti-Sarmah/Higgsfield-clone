import { apiClient } from "./client"
import type { RunWithGuestSession } from "./guestSession"

export type FaceSwapInsufficient = { balance: number; required: number }

export type FaceSwapSubmitOutcome =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient"; insufficient: FaceSwapInsufficient }
  | { kind: "limit" }
  | { kind: "invalid" }
  | { kind: "error" }

export function faceSwapJobBody(
  sourceAssetId: string,
  targetAssetId: string,
  idempotencyKey: string,
): { source_asset_id: string; target_asset_id: string; idempotency_key: string } {
  return {
    source_asset_id: sourceAssetId,
    target_asset_id: targetAssetId,
    idempotency_key: idempotencyKey,
  }
}

function insufficientOf(error: unknown): FaceSwapInsufficient {
  const detail = (error ?? {}) as Partial<FaceSwapInsufficient>
  return { balance: detail.balance ?? 0, required: detail.required ?? 0 }
}

const STATUS_KINDS: Record<number, "limit" | "invalid"> = {
  429: "limit",
  422: "invalid",
  404: "invalid",
}

// 404/422 both mean the picked images can't be swapped right now; the composer shows one message.
function outcomeFor(
  status: number,
  data: { id: string } | undefined,
  error: unknown,
): FaceSwapSubmitOutcome {
  if (status === 202 && data) return { kind: "accepted", jobId: data.id }
  if (status === 402) return { kind: "insufficient", insufficient: insufficientOf(error) }
  const kind = STATUS_KINDS[status]
  return kind ? { kind } : { kind: "error" }
}

export async function submitFaceSwap(
  run: RunWithGuestSession,
  sourceAssetId: string,
  targetAssetId: string,
): Promise<FaceSwapSubmitOutcome> {
  try {
    const outcome = await run(() =>
      apiClient.POST("/api/v1/faceswap-jobs", {
        body: faceSwapJobBody(sourceAssetId, targetAssetId, crypto.randomUUID()),
      }),
    )
    if (outcome.outcome === "session-failed") return { kind: "error" }
    const { data, response, error } = outcome.result
    return outcomeFor(response.status, data, error)
  } catch {
    return { kind: "error" }
  }
}
