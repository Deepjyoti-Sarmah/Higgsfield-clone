import type { PresetsState } from "../../api/presets"
import { ButtonLink } from "../../ui/ButtonLink"
import { exploreCopy } from "./exploreCopy"
import { PresetGalleryCard } from "./PresetGalleryCard"
import { PresetGalleryStates } from "./PresetGalleryStates"
import { TILE_ASPECTS, TILE_ASPECT_PATTERN } from "./presetTileStyles"

type PresetGalleryProps = {
  state: PresetsState
}

export function PresetGallery({ state }: PresetGalleryProps) {
  const { title, subtitle, headerCta, headerCtaHref } = exploreCopy.gallery

  return (
    <section id="effects" aria-labelledby="effects-title" className="pb-10">
      <div className="flex items-start justify-between gap-4 px-4">
        <div>
          <p id="effects-title" className="font-display text-4xl uppercase leading-none text-accent">
            {title}
          </p>
          <p className="mt-2 text-sm text-muted">{subtitle}</p>
        </div>
        <ButtonLink to={headerCtaHref} className="shrink-0">
          {headerCta}
        </ButtonLink>
      </div>
      {state.status !== "ready" && (
        <PresetGalleryStates status={state.status} onRetry={state.reloadPresets} />
      )}
      {state.status === "ready" && state.presets.length === 0 && (
        <PresetGalleryStates status="empty" onRetry={state.reloadPresets} />
      )}
      {state.status === "ready" && (
        <div className="columns-2 gap-3 px-4 pt-4 sm:columns-3 lg:columns-4 [column-fill:_balance]">
          {state.presets.map((preset, index) => (
            <div key={preset.slug} className="mb-3 break-inside-avoid">
              <PresetGalleryCard
                preset={preset}
                aspect={TILE_ASPECTS[TILE_ASPECT_PATTERN[index % TILE_ASPECT_PATTERN.length]]}
              />
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
