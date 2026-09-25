import type { Preset } from "../../api/presets"
import { previewPosterUrl } from "../../api/webMedia"
import { SHOWCASE_STILLS } from "../../api/webMedia"

export function StillStepMedia() {
  const still = SHOWCASE_STILLS[0]
  return (
    <img
      src={still.url}
      alt={still.title}
      className="h-36 w-full rounded-lg border border-border object-cover sm:h-44"
    />
  )
}

export function ClipStepMedia({ preset }: { preset: Preset | null }) {
  const previewUrl = preset?.preview_url ?? null
  const posterUrl = previewUrl === null ? null : previewPosterUrl(previewUrl)
  if (previewUrl === null) {
    return (
      <img
        src={SHOWCASE_STILLS[1].url}
        alt=""
        className="h-36 w-full rounded-lg border border-border object-cover sm:h-44"
      />
    )
  }
  return (
    <video
      src={previewUrl}
      poster={posterUrl ?? undefined}
      muted
      loop
      playsInline
      autoPlay
      preload="metadata"
      className="h-36 w-full rounded-lg border border-border object-cover motion-safe:sm:h-44"
    />
  )
}

export function SequenceStepMedia() {
  return (
    <div className="flex items-center gap-2">
      <img
        src={SHOWCASE_STILLS[2].url}
        alt=""
        className="h-20 w-32 rounded-lg border border-border object-cover"
      />
      <span className="rounded-full border border-border bg-surface px-2 py-0.5 font-mono text-[10px] tracking-wide text-muted">
        XFADE
      </span>
      <img
        src={SHOWCASE_STILLS[3].url}
        alt=""
        className="h-20 w-32 rounded-lg border border-border object-cover"
      />
    </div>
  )
}
