import { Link } from "react-router-dom"
import type { Preset } from "../../api/presets"
import { previewPosterUrl } from "../../api/webMedia"
import { exploreCopy } from "./exploreCopy"
import { presetTileStyles } from "./presetTileStyles"
import { recreateHref } from "./recreateHref"

type PresetGalleryCardProps = {
  preset: Preset
  aspect: string
}

function stemEndsWithVideo(mediaUrl: string): boolean {
  // Presigned URLs carry a query string, so detect the type from the path stem.
  const stem = mediaUrl.split("?")[0]
  return stem.endsWith(".mp4") || stem.endsWith(".webm")
}

function PreviewMedia({ preset }: { preset: Preset }) {
  const mediaUrl = preset.preview_url
  if (mediaUrl === null) {
    return (
      <span aria-hidden="true" className={`absolute inset-0 ${presetTileStyles[preset.category]}`} />
    )
  }
  const isVideo = stemEndsWithVideo(mediaUrl)
  const className = "absolute inset-0 h-full w-full object-cover"
  if (!isVideo) {
    return <img src={mediaUrl} alt="" loading="lazy" className={className} />
  }
  // A presigned query signs one key only, so it cannot be reused for the poster.
  const poster = mediaUrl.includes("?")
    ? undefined
    : (previewPosterUrl(mediaUrl) ?? undefined)
  return (
    <video
      src={mediaUrl}
      poster={poster}
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

export function PresetGalleryCard({ preset, aspect }: PresetGalleryCardProps) {
  const { cardCta, creditCost, recreateAriaLabel } = exploreCopy.gallery

  return (
    <Link
      to={recreateHref(preset.slug)}
      aria-label={recreateAriaLabel(preset.name)}
      className={`group relative block overflow-hidden rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${aspect}`}
    >
      <PreviewMedia preset={preset} />
      <span
        aria-hidden="true"
        className="preset-overlay absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/55 p-3 text-center opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        <span className="font-display text-xl uppercase leading-tight text-white">
          {preset.name}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-accent px-3 py-1 text-xs font-bold text-accent-ink">
          <span aria-hidden="true">✦</span> {cardCta}
        </span>
        <span className="text-xs text-white/70">{creditCost(preset.credit_cost)}</span>
      </span>
    </Link>
  )
}
