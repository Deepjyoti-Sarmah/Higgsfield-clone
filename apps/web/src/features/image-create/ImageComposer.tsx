import type { ImageOptionsState } from "../../api/imageOptions"
import { Button } from "../../ui/Button"
import { ButtonLink } from "../../ui/ButtonLink"
import { imageCreateCopy } from "./imageCreateCopy"
import type { ImageBalance, ImageGenerateProps, ImageSettingsControls } from "./imageCreateTypes"
import { ImageSettingsRow } from "./ImageSettingsRow"

type ImageComposerProps = {
  options: ImageOptionsState
  settings: ImageSettingsControls
  prompt: string
  onPromptChange: (value: string) => void
  generate: ImageGenerateProps
}

const MAX_PROMPT_LENGTH = 500

function generateLabel(generate: ImageGenerateProps): string {
  if (generate.isSubmitting) return imageCreateCopy.generate.submitting
  return imageCreateCopy.generate.withCost(generate.cost)
}

function blockedText(reason: ImageGenerateProps["blockedReason"]): string | null {
  if (reason === "no-prompt") return imageCreateCopy.generate.blockedNoPrompt
  if (reason === "options-unavailable") return imageCreateCopy.states.optionsError.title
  return null
}

function balanceText(balance: ImageBalance): string {
  if (balance.status === "known" && balance.balance !== null) {
    return imageCreateCopy.generate.balanceKnown(balance.balance)
  }
  if (balance.status === "error") return imageCreateCopy.generate.balanceError
  return imageCreateCopy.generate.balanceLoading
}

function submitErrorText(kind: NonNullable<ImageGenerateProps["submitError"]>): string {
  if (kind === "session") return imageCreateCopy.generate.sessionError
  return imageCreateCopy.states.optionsError.body
}

function PromptField({
  prompt,
  onPromptChange,
}: {
  prompt: string
  onPromptChange: (value: string) => void
}) {
  const copy = imageCreateCopy
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="image-prompt" className="text-sm text-muted">
        {copy.prompt.label}
      </label>
      <textarea
        id="image-prompt"
        value={prompt}
        maxLength={MAX_PROMPT_LENGTH}
        placeholder={copy.prompt.placeholder}
        onChange={(event) => onPromptChange(event.target.value)}
        className="min-h-24 rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text"
      />
      <p className="self-end text-xs text-muted">{copy.prompt.counter(prompt.length)}</p>
    </div>
  )
}

function GenerateSection({ generate }: { generate: ImageGenerateProps }) {
  const copy = imageCreateCopy
  const blocked = blockedText(generate.blockedReason)
  return (
    <div className="flex flex-col items-start gap-2">
      <Button
        onClick={generate.onGenerate}
        disabled={!generate.canGenerate}
        isLoading={generate.isSubmitting}
      >
        {generateLabel(generate)}
      </Button>
      <p className="text-xs text-muted">{balanceText(generate.balance)}</p>
      {blocked !== null && <p className="text-sm text-muted">{blocked}</p>}
      {generate.insufficient !== null && (
        <p className="text-sm text-red-400">
          {copy.generate.insufficient(
            generate.insufficient.balance,
            generate.insufficient.required,
          )}
        </p>
      )}
      {generate.insufficient !== null && (
        <ButtonLink to={copy.generate.getCreditsHref} variant="secondary">
          {copy.generate.getCredits}
        </ButtonLink>
      )}
      {generate.submitError !== null && (
        <p role="alert" className="text-sm text-red-400">
          {submitErrorText(generate.submitError)}
        </p>
      )}
    </div>
  )
}

export function ImageComposer({
  options,
  settings,
  prompt,
  onPromptChange,
  generate,
}: ImageComposerProps) {
  return (
    <div className="flex flex-col gap-5 rounded-2xl border border-border bg-surface px-6 py-5">
      <PromptField prompt={prompt} onPromptChange={onPromptChange} />
      {options.options !== null && (
        <ImageSettingsRow options={options.options} settings={settings} />
      )}
      <GenerateSection generate={generate} />
    </div>
  )
}
