import type { LibraryItem } from "../../api/library"
import type { SequenceDraftControls } from "../../api/studioContracts"
import { clipEligibility, DEFAULT_CLIP_DURATION_MS } from "./sequenceDraftView"
import { useClipAspects } from "./useClipAspects"
import { sequenceCopy } from "./sequenceCopy"

type ClipPickerProps = {
  libraryItems: LibraryItem[]
  sequence: SequenceDraftControls
  onGoToClipTab?: () => void
}

type ClipCardProps = {
  item: LibraryItem
  aspect: number | null
  firstAspect: number | null
  isInDraft: boolean
  sequence: SequenceDraftControls
}

function verdictFor(item: LibraryItem, firstAspect: number | null, aspect: number | null, inDraft: boolean) {
  return clipEligibility(item, firstAspect, aspect, inDraft)
}

function ClipCard({ item, aspect, firstAspect, isInDraft, sequence }: ClipCardProps) {
  const verdict = verdictFor(item, firstAspect, aspect, isInDraft)
  return (
    <div className="flex shrink-0 items-center gap-2 rounded-lg border border-border bg-surface p-1 pr-2">
      {item.thumbnail_url && (
        <img src={item.thumbnail_url} alt="" className="h-9 w-16 rounded object-cover" />
      )}
      <div className="flex flex-col">
        <span className="max-w-[140px] truncate text-xs text-text">
          {item.prompt ?? item.preset_name ?? "Untitled"}
        </span>
        {!verdict.eligible && verdict.reason && (
          <span className="text-[11px] text-faint">{verdict.reason}</span>
        )}
      </div>
      <button
        type="button"
        disabled={!verdict.eligible || isInDraft}
        onClick={() =>
          sequence.addClip({
            jobId: item.id,
            posterUrl: item.thumbnail_url,
            aspect,
            durationMs: item.duration_ms ?? DEFAULT_CLIP_DURATION_MS,
          })
        }
        className="h-8 rounded-md border border-border px-2 text-xs font-medium text-text hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isInDraft ? sequenceCopy.picker.added : sequenceCopy.picker.add}
      </button>
    </div>
  )
}

const VIDEO_ELIGIBLE_KIND = "video"

function isCandidate(item: LibraryItem): boolean {
  return item.kind === VIDEO_ELIGIBLE_KIND
}

function EmptyPicker({ onGoToClipTab }: { onGoToClipTab?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-lg border border-dashed border-border bg-sunken p-3">
      <p className="text-[13px] font-medium text-text">{sequenceCopy.picker.emptyTitle}</p>
      <p className="text-[13px] text-faint">{sequenceCopy.picker.emptyBody}</p>
      {onGoToClipTab && (
        <button
          type="button"
          onClick={onGoToClipTab}
          className="h-8 rounded-md border border-border bg-surface px-2 text-xs font-medium text-text hover:border-accent/60"
        >
          {sequenceCopy.picker.goToClip}
        </button>
      )}
    </div>
  )
}

export function ClipPicker({ libraryItems, sequence, onGoToClipTab }: ClipPickerProps) {
  const aspects = useClipAspects(libraryItems)
  const draftJobIds = new Set(sequence.draft.clips.map((clip) => clip.jobId))
  const firstAspect = sequence.draft.clips.find((clip) => clip.aspect !== null)?.aspect ?? null
  const candidates = libraryItems.filter(isCandidate)

  if (candidates.length === 0) return <EmptyPicker onGoToClipTab={onGoToClipTab} />

  return (
    <div className="flex flex-col gap-2">
      <p className="text-[13px] font-medium text-muted">{sequenceCopy.picker.heading}</p>
      <p className="text-[13px] text-faint">{sequenceCopy.picker.hint}</p>
      <p className="text-[13px] text-faint">{sequenceCopy.picker.stageHint}</p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {candidates.map((item) => (
          <ClipCard
            key={item.id}
            item={item}
            aspect={aspects[item.id] ?? null}
            firstAspect={firstAspect}
            isInDraft={draftJobIds.has(item.id)}
            sequence={sequence}
          />
        ))}
      </div>
    </div>
  )
}
