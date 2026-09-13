import { Button } from "./Button"

type ToastProps = {
  message: string
  actionLabel?: string
  onAction?: () => void
  onDismiss: () => void
}

export function Toast({ message, actionLabel, onAction, onDismiss }: ToastProps) {
  return (
    <div
      role="alert"
      className="fixed bottom-4 right-4 z-50 flex max-w-sm items-center gap-3 rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text shadow-lg"
    >
      <span>{message}</span>
      {actionLabel && onAction && (
        <Button variant="secondary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
      <button
        type="button"
        aria-label="Dismiss"
        onClick={onDismiss}
        className="text-muted transition-colors hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        ×
      </button>
    </div>
  )
}
