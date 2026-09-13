import type { Preset } from "./createVideoTypes"
import { presetMotionClass } from "./presetMotionHints"

type PresetCardProps = {
  preset: Preset
  isSelected: boolean
  previewImageUrl: string | null
  onSelect: (slug: string) => void
}

function CheckBadge() {
  return (
    <span className="absolute right-1.5 top-1.5 z-10 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-ink">
      ✓
    </span>
  )
}

function PreviewMedia({
  src,
  motionClasses,
}: {
  src: string
  motionClasses: string
}) {
  return (
    <img src={src} alt="" className={`h-full w-full object-cover ${motionClasses}`} />
  )
}

export function PresetCard({
  preset,
  isSelected,
  previewImageUrl,
  onSelect,
}: PresetCardProps) {
  const motionClasses = presetMotionClass(preset.slug)
  const tileClasses = isSelected ? "border-accent" : "border-transparent"
  return (
    <label className="group block cursor-pointer">
      <span
        className={`relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border-2 bg-gradient-to-br from-border to-bg ${tileClasses} group-has-[:focus-visible]:outline-2 group-has-[:focus-visible]:outline-offset-2 group-has-[:focus-visible]:outline-accent`}
      >
        <input
          type="radio"
          name="preset"
          value={preset.slug}
          checked={isSelected}
          onChange={() => onSelect(preset.slug)}
          className="sr-only"
        />
        {previewImageUrl !== null && <PreviewMedia src={previewImageUrl} motionClasses={motionClasses} />}
        {isSelected && <CheckBadge />}
      </span>
      <span className="mt-1.5 block line-clamp-2 text-xs font-semibold text-text">
        {preset.name}
      </span>
    </label>
  )
}
