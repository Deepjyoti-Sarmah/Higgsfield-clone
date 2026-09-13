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
  const isVideo = src.endsWith(".mp4") || src.endsWith(".webm") || src.includes(".mp4")
  if (isVideo) {
    return (
      <video
        src={src}
        autoPlay
        loop
        muted
        playsInline
        aria-hidden="true"
        className="h-full w-full object-cover"
      />
    )
  }
  return <img src={src} alt="" className={`h-full w-full object-cover ${motionClasses}`} />
}

export function PresetCard({
  preset,
  isSelected,
  previewImageUrl,
  onSelect,
}: PresetCardProps) {
  const motionClasses = presetMotionClass(preset.slug)
  const mediaSrc = previewImageUrl ?? preset.preview_url
  const tileClasses = isSelected
    ? "border-accent shadow-lg shadow-accent/25"
    : "border-transparent hover:border-accent/50"
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
        {mediaSrc !== null && <PreviewMedia src={mediaSrc} motionClasses={motionClasses} />}
        {isSelected && <CheckBadge />}
      </span>
      <span className="mt-1.5 block line-clamp-2 text-xs font-semibold text-text">
        {preset.name}
      </span>
    </label>
  )
}
