import { createVideoCopy } from "./createVideoCopy"

type StatusStepsProps = {
  current: "queued" | "generating" | "done"
}

const steps: { key: StatusStepsProps["current"]; label: string }[] = [
  { key: "queued", label: createVideoCopy.status.queued },
  { key: "generating", label: createVideoCopy.status.generating },
  { key: "done", label: createVideoCopy.status.done },
]

export function StatusSteps({ current }: StatusStepsProps) {
  return (
    <ol className="flex flex-wrap items-center justify-center gap-2">
      {steps.map((step) => {
        const isCurrent = step.key === current
        const classes = isCurrent
          ? "bg-accent text-accent-ink"
          : "border border-border text-muted"
        return (
          <li
            key={step.key}
            aria-current={isCurrent ? "step" : undefined}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${classes}`}
          >
            {step.label}
          </li>
        )
      })}
    </ol>
  )
}
