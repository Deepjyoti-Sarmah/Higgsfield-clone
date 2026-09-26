import { apiClient } from "./client"
import type { RunWithGuestSession } from "./guestSession"

export type VideoFaceSwapInsufficient = { balance: number; required: number }

export type VideoFaceSwapSubmitOutcome =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient"; insufficient: VideoFaceSwapInsufficient }
  | { kind: "limit" }
  | { kind: "invalid" }
  | { kind: "error" }

export function videoFaceSwapJobBody(
  sourceAssetId: string,
  targetJobId: string,
  idempotencyKey: string,
  keyframeAssetId: string | null,
): { source_asset_id: string; target_job_id: string; keyframe_asset_id: string | null; idempotency_key: string } {
  return {
    source_asset_id: sourceAssetId,
    target_job_id: targetJobId,
    keyframe_asset_id: keyframeAssetId,
    idempotency_key: idempotencyKey,
  }
}

function insufficientOf(error: unknown): VideoFaceSwapInsufficient {
  const detail = (error ?? {}) as Partial<VideoFaceSwapInsufficient>
  return { balance: detail.balance ?? 0, required: detail.required ?? 0 }
}

const STATUS_KINDS: Record<number, "limit" | "invalid"> = {
  429: "limit",
  422: "invalid",
  404: "invalid",
}

// 404/422 both mean the picked face or video can't be swapped right now.
export function videoFaceSwapOutcomeFor(
  status: number,
  data: { id: string } | undefined,
  error: unknown,
): VideoFaceSwapSubmitOutcome {
  if (status === 202 && data) return { kind: "accepted", jobId: data.id }
  if (status === 402) return { kind: "insufficient", insufficient: insufficientOf(error) }
  const kind = STATUS_KINDS[status]
  return kind ? { kind } : { kind: "error" }
}

export async function submitVideoFaceSwap(
  run: RunWithGuestSession,
  sourceAssetId: string,
  targetJobId: string,
  keyframeAssetId: string | null,
): Promise<VideoFaceSwapSubmitOutcome> {
  try {
    const outcome = await run(() =>
      apiClient.POST("/api/v1/video-faceswap-jobs", {
        body: videoFaceSwapJobBody(sourceAssetId, targetJobId, crypto.randomUUID(), keyframeAssetId),
      }),
    )
    if (outcome.outcome === "session-failed") return { kind: "error" }
    const { data, response, error } = outcome.result
    return videoFaceSwapOutcomeFor(response.status, data, error)
  } catch {
    return { kind: "error" }
  }
}
