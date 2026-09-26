import { faceSwapCopy } from "./faceSwapCopy"
import type { FaceSwapInsufficient } from "../../api/faceswapJobs"
import type { SubmitBlockedReason } from "./faceSwapTypes"

type FaceSwapActionsProps = {
  cost: number
  blocked: SubmitBlockedReason | null
  isSubmitting: boolean
  insufficient: FaceSwapInsufficient | null
  failure: "limit" | "invalid" | "error" | null
  onSubmit: () => void
}

function blockedMessage(blocked: SubmitBlockedReason | null): string | null {
  if (blocked === "no-face") return faceSwapCopy.submit.blockedNoFace
  if (blocked === "no-target") return faceSwapCopy.submit.blockedNoTarget
  if (blocked === "uploading") return faceSwapCopy.submit.blockedUploading
  return null
}

function failureMessage(failure: "limit" | "invalid" | "error" | null): string | null {
  if (failure === "limit") return faceSwapCopy.submit.limitHit
  if (failure === "invalid") return faceSwapCopy.submit.invalid
  if (failure === "error") return faceSwapCopy.submit.networkToast
  return null
}

export function FaceSwapActions(props: FaceSwapActionsProps) {
  const label = props.isSubmitting ? faceSwapCopy.submit.submitting : faceSwapCopy.submit.withCost(props.cost)
  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={props.onSubmit}
        disabled={props.blocked !== null || props.isSubmitting}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-[10px] bg-accent px-4 font-mono text-sm font-medium text-accent-ink transition-all duration-150 hover:bg-accent/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
      >
        {label}
      </button>
      {blockedMessage(props.blocked) !== null && (
        <p className="text-[13px] text-faint">{blockedMessage(props.blocked)}</p>
      )}
      {props.insufficient !== null && (
        <p role="alert" className="text-[13px] text-danger">
          {faceSwapCopy.submit.insufficient(props.insufficient.balance, props.insufficient.required)}
        </p>
      )}
      {props.insufficient === null && failureMessage(props.failure) !== null && (
        <p role="alert" className="text-[13px] text-danger">
          {failureMessage(props.failure)}
        </p>
      )}
    </div>
  )
}
