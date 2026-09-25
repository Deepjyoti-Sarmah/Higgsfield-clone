import type { ReactNode } from "react"

type EmptyStateProps = {
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-4 px-8 py-16 text-center">
      <h2 className="font-display text-3xl text-text">{title}</h2>
      <p className="max-w-[65ch] text-sm leading-relaxed text-muted">{description}</p>
      {action}
    </div>
  )
}
