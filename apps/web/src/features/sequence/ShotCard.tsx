import type { LibraryItem } from "../../api/library"
import type { SequenceDraftClip, SequenceDraftControls } from "../../api/studioContracts"
import { formatSecondsShort } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"
import { TrimControls } from "./TrimControls"

type ShotCardProps = {
  index: number
  total: number
  clip: SequenceDraftClip
  item: LibraryItem | null
  sequence: SequenceDraftControls
  onFaceSwap?: (item: LibraryItem) => void
}

const CHROME = "absolute h-6 rounded bg-surface/90 font-mono text-xs text-text hover:text-accent"

function FrameButton({ label, className, disabled, onClick, children }: {
  label: string
  className: string
  disabled?: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button type="button" aria-label={label} disabled={disabled} onClick={onClick} className={className}>
      {children}
    </button>
  )
}

function MoveButtons({ index, total, sequence }: { index: number; total: number; sequence: SequenceDraftControls }) {
  const position = index + 1
  const classes = `${CHROME} bottom-1 w-6 disabled:opacity-40`
  return (
    <>
      <FrameButton label={sequenceCopy.strip.moveLeft(position)} disabled={index === 0}
        onClick={() => sequence.moveClip(index, index - 1)} className={`${classes} left-1`}>←</FrameButton>
      <FrameButton label={sequenceCopy.strip.moveRight(position)} disabled={index === total - 1}
        onClick={() => sequence.moveClip(index, index + 1)} className={`${classes} right-1`}>→</FrameButton>
    </>
  )
}

function FaceSwapButton({ position, item, onFaceSwap }: {
  position: number
  item: LibraryItem | null
  onFaceSwap?: (item: LibraryItem) => void
}) {
  if (item === null || onFaceSwap === undefined) return null
  return (
    <FrameButton
      label={sequenceCopy.strip.faceSwap(position)}
      onClick={() => onFaceSwap(item)}
      className={`${CHROME} right-1 top-1 px-1.5 text-[10px]`}
    >
      Swap
    </FrameButton>
  )
}

function shotCaption(index: number, total: number, trimmedMs: number, isSwapped: boolean): string {
  const parts = [sequenceCopy.strip.shotLabel(index + 1, total), formatSecondsShort(trimmedMs)]
  if (isSwapped) parts.push(sequenceCopy.strip.swapped)
  return parts.join(" · ")
}

export function ShotCard({ index, total, clip, item, sequence, onFaceSwap }: ShotCardProps) {
  const trimmedMs = clip.trimEndMs - clip.trimStartMs
  const isSwapped = item?.kind === "video_faceswap"
  return (
    <div className="flex shrink-0 flex-col items-center gap-1">
      <p className="font-mono text-[10px] text-muted">{shotCaption(index, total, trimmedMs, isSwapped)}</p>
      <div className="relative rounded-lg border border-border bg-sunken">
        {clip.posterUrl ? (
          <img src={clip.posterUrl} alt="" className="h-[84px] w-[150px] rounded-lg object-cover" />
        ) : (
          <div className="flex h-[84px] w-[150px] items-center justify-center font-mono text-xs text-faint">
            {index + 1}
          </div>
        )}
        <MoveButtons index={index} total={total} sequence={sequence} />
        <FaceSwapButton position={index + 1} item={item} onFaceSwap={onFaceSwap} />
        <FrameButton
          label={sequenceCopy.strip.removeShot(index + 1)}
          onClick={() => sequence.removeClip(index)}
          className={`${CHROME} left-1 top-1 w-6`}
        >
          ×
        </FrameButton>
      </div>
      <TrimControls index={index} clip={clip} sequence={sequence} />
    </div>
  )
}
