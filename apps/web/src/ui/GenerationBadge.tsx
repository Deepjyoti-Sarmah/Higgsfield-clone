type GenerationBadgeKind = "video" | "image"

type GenerationBadgeProps = {
  generatedBy: string | null | undefined
  kind?: GenerationBadgeKind
}

const AI_BACKENDS = new Set(["modal", "openrouter"])

function labelFor(generatedBy: string, kind: GenerationBadgeKind): string | null {
  if (AI_BACKENDS.has(generatedBy)) return kind === "image" ? "AI image" : "AI video"
  if (generatedBy === "local-motion") return "Motion preview"
  if (generatedBy === "placeholder") return "Placeholder image"
  if (generatedBy === "mock") return "Mock"
  return null
}

export function GenerationBadge({ generatedBy, kind = "video" }: GenerationBadgeProps) {
  if (generatedBy === null || generatedBy === undefined) return null
  const label = labelFor(generatedBy, kind)
  if (label === null) return null
  const classes = AI_BACKENDS.has(generatedBy)
    ? "border-accent/50 bg-accent/10 text-accent"
    : "border-border bg-surface text-muted"
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${classes}`}
    >
      {label}
    </span>
  )
}
