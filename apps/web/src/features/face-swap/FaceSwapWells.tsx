import { faceSwapCopy } from "./faceSwapCopy"
import { ImageWell } from "./ImageWell"
import type { WellControls } from "./faceSwapTypes"
import type { useHeldSeed } from "./useHeldSeed"

type FaceSwapWellsProps = {
  faceUpload: WellControls
  targetUpload: WellControls
  heldTarget: ReturnType<typeof useHeldSeed>
}

export function FaceSwapWells({ faceUpload, targetUpload, heldTarget }: FaceSwapWellsProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row">
      <ImageWell
        label={faceSwapCopy.face.label}
        hint={faceSwapCopy.face.hint}
        seedUrl={null}
        onDropSeed={() => undefined}
        upload={faceUpload}
      />
      <div className="flex-1">
        <ImageWell
          label={faceSwapCopy.target.label}
          hint={faceSwapCopy.target.hint}
          seedUrl={heldTarget.active !== null ? heldTarget.active.url : null}
          onDropSeed={heldTarget.drop}
          upload={targetUpload}
        />
        {heldTarget.active === null && (
          <p className="mt-1 text-xs text-muted">{faceSwapCopy.target.seedHint}</p>
        )}
      </div>
    </div>
  )
}
