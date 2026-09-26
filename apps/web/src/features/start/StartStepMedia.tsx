import { useState } from "react"
import type { ShowcaseMedia } from "../../api/webMedia"
import type { StepTool } from "./startCopy"
import { TOOL_DEMOS } from "./toolDemos"

function ToolMedia({ media, alt }: { media: ShowcaseMedia; alt: string }) {
  const [failed, setFailed] = useState(false)
  if (failed) return null
  const mediaClasses = "h-36 w-full rounded-lg border border-border object-cover sm:h-44"
  if (media.kind === "still") {
    return (
      <img src={media.url} alt={alt} onError={() => setFailed(true)} className={mediaClasses} />
    )
  }
  return (
    <video
      src={media.url}
      poster={media.poster ?? undefined}
      muted
      loop
      playsInline
      autoPlay
      preload="metadata"
      onError={() => setFailed(true)}
      className={mediaClasses}
    />
  )
}

export function ToolStepMedia({ tool }: { tool: StepTool }) {
  const demo = TOOL_DEMOS[tool]
  return <ToolMedia media={demo.media} alt={demo.alt} />
}
