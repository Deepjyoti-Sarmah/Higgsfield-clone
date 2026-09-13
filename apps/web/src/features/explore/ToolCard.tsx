import { Link } from "react-router-dom"
import type { ToolCard as ToolCardData } from "./toolCards"

export function ToolCard({ label, description, to }: ToolCardData) {
  return (
    <Link
      to={to}
      className="flex h-full flex-col gap-1.5 rounded-2xl border border-border bg-surface p-4 transition-colors hover:border-accent/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <span className="text-sm font-semibold text-text">{label}</span>
      <span className="text-xs text-muted">{description}</span>
    </Link>
  )
}
