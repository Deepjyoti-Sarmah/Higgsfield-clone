import type { ReactNode } from "react"
import { createVideoCopy } from "./createVideoCopy"

export type HowItWorksStepState = "todo" | "current" | "busy" | "done"
export type StepIllustration = "image" | "preset" | "video"

type HowItWorksStepProps = {
  index: 1 | 2 | 3
  title: string
  body: string
  state: HowItWorksStepState
  illustration: StepIllustration
}

function ImageIllustration() {
  return (
    <div className="flex aspect-video items-center justify-center rounded-xl border-2 border-dashed border-border text-muted">
      <span aria-hidden="true" className="text-xl">
        ↑
      </span>
    </div>
  )
}

function PresetIllustration() {
  return (
    <div className="flex aspect-video items-center justify-center gap-1">
      <span className="h-8 w-6 rounded bg-border" />
      <span className="h-11 w-8 rounded border-2 border-accent bg-border" />
      <span className="h-8 w-6 rounded bg-border" />
    </div>
  )
}

function VideoIllustration() {
  return (
    <div className="aspect-video overflow-hidden rounded-xl border border-border">
      <div className="h-full w-full bg-gradient-to-br from-accent/40 to-bg motion-safe:animate-hf-motion-zoom-in" />
    </div>
  )
}

const illustrations: Record<StepIllustration, ReactNode> = {
  image: <ImageIllustration />,
  preset: <PresetIllustration />,
  video: <VideoIllustration />,
}

function StepBadge({ state }: { state: HowItWorksStepState }) {
  if (state === "done") {
    return (
      <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-semibold text-accent-ink">
        {createVideoCopy.howItWorks.badgeDone}
      </span>
    )
  }
  if (state === "busy") {
    return (
      <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted">
        {createVideoCopy.howItWorks.badgeUploading}
      </span>
    )
  }
  return null
}

export function HowItWorksStep({
  index,
  title,
  body,
  state,
  illustration,
}: HowItWorksStepProps) {
  const border = state === "current" ? "border-accent" : "border-border"
  return (
    <li className={`flex flex-col gap-3 rounded-2xl border p-3 ${border}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-muted">{index}</span>
        <StepBadge state={state} />
      </div>
      {illustrations[illustration]}
      <div>
        <p className="text-sm font-semibold text-text">{title}</p>
        <p className="text-xs text-muted">{body}</p>
      </div>
    </li>
  )
}
