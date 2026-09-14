import { Link } from "react-router-dom"
import type { Preset } from "../../api/presets"
import { previewPosterUrl } from "../../api/webMedia"
import { exploreCopy } from "./exploreCopy"
import { presetTileStyles } from "./presetTileStyles"
import { recreateHref } from "./recreateHref"

type PresetGalleryCardProps = {
  preset: Preset
}

function PreviewMedia({ preset }: PresetGalleryCardProps) {
  const mediaUrl = preset.preview_url
  if (mediaUrl === null) {
    return (
      <span aria-hidden="true" className={`absolute inset-0 ${presetTileStyles[preset.category]}`} />
    )
  }
  const isVideo = mediaUrl.endsWith(".mp4") || mediaUrl.endsWith(".webm")
  const className =
    "absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
  if (!isVideo) {
    return <img src={mediaUrl} alt="" loading="lazy" className={className} />
  }
  return (
    <video
      src={mediaUrl}
      poster={previewPosterUrl(mediaUrl) ?? undefined}
      preload="metadata"
      autoPlay
      loop
      muted
      playsInline
      aria-hidden="true"
      className={className}
    />
  )
}

export function PresetGalleryCard({ preset }: PresetGalleryCardProps) {
  const { cardCta, categoryLabel, creditCost, recreateAriaLabel } = exploreCopy.gallery

  return (
    <Link
      to={recreateHref(preset.slug)}
      aria-label={recreateAriaLabel(preset.name)}
      className="group relative block aspect-[16/10] overflow-hidden rounded-lg border border-border bg-surface transition-colors hover:border-accent/70 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <PreviewMedia preset={preset} />
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-scrim to-transparent"
      />
      <span className="absolute left-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[10px] font-semibold text-accent backdrop-blur">
        {creditCost(preset.credit_cost)}
      </span>
      <span className="absolute inset-x-2 bottom-2 flex items-end justify-between gap-2">
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold text-text">{preset.name}</span>
          <span className="block text-[11px] text-muted">{categoryLabel(preset.category)}</span>
        </span>
        <span className="hidden shrink-0 rounded-full bg-accent px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-accent-ink group-hover:inline group-focus-visible:inline">
          {cardCta}
        </span>
      </span>
    </Link>
  )
}
