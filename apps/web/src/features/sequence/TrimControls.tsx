import type { SequenceDraftClip, SequenceDraftControls } from "../../api/studioContracts"
import { clampTrim, formatTrimRange, TRIM_STEP_MS } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"

type TrimControlsProps = {
  index: number
  clip: SequenceDraftClip
  sequence: SequenceDraftControls
}

function TrimStepButton({ glyph, label, onClick }: {
  glyph: string
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="h-5 w-5 shrink-0 rounded bg-sunken font-mono text-[10px] leading-none text-text hover:text-accent"
    >
      {glyph}
    </button>
  )
}

// Two steppers (in, out) in 0.5 s steps, clamped to stay in bounds with at least 1 s of clip left.
export function TrimControls({ index, clip, sequence }: TrimControlsProps) {
  const { trimStartMs, trimEndMs, durationMs } = clip
  const position = index + 1
  const nudge = (startDeltaMs: number, endDeltaMs: number) => {
    const next = clampTrim(durationMs, trimStartMs + startDeltaMs, trimEndMs + endDeltaMs)
    sequence.setTrim(index, next.trimStartMs, next.trimEndMs)
  }
  return (
    <div className="flex w-[120px] shrink-0 items-center justify-between gap-1 px-0.5 pt-1">
      <TrimStepButton
        glyph="−"
        label={sequenceCopy.strip.trimStartEarlier(position)}
        onClick={() => nudge(-TRIM_STEP_MS, 0)}
      />
      <span className="flex-1 text-center font-mono text-[9px] text-muted">
        {formatTrimRange(trimStartMs, trimEndMs)}
      </span>
      <TrimStepButton
        glyph="+"
        label={sequenceCopy.strip.trimStartLater(position)}
        onClick={() => nudge(TRIM_STEP_MS, 0)}
      />
      <TrimStepButton
        glyph="−"
        label={sequenceCopy.strip.trimEndEarlier(position)}
        onClick={() => nudge(0, -TRIM_STEP_MS)}
      />
      <TrimStepButton
        glyph="+"
        label={sequenceCopy.strip.trimEndLater(position)}
        onClick={() => nudge(0, TRIM_STEP_MS)}
      />
    </div>
  )
}
