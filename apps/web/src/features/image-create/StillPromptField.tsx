import { imageCreateCopy } from "./imageCreateCopy"

const MAX_PROMPT_LENGTH = 500

type StillPromptFieldProps = {
  prompt: string
  onPromptChange: (value: string) => void
}

export function StillPromptField({ prompt, onPromptChange }: StillPromptFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-2">
        <label htmlFor="still-prompt" className="text-sm text-muted">
          {imageCreateCopy.prompt.label}
        </label>
        <span className="text-xs text-muted">
          {imageCreateCopy.prompt.counter(prompt.length)}
        </span>
      </div>
      <textarea
        id="still-prompt"
        value={prompt}
        maxLength={MAX_PROMPT_LENGTH}
        rows={3}
        placeholder={imageCreateCopy.prompt.placeholder}
        onChange={(event) => onPromptChange(event.target.value)}
        className="w-full resize-y rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
    </div>
  )
}
