import { Link } from "react-router-dom"
import type { Preset } from "../../api/presets"
import { exploreCopy } from "./exploreCopy"
import { DEFAULT_TILE_CLASSES, presetTileStyles } from "./presetTileStyles"
import { recreateHref } from "./recreateHref"

type PresetGalleryCardProps = {
  preset: Preset
}

function PreviewMedia({ preset }: PresetGalleryCardProps) {
  if (preset.preview_url === null) {
    return (
      <span
        aria-hidden="true"
        className={`block h-full w-full ${presetTileStyles[preset.category] ?? DEFAULT_TILE_CLASSES}`}
      />
    )
  }
  return (
    <img
      src={preset.preview_url}
      alt={exploreCopy.gallery.previewAlt(preset.name)}
      loading="lazy"
      className="h-full w-full object-cover"
    />
  )
}

export function PresetGalleryCard({ preset }: PresetGalleryCardProps) {
  const { cardCta, categoryLabel, creditCost, recreateAriaLabel } = exploreCopy.gallery

  return (
    <article className="flex h-full flex-col gap-3 rounded-2xl border border-border bg-surface p-4">
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl border border-border">
        <PreviewMedia preset={preset} />
      </div>
      <div className="flex flex-col gap-1">
        <h3 className="text-sm font-semibold text-text">{preset.name}</h3>
        <p className="text-xs text-muted">{categoryLabel(preset.category)}</p>
        <p className="text-xs text-muted">{creditCost(preset.credit_cost)}</p>
      </div>
      <Link
        to={recreateHref(preset.slug)}
        aria-label={recreateAriaLabel(preset.name)}
        className="mt-auto inline-flex items-center justify-center rounded-full border border-border px-4 py-2 text-xs font-semibold text-text transition-colors hover:border-accent/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {cardCta}
      </Link>
    </article>
  )
}
