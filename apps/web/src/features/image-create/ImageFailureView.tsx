import { Button } from "../../ui/Button"
import { imageCreateCopy } from "./imageCreateCopy"

type ImageFailureViewProps = {
  isMissing: boolean
  onRetry: () => void
  onMakeAnother: () => void
}

export function ImageFailureView({ isMissing, onRetry, onMakeAnother }: ImageFailureViewProps) {
  const copy = imageCreateCopy
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-4 rounded-2xl border border-border bg-surface px-8 py-16 text-center"
    >
      <h2 className="text-2xl text-text">
        {isMissing ? copy.failure.missing : copy.failure.title}
      </h2>
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button onClick={onRetry}>{copy.failure.retry}</Button>
        <Button variant="secondary" onClick={onMakeAnother}>
          {copy.result.makeAnother}
        </Button>
      </div>
    </div>
  )
}
