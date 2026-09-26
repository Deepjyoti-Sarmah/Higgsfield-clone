import type { RunWithGuestSession } from "../../api/guestSession"
import type { FaceSwapSeed } from "../../api/studioContracts"
import { submitBlockedReason, wellInput } from "./faceSwapTypes"
import { useHeldSeed } from "./useHeldSeed"
import { useImageWell } from "./useImageWell"
import { useSeedConsumedEffect } from "./useSeedConsumedEffect"

// Both wells, the held target seed, and the derived blocked reason for the submit button.
export function useFaceSwapWells(
  run: RunWithGuestSession,
  seedTarget: FaceSwapSeed | null,
  onSeedConsumed: () => void,
) {
  const faceUpload = useImageWell(run)
  const targetUpload = useImageWell(run)
  const heldTarget = useHeldSeed(seedTarget)
  useSeedConsumedEffect(heldTarget.active, onSeedConsumed)

  const face = wellInput(null, null, faceUpload.state)
  const target = wellInput(heldTarget.active?.assetId ?? null, heldTarget.active?.url ?? null, targetUpload.state)
  const isUploading = faceUpload.state.status === "uploading" || targetUpload.state.status === "uploading"
  const blocked = submitBlockedReason(face, target, isUploading)

  return { faceUpload, targetUpload, heldTarget, face, target, blocked }
}
