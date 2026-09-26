import { useCallback, useState } from "react"
import { useOutletContext } from "react-router-dom"
import { useGuestSessionRunner } from "../../api/guestSession"
import type { ImageInsufficient } from "../../api/imageJobs"
import { useImageOptions } from "../../api/imageOptions"
import { useCreditsPopover } from "../../ui/useCreditsPopover"
import type { SessionContextValue } from "../session/useSession"
import { imageCreateCopy } from "./imageCreateCopy"
import { imageCost } from "./imageSettings"
import { ImageSettingsRow } from "./ImageSettingsRow"
import { StillPromptField } from "./StillPromptField"
import { useStillSettings } from "./useStillSettings"
import { useStillSubmit } from "./useStillSubmit"

type StillComposerProps = {
  onJobStarted: (jobId: string) => void
}

const BLOCKED_LINES = {
  "no-prompt": imageCreateCopy.generate.blockedNoPrompt,
  "options-unavailable": imageCreateCopy.generate.optionsUnavailable,
} as const

function ErrorLines(props: {
  insufficient: ImageInsufficient | null
  failure: "limit" | "error" | null
}) {
  if (props.insufficient !== null) {
    return (
      <p role="alert" className="text-[13px] text-danger">
        {imageCreateCopy.generate.insufficient(props.insufficient.balance, props.insufficient.required)}
      </p>
    )
  }
  if (props.failure === null) return null
  return (
    <p role="alert" className="text-[13px] text-danger">
      {props.failure === "limit" ? imageCreateCopy.generate.limitHit : imageCreateCopy.generate.network}
    </p>
  )
}
export function StillComposer({ onJobStarted }: StillComposerProps) {
  const session = useOutletContext<SessionContextValue>()
  const run = useGuestSessionRunner(session)
  const optionsState = useImageOptions()
  const { openCredits } = useCreditsPopover()
  const settingsState = useStillSettings()
  const submitState = useStillSubmit(run, onJobStarted, openCredits)
  const [prompt, setPrompt] = useState("")

  const options = optionsState.options
  const blocked: "no-prompt" | "options-unavailable" | null =
    options === null ? "options-unavailable" : prompt.trim() === "" ? "no-prompt" : null
  const cost = options === null ? 0 : imageCost(options, settingsState.settings)

  const handleSubmit = useCallback(() => {
    if (options === null) return
    submitState.submit(prompt, settingsState.settings)
  }, [options, prompt, settingsState.settings, submitState])

  return (
    <div className="flex flex-col gap-5 px-4 py-5 sm:px-6">
      <StillPromptField prompt={prompt} onPromptChange={setPrompt} />
      {options !== null && <ImageSettingsRow options={options} />}
      <StillActions
        cost={cost}
        blocked={blocked}
        isBlocked={blocked !== null}
        isSubmitting={submitState.isSubmitting}
        insufficient={submitState.insufficient}
        failure={submitState.failure}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

function StillActions(props: {
  cost: number
  blocked: keyof typeof BLOCKED_LINES | null
  isBlocked: boolean
  isSubmitting: boolean
  insufficient: ImageInsufficient | null
  failure: "limit" | "error" | null
  onSubmit: () => void
}) {
  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={props.onSubmit}
        disabled={props.isBlocked || props.isSubmitting}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-[10px] bg-accent px-4 text-sm font-medium text-accent-ink transition-all duration-150 hover:bg-accent/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100"
      >
        {props.isSubmitting
          ? imageCreateCopy.generate.submitting
          : imageCreateCopy.generate.withCost(props.cost)}
      </button>
      {props.blocked !== null && (
        <p className="text-[13px] text-faint">{BLOCKED_LINES[props.blocked]}</p>
      )}
      <ErrorLines insufficient={props.insufficient} failure={props.failure} />
    </div>
  )
}
