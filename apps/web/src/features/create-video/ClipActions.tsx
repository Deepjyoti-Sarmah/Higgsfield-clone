import type { InsufficientCredits } from "./createVideoTypes"
import { createVideoCopy } from "./createVideoCopy"

type ClipActionsProps = {
  cost: number | null
  isBlocked: boolean
  isSubmitting: boolean
  blockedMessage: string | null
  insufficient: InsufficientCredits | null
  failure: "limit" | "error" | null
  onSubmit: () => void
}

function buttonLabel(isSubmitting: boolean, cost: number | null): string {
  if (isSubmitting) return createVideoCopy.generate.submitting
  if (cost === null) return createVideoCopy.generate.label
  return createVideoCopy.generate.withCost(cost)
}

function ErrorLines(props: {
  insufficient: InsufficientCredits | null
  failure: "limit" | "error" | null
}) {
  if (props.insufficient !== null) {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {createVideoCopy.generate.insufficient(props.insufficient.balance, props.insufficient.required)}
      </p>
    )
  }
  if (props.failure === null) return null
  return (
    <p role="alert" className="text-[13px] text-danger">
      {props.failure === "limit"
        ? createVideoCopy.generate.limitHit
        : createVideoCopy.generate.networkToast}
    </p>
  )
}

export function ClipActions(props: ClipActionsProps) {
  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={props.onSubmit}
        disabled={props.isBlocked || props.isSubmitting}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-[10px] bg-accent px-4 text-sm font-medium text-accent-ink transition-all duration-150 hover:bg-accent/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
      >
        {buttonLabel(props.isSubmitting, props.cost)}
      </button>
      {props.blockedMessage !== null && (
        <p className="text-[13px] text-faint">{props.blockedMessage}</p>
      )}
      <ErrorLines insufficient={props.insufficient} failure={props.failure} />
    </div>
  )
}
