import type { ReactNode } from "react"
import { previewClipUrl, SHOWCASE_MEDIA } from "../../api/webMedia"
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
    <div className="relative flex aspect-video overflow-hidden rounded-xl border border-border">
      <img
        src="/showcase/sample-01.jpg"
        alt={createVideoCopy.howItWorks.imageAlt}
        className="h-full w-full object-cover"
      />
      <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-[1px]">
        <span aria-hidden="true" className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-lg font-bold text-accent-ink shadow-lg">
          ↑
        </span>
      </div>
    </div>
  )
}

function PreviewTile({ slug, className }: { slug: string; className: string }) {
  return (
    <video
      src={previewClipUrl(slug)}
      autoPlay
      loop
      muted
      playsInline
      aria-hidden="true"
      className={className}
    />
  )
}

function PresetIllustration() {
  return (
    <div className="flex aspect-video items-center justify-center gap-1.5 overflow-hidden rounded-xl border border-border bg-black/40 p-2">
      <PreviewTile slug={SHOWCASE_MEDIA.dollyOutSlug} className="h-full w-1/3 rounded-lg object-cover opacity-60" />
      <PreviewTile slug={SHOWCASE_MEDIA.dollyIn.slug} className="h-full w-1/3 rounded-lg border border-accent object-cover shadow-md shadow-accent/20" />
      <PreviewTile slug={SHOWCASE_MEDIA.panLeftSlug} className="h-full w-1/3 rounded-lg object-cover opacity-60" />
    </div>
  )
}

function VideoIllustration() {
  return (
    <div className="aspect-video overflow-hidden rounded-xl border border-border">
      <PreviewTile slug={SHOWCASE_MEDIA.kenBurns.slug} className="h-full w-full object-cover" />
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
