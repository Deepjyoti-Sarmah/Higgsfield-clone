import { useState } from "react"
import type { DragEvent as ReactDragEvent } from "react"
import type { SequenceDraftClip, SequenceDraftControls } from "../../api/studioContracts"
import { formatSecondsShort } from "./sequenceDraftView"
import { sequenceCopy } from "./sequenceCopy"
import { TransitionChip } from "./TransitionChip"
import { TrimControls } from "./TrimControls"

type SequenceStripProps = {
  sequence: SequenceDraftControls
}

type SlotChromeProps = {
  index: number
  jobId: string
  sequence: SequenceDraftControls
  children: React.ReactNode
}

function SlotChrome({ index, jobId, sequence, children }: SlotChromeProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const readIndex = (event: ReactDragEvent) => Number(event.dataTransfer.getData("text/plain"))
  const frameClasses = `relative shrink-0 rounded-lg border bg-sunken ${
    isDragOver ? "border-accent" : "border-border"
  }`
  return (
    <div
      draggable
      onDragStart={(event) => event.dataTransfer.setData("text/plain", String(index))}
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(event) => {
        event.preventDefault()
        setIsDragOver(false)
        const from = readIndex(event)
        if (!Number.isNaN(from)) sequence.moveClip(from, index)
      }}
      className={frameClasses}
    >
      {children}
      <SlotControls index={index} sequence={sequence} />
      <RemoveButton index={index} jobId={jobId} sequence={sequence} />
    </div>
  )
}

function SlotControls({ index, sequence }: { index: number; sequence: SequenceDraftControls }) {
  const position = index + 1
  return (
    <div className="absolute inset-x-0 bottom-0 flex justify-between p-1">
      <button
        type="button"
        aria-label={sequenceCopy.strip.moveLeft(position)}
        disabled={index === 0}
        onClick={() => sequence.moveClip(index, index - 1)}
        className="h-6 w-6 rounded bg-surface/90 font-mono text-xs text-text disabled:opacity-40"
      >
        ←
      </button>
      <button
        type="button"
        aria-label={sequenceCopy.strip.moveRight(position)}
        onClick={() => sequence.moveClip(index, index + 1)}
        className="h-6 w-6 rounded bg-surface/90 font-mono text-xs text-text"
      >
        →
      </button>
    </div>
  )
}

function RemoveButton({ index, jobId, sequence }: {
  index: number
  jobId: string
  sequence: SequenceDraftControls
}) {
  return (
    <button
      type="button"
      aria-label={sequenceCopy.strip.removeShot(index + 1)}
      onClick={() => sequence.removeClip(index)}
      data-job={jobId}
      className="absolute right-1 top-1 h-6 w-6 rounded bg-surface/90 font-mono text-xs text-text hover:text-danger"
    >
      ×
    </button>
  )
}

function ClipSlot({ index, clip, total, sequence }: {
  index: number
  clip: SequenceDraftClip
  total: number
  sequence: SequenceDraftControls
}) {
  const trimmedMs = clip.trimEndMs - clip.trimStartMs
  return (
    <div className="flex flex-col items-center gap-1">
      <p className="font-mono text-[10px] text-muted">
        {sequenceCopy.strip.shotLabel(index + 1, total)} · {formatSecondsShort(trimmedMs)}
      </p>
      <SlotChrome index={index} jobId={clip.jobId} sequence={sequence}>
        {clip.posterUrl ? (
          <img src={clip.posterUrl} alt="" className="h-[68px] w-[120px] rounded-lg object-cover" />
        ) : (
          <div className="flex h-[68px] w-[120px] items-center justify-center font-mono text-xs text-faint">
            {index + 1}
          </div>
        )}
      </SlotChrome>
      <TrimControls index={index} clip={clip} sequence={sequence} />
    </div>
  )
}

function EmptySlot() {
  return (
    <div className="flex h-[68px] w-[120px] shrink-0 items-center justify-center rounded-lg border border-dashed border-border bg-sunken px-2 text-center text-[11px] leading-tight text-faint">
      {sequenceCopy.strip.emptySlot}
    </div>
  )
}

export function SequenceStrip({ sequence }: SequenceStripProps) {
  const clips = sequence.draft.clips
  const trailingEmpty = clips.length === 0 ? 2 : clips.length < 2 ? 1 : 0
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1" aria-label="Sequence strip">
      {clips.map((clip, index) => (
        <div key={`${clip.jobId}-${index}`} className="flex items-center gap-2">
          {index > 0 && (
            <TransitionChip
              position={index}
              transition={clip.transitionIn}
              onCycle={(next) => sequence.setTransition(index, next)}
            />
          )}
          <ClipSlot index={index} clip={clip} total={clips.length} sequence={sequence} />
        </div>
      ))}
      {Array.from({ length: trailingEmpty }).map((_, index) => (
        <EmptySlot key={`empty-${index}`} />
      ))}
    </div>
  )
}
