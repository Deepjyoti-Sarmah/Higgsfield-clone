import { useCallback } from "react"
import { useOutletContext } from "react-router-dom"
import { useGuestSessionRunner } from "../../api/guestSession"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import type { FaceSwapComposerProps } from "../../api/studioContracts"
import type { SessionContextValue } from "../session/useSession"
import { FACESWAP_CREDIT_COST } from "./faceSwapCost"
import { FaceSwapActions } from "./FaceSwapActions"
import { FaceSwapWells } from "./FaceSwapWells"
import { useFaceSwapSubmit } from "./useFaceSwapSubmit"
import { useFaceSwapWells } from "./useFaceSwapWells"

export function FaceSwapComposer({ onJobStarted, seedTarget, onSeedConsumed }: FaceSwapComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const { openCredits } = useCreditsPopover()
  const wells = useFaceSwapWells(run, seedTarget, onSeedConsumed)
  const submitState = useFaceSwapSubmit(run, onJobStarted, openCredits)

  const { face, target } = wells
  const handleSubmit = useCallback(() => {
    if (face === null || target === null) return
    submitState.submit(face.assetId, target.assetId)
  }, [face, target, submitState])

  return (
    <div className="flex flex-col gap-4 px-4 py-5 sm:px-6">
      <FaceSwapWells faceUpload={wells.faceUpload} targetUpload={wells.targetUpload} heldTarget={wells.heldTarget} />
      <FaceSwapActions
        cost={FACESWAP_CREDIT_COST}
        blocked={wells.blocked}
        isSubmitting={submitState.isSubmitting}
        insufficient={submitState.insufficient}
        failure={submitState.failure}
        onSubmit={handleSubmit}
      />
    </div>
  )
}
