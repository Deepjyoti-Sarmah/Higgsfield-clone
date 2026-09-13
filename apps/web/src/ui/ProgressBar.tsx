type ProgressBarProps = {
  value: number | null
  label: string
}

export function ProgressBar({ value, label }: ProgressBarProps) {
  const isDeterminate = value !== null
  const percent = value === null ? 0 : Math.round(Math.min(1, Math.max(0, value)) * 100)

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={isDeterminate ? percent : undefined}
      className="h-1.5 w-full overflow-hidden rounded-full bg-border"
    >
      {isDeterminate ? (
        <div className="h-full rounded-full bg-accent" style={{ width: `${percent}%` }} />
      ) : (
        <div className="h-full w-1/3 rounded-full bg-accent motion-safe:animate-hf-progress" />
      )}
    </div>
  )
}
