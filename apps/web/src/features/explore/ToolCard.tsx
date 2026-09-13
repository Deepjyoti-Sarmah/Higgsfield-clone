import type { ReactNode } from "react"
import { Link } from "react-router-dom"
import type { ToolCard as ToolCardData } from "./toolCards"

function Glyph({ path }: { path: string }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="h-5 w-5 text-accent">
      <path d={path} fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const glyphs: Record<string, ReactNode> = {
  "/": <Glyph path="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z" />,
  "/create/video": <Glyph path="M4 2.5v11l9-5.5z" />,
  "/create/image": <Glyph path="M2 12l3.5-4 2.5 3 2-2.5L14 12zM2 2h12v12H2z" />,
  "/library": <Glyph path="M2 5l6-3 6 3-6 3zM2 8.5l6 3 6-3M2 12l6 3 6-3" />,
  "/credits": <Glyph path="M9 1.5L3 9h4.5L7 14.5 13 6.5H8.5z" />,
}

export function ToolCard({ label, description, to, tag }: ToolCardData) {
  return (
    <Link
      to={to}
      className="group flex h-full flex-col gap-1.5 rounded-2xl border border-border bg-surface p-4 transition-colors hover:border-accent/70 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <span className="flex items-start justify-between gap-2">
        {glyphs[to] ?? <Glyph path="M2 8h12" />}
        <span className="rounded-full border border-border px-2 py-0.5 text-[11px] font-semibold text-muted transition-colors group-hover:border-accent/50 group-hover:text-text">
          {tag}
        </span>
      </span>
      <span className="mt-2 text-sm font-semibold text-text">{label}</span>
      <span className="text-xs text-muted">{description}</span>
    </Link>
  )
}
