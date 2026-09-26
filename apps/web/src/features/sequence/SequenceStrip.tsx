import type { LibraryItem } from "../../api/library"
import type { SequenceDraftControls } from "../../api/studioContracts"
import { sequenceCopy } from "./sequenceCopy"
import { ShotCard } from "./ShotCard"
import { TransitionChip } from "./TransitionChip"

type SequenceStripProps = {
  sequence: SequenceDraftControls
  libraryItems: LibraryItem[]
  onFaceSwapClip?: (item: LibraryItem) => void
}

function EmptySlot() {
  return (
    <div className="flex h-[84px] w-[150px] shrink-0 items-center justify-center rounded-lg border border-dashed border-border bg-sunken px-2 text-center text-[11px] leading-tight text-faint">
      {sequenceCopy.strip.emptySlot}
    </div>
  )
}

function emptySlotCount(clipCount: number): number {
  if (clipCount === 0) return 2
  return Math.max(0, 2 - clipCount)
}

export function SequenceStrip({ sequence, libraryItems, onFaceSwapClip }: SequenceStripProps) {
  const clips = sequence.draft.clips
  const itemsById = new Map(libraryItems.map((item) => [item.id, item]))
  return (
    <section aria-label="Sequence timeline" className="flex flex-col gap-2 rounded-xl border border-border bg-surface p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-[13px] font-semibold text-text">{sequenceCopy.timeline.title}</h3>
        <p className="text-[13px] text-faint">{sequenceCopy.timeline.hint}</p>
      </div>
      <div className="flex items-start gap-2 overflow-x-auto pb-1">
        {clips.map((clip, index) => (
          <div key={clip.jobId + "-" + index} className="flex items-start gap-2">
            {index > 0 && (
              <div className="pt-7">
                <TransitionChip
                  position={index}
                  transition={clip.transitionIn}
                  onCycle={(next) => sequence.setTransition(index, next)}
                />
              </div>
            )}
            <ShotCard
              index={index}
              total={clips.length}
              clip={clip}
              item={itemsById.get(clip.jobId) ?? null}
              sequence={sequence}
              onFaceSwap={onFaceSwapClip}
            />
          </div>
        ))}
        {Array.from({ length: emptySlotCount(clips.length) }).map((_, index) => (
          <EmptySlot key={"empty-" + index} />
        ))}
      </div>
    </section>
  )
}
