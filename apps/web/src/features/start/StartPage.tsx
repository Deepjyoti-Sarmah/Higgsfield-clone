import { usePresets } from "../../api/presets"
import { ButtonLink } from "../../ui/ButtonLink"
import { PresetChipRow } from "./PresetChipRow"
import { StartSteps } from "./StartSteps"
import { startCopy } from "./startCopy"

export function StartPage() {
  const presetsState = usePresets()
  const clipPreset = presetsState.presets[0] ?? null

  return (
    <div className="mx-auto w-full max-w-[1200px] px-4 py-12 sm:px-6 sm:py-16 lg:py-24">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="flex flex-col items-start gap-6 lg:col-span-5">
          <h1 className="font-display text-[clamp(2.5rem,5vw,4rem)] leading-[1.05] tracking-[-0.01em] text-text">
            {startCopy.headline}
          </h1>
          <p className="max-w-[65ch] text-[0.9375rem] leading-relaxed text-muted">
            {startCopy.pitch}
          </p>
          <ButtonLink to="/studio">{startCopy.cta}</ButtonLink>
        </div>
        <div className="lg:col-span-7">
          <StartSteps clipPreset={clipPreset} />
        </div>
      </div>
      <div className="mt-12">
        <PresetChipRow presetsState={presetsState} />
      </div>
    </div>
  )
}
