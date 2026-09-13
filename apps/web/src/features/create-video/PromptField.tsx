import { createVideoCopy } from "./createVideoCopy"

type PromptFieldProps = {
  value: string
  onChange: (value: string) => void
}

export const MAX_PROMPT_LENGTH = 500

export function PromptField({ value, onChange }: PromptFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-2">
        <label
          htmlFor="create-video-prompt"
          className="text-xs font-semibold uppercase tracking-wide text-muted"
        >
          {createVideoCopy.prompt.label}
        </label>
        <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted">
          {createVideoCopy.prompt.optional}
        </span>
      </div>
      <textarea
        id="create-video-prompt"
        value={value}
        maxLength={MAX_PROMPT_LENGTH}
        rows={3}
        placeholder={createVideoCopy.prompt.placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="w-full resize-y rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text placeholder:text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
      <div className="flex items-center justify-between gap-2 text-xs text-muted">
        <span>{createVideoCopy.prompt.helper}</span>
        <span>{createVideoCopy.prompt.counter(value.length)}</span>
      </div>
    </div>
  )
}
