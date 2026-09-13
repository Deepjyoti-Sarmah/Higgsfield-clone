import { Link } from "react-router-dom"
import type { ToolCard as ToolCardData } from "./toolCards"

export function ToolCard({ label, to, tag }: ToolCardData) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <span className="font-semibold text-text">{label}</span>
      <span>{tag}</span>
    </Link>
  )
}
