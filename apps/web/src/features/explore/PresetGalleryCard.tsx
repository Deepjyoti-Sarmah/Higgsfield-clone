import { Link } from "react-router-dom"
import type { Preset } from "../../api/presets"
import { exploreCopy } from "./exploreCopy"
import { recreateHref } from "./recreateHref"

type PresetGalleryCardProps = {
  preset: Preset
}

function PreviewMedia({ preset }: PresetGalleryCardProps) {
  const mediaUrl = preset.preview_url
  const isVideo =
    mediaUrl !== null &&
    (mediaUrl.endsWith(".mp4") || mediaUrl.endsWith(".webm") || mediaUrl.includes(".mp4"))
  if (isVideo && mediaUrl !== null) {
    return (
      <video
        src={mediaUrl}
        autoPlay
        loop
        muted
        playsInline
        aria-hidden="true"
        onMouseEnter={(e) => void e.currentTarget.play()}
        onMouseLeave={(e) => e.currentTarget.pause()}
        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
      />
    )
  }
  if (mediaUrl === null) {
    return (
      <span
        aria-hidden="true"
        className="block h-full w-full bg-gradient-to-br from-border to-bg"
      />
    )
  }
  return (
    <img
      src={mediaUrl}
      alt={exploreCopy.gallery.previewAlt(preset.name)}
      loading="lazy"
      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100"
    />
  )
}

export function PresetGalleryCard({ preset }: PresetGalleryCardProps) {
  const { cardCta, categoryLabel, creditCost, recreateAriaLabel } = exploreCopy.gallery

  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-surface p-4 transition-all duration-300 hover:-translate-y-1 hover:border-accent/70 hover:shadow-xl hover:shadow-black/50 focus-within:border-accent/70">
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl border border-border">
        <PreviewMedia preset={preset} />
        <span aria-hidden="true" className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/80 to-transparent" />
        <span className="absolute left-2.5 top-2.5 rounded-full bg-black/60 px-2.5 py-0.5 text-[11px] font-medium text-accent backdrop-blur border border-accent/20">
          {creditCost(preset.credit_cost)}
        </span>
      </div>
      <div className="mt-3 flex flex-col gap-1">
        <h3 className="text-base text-text">{preset.name}</h3>
        <p className="text-xs text-muted">{categoryLabel(preset.category)}</p>
      </div>
      <Link
        to={recreateHref(preset.slug)}
        aria-label={recreateAriaLabel(preset.name)}
        className="mt-3 inline-flex items-center justify-center gap-1.5 rounded-full bg-accent px-4 py-2 text-xs font-bold uppercase tracking-wide text-accent-ink shadow-lg shadow-accent/20 transition-all hover:bg-accent/90 hover:scale-[1.02] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <span aria-hidden="true">✦</span> {cardCta}
      </Link>
    </article>
  )
}
