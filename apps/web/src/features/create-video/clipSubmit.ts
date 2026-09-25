import { apiClient } from "../../api/client"
import type { RunWithGuestSession } from "../../api/guestSession"
import type { InsufficientCredits } from "./createVideoTypes"
import type { SeedImage } from "../../api/studioContracts"

export type ClipInputImage = {
  assetId: string
  previewUrl: string | null
  fromSeed: boolean
}

// A seeded still is used as-is with no upload; a picked file replaces it.
export function clipInputImage(
  seed: SeedImage | null,
  uploadAssetId: string | null,
  uploadPreviewUrl: string | null,
): ClipInputImage | null {
  if (uploadAssetId !== null) {
    return { assetId: uploadAssetId, previewUrl: uploadPreviewUrl, fromSeed: false }
  }
  if (seed !== null) {
    return { assetId: seed.assetId, previewUrl: seed.url, fromSeed: true }
  }
  return null
}

export type ClipBlockedReason = "no-image" | "no-preset" | "no-image-no-preset" | "uploading" | null

export function clipBlockedReason(
  input: ClipInputImage | null,
  hasPreset: boolean,
  isUploading: boolean,
): ClipBlockedReason {
  if (isUploading) return "uploading"
  if (input === null) return hasPreset ? "no-image" : "no-image-no-preset"
  if (!hasPreset) return "no-preset"
  return null
}

export function clipBlockedMessage(
  reason: ClipBlockedReason,
  copy: {
    blockedNoImageNoPreset: string
    blockedNoImage: string
    blockedNoPreset: string
    blockedUploading: string
  },
): string | null {
  if (reason === "no-image-no-preset") return copy.blockedNoImageNoPreset
  if (reason === "no-image") return copy.blockedNoImage
  if (reason === "no-preset") return copy.blockedNoPreset
  if (reason === "uploading") return copy.blockedUploading
  return null
}

export type ClipSubmitOutcome =
  | { kind: "accepted"; jobId: string }
  | { kind: "insufficient"; insufficient: InsufficientCredits }
  | { kind: "limit" }
  | { kind: "error" }

function readInsufficient(error: unknown): InsufficientCredits {
  const detail = (error ?? {}) as Partial<InsufficientCredits>
  return {
    detail: detail.detail ?? "",
    balance: detail.balance ?? 0,
    required: detail.required ?? 0,
  }
}

export async function postClipJob(
  run: RunWithGuestSession,
  body: ReturnType<typeof clipJobBody>,
): Promise<ClipSubmitOutcome> {
  try {
    const outcome = await run(() => apiClient.POST("/api/v1/jobs", { body }))
    if (outcome.outcome === "session-failed") return { kind: "error" }
    const { data, response, error } = outcome.result
    if (response.status === 202 && data) return { kind: "accepted", jobId: data.id }
    if (response.status === 402) {
      return { kind: "insufficient", insufficient: readInsufficient(error) }
    }
    return response.status === 429 ? { kind: "limit" } : { kind: "error" }
  } catch {
    return { kind: "error" }
  }
}

export function clipJobBody(
  input: ClipInputImage,
  presetSlug: string,
  prompt: string | null,
  idempotencyKey: string,
): {
  preset_slug: string
  input_asset_id: string
  prompt: string | null
  idempotency_key: string
} {
  const trimmed = prompt?.trim() ?? ""
  return {
    preset_slug: presetSlug,
    input_asset_id: input.assetId,
    prompt: trimmed === "" ? null : trimmed,
    idempotency_key: idempotencyKey,
  }
}
