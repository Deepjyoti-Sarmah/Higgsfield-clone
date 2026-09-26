import { useState } from "react"
import type { SeedImage } from "../../api/studioContracts"
import { clipBlockedReason, clipInputImage } from "./clipSubmit"
import type { ClipInputImage, ClipBlockedReason } from "./clipSubmit"
import type { ImageUploadControls } from "./createVideoTypes"
import type { PresetSelection } from "./createVideoTypes"

export function useClipInput(
  seedImage: SeedImage | null,
  upload: ImageUploadControls,
  selection: PresetSelection,
): {
  input: ClipInputImage | null
  blocked: ClipBlockedReason
  previewUrl: string | null
  seedDropped: boolean
  dropSeed: () => void
} {
  // The parent clears its seed once adopted, so keep our own copy until the user drops it.
  const [heldSeed, setHeldSeed] = useState<SeedImage | null>(seedImage)
  const [seedDropped, setSeedDropped] = useState(false)
  if (seedImage !== null && seedImage.assetId !== heldSeed?.assetId) {
    setHeldSeed(seedImage)
    setSeedDropped(false)
  }
  const activeSeed = seedDropped ? null : heldSeed
  const uploadAssetId = upload.state.status === "ready" ? upload.state.asset.id : null
  const previewUrl = upload.state.status === "idle" ? null : upload.state.previewUrl
  const input = clipInputImage(activeSeed, uploadAssetId, previewUrl)
  const isUploading = upload.state.status === "uploading"
  const blocked = clipBlockedReason(input, selection.selectedPreset !== null, isUploading)
  return {
    input,
    blocked,
    previewUrl,
    seedDropped,
    dropSeed: () => setSeedDropped(true),
  }
}
