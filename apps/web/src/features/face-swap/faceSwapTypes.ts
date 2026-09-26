import type { components } from "../../api/generated/schema"

export type Asset = components["schemas"]["AssetResponse"]

export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"] as const
export const MAX_IMAGE_BYTES = 10_485_760

export function checkImageFile(file: File): boolean {
  const isAcceptedType = ACCEPTED_IMAGE_TYPES.some((type) => type === file.type)
  return isAcceptedType && file.size > 0 && file.size <= MAX_IMAGE_BYTES
}

export type WellErrorKind = "network" | "session" | "not-finished"

export type WellState =
  | { status: "idle" }
  | { status: "uploading"; file: File; previewUrl: string; progress: number }
  | { status: "ready"; file: File; previewUrl: string; asset: Asset }
  | { status: "error"; file: File; previewUrl: string; errorKind: WellErrorKind }

export type WellControls = {
  state: WellState
  rejection: "invalid-file" | null
  selectImage: (file: File) => void
  clearImage: () => void
  retryUpload: () => void
}

// A well is ready either from an upload or a seed carried over from the stage.
export type WellInput = { assetId: string; previewUrl: string; fromSeed: boolean } | null

export function wellInput(seedAssetId: string | null, seedUrl: string | null, upload: WellState): WellInput {
  if (seedAssetId !== null && seedUrl !== null) {
    return { assetId: seedAssetId, previewUrl: seedUrl, fromSeed: true }
  }
  if (upload.status === "ready") {
    return { assetId: upload.asset.id, previewUrl: upload.previewUrl, fromSeed: false }
  }
  return null
}

export type SubmitBlockedReason = "no-face" | "no-target" | "uploading"

export function submitBlockedReason(
  face: WellInput,
  target: WellInput,
  isUploading: boolean,
): SubmitBlockedReason | null {
  if (face === null) return "no-face"
  if (target === null) return "no-target"
  if (isUploading) return "uploading"
  return null
}
