import { Button } from "../../ui/Button"
import { createVideoCopy } from "./createVideoCopy"
import type { Job } from "./createVideoTypes"

type FailureViewProps = {
  variant: "failed" | "missing"
  job: Job | null
  onRetry: () => void
  onMakeAnother: () => void
  onDismissMissing: () => void
}

function FailureBody({ job }: { job: Job | null }) {
  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <p className="text-sm text-red-400">
        {createVideoCopy.failure.refunded(job?.credit_cost ?? 0)}
      </p>
      {job?.error_message != null && (
        <p className="text-xs text-muted">{job.error_message}</p>
      )}
    </div>
  )
}

export function FailureView({
  variant,
  job,
  onRetry,
  onMakeAnother,
  onDismissMissing,
}: FailureViewProps) {
  if (variant === "missing") {
    return (
      <div className="flex flex-col items-center gap-4">
        <p className="text-center text-sm text-muted">{createVideoCopy.failure.missingBody}</p>
        <Button variant="secondary" onClick={onDismissMissing}>
          {createVideoCopy.failure.backToCreate}
        </Button>
      </div>
    )
  }
  return (
    <div className="flex flex-col items-center gap-4">
      <FailureBody job={job} />
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button onClick={onRetry}>{createVideoCopy.toast.retry}</Button>
        <Button variant="secondary" onClick={onMakeAnother}>
          {createVideoCopy.result.makeAnother}
        </Button>
      </div>
    </div>
  )
}
