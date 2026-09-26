import type { LibraryItem } from "../../api/library"
import type { SequenceDraftControls } from "../../api/studioContracts"
import { MAX_SEQUENCE_CLIPS } from "../studio/draftOps"
import { clipEligibility, DEFAULT_CLIP_DURATION_MS } from "./sequenceDraftView"
import type { ClipAspects } from "./useClipAspects"
import { useClipAspects } from "./useClipAspects"
import { sequenceCopy } from "./sequenceCopy"

type AddShotPanelProps = {
  libraryItems: LibraryItem[]
  sequence: SequenceDraftControls
  onGoToClip?: () => void
  onGoToFaceSwap?: () => void
}

type ShotOptionProps = {
  item: LibraryItem
  aspect: number | null
  firstAspect: number | null
  isInDraft: boolean
  sequence: SequenceDraftControls
}

const ADD_BUTTON = "h-8 rounded-md border border-border px-2 text-xs font-medium text-text hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-50"

function shotTitle(item: LibraryItem): string {
  return item.prompt ?? item.preset_name ?? "Untitled"
}

function shotKindLabel(item: LibraryItem): string {
  return item.kind === "video_faceswap" ? "Swapped video" : "Clip"
}

function addShot(item: LibraryItem, aspect: number | null, sequence: SequenceDraftControls): void {
  sequence.addClip({
    jobId: item.id,
    posterUrl: item.thumbnail_url,
    aspect,
    durationMs: item.duration_ms ?? DEFAULT_CLIP_DURATION_MS,
  })
}

function ShotOption({ item, aspect, firstAspect, isInDraft, sequence }: ShotOptionProps) {
  const verdict = clipEligibility(item, firstAspect, aspect, isInDraft)
  const isBlocked = !verdict.eligible || isInDraft
  return (
    <div className="flex w-[15rem] shrink-0 flex-col gap-2 rounded-lg border border-border bg-surface p-2">
      <div className="flex items-center gap-2">
        {item.thumbnail_url ? (
          <img src={item.thumbnail_url} alt="" className="h-10 w-16 rounded object-cover" />
        ) : null}
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs text-text">{shotTitle(item)}</p>
          <p className="font-mono text-[10px] text-faint">{shotKindLabel(item)}</p>
        </div>
      </div>
      <button type="button" disabled={isBlocked} onClick={() => addShot(item, aspect, sequence)} className={ADD_BUTTON}>
        {isInDraft ? sequenceCopy.picker.added : sequenceCopy.picker.add}
      </button>
      {verdict.eligible ? null : <p className="text-[11px] text-faint">{verdict.reason}</p>}
    </div>
  )
}

function ShotOptionList({ candidates, aspects, firstAspect, draftIds, sequence }: {
  candidates: LibraryItem[]
  aspects: ClipAspects
  firstAspect: number | null
  draftIds: Set<string>
  sequence: SequenceDraftControls
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {candidates.map((item) => (
        <ShotOption
          key={item.id}
          item={item}
          aspect={aspects[item.id] ?? null}
          firstAspect={firstAspect}
          isInDraft={draftIds.has(item.id)}
          sequence={sequence}
        />
      ))}
    </div>
  )
}

function PanelLink({ label, onClick }: { label: string; onClick?: () => void }) {
  if (onClick === undefined) return null
  return <button type="button" onClick={onClick} className={ADD_BUTTON}>{label}</button>
}

function PanelNote({ title, body, onGoToClip, onGoToFaceSwap }: {
  title: string
  body: string
  onGoToClip?: () => void
  onGoToFaceSwap?: () => void
}) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-lg border border-dashed border-border bg-sunken p-3">
      <p className="text-[13px] font-medium text-text">{title}</p>
      <p className="max-w-[45ch] text-[13px] text-faint">{body}</p>
      <div className="flex flex-wrap gap-2">
        <PanelLink label={sequenceCopy.picker.goToClip} onClick={onGoToClip} />
        <PanelLink label={sequenceCopy.picker.goToFaceSwap} onClick={onGoToFaceSwap} />
      </div>
    </div>
  )
}

export function AddShotPanel({ libraryItems, sequence, onGoToClip, onGoToFaceSwap }: AddShotPanelProps) {
  const aspects = useClipAspects(libraryItems)
  const draftIds = new Set(sequence.draft.clips.map((clip) => clip.jobId))
  const firstAspect = sequence.draft.clips.find((clip) => clip.aspect !== null)?.aspect ?? null
  const candidates = libraryItems.filter((item) => item.kind === "video" || item.kind === "video_faceswap")
  if (candidates.length === 0) {
    return (
      <PanelNote
        title={sequenceCopy.picker.emptyTitle}
        body={sequenceCopy.picker.emptyBody}
        onGoToClip={onGoToClip}
        onGoToFaceSwap={onGoToFaceSwap}
      />
    )
  }
  if (sequence.draft.clips.length >= MAX_SEQUENCE_CLIPS) {
    return <PanelNote title={sequenceCopy.picker.fullTitle} body={sequenceCopy.picker.fullBody} />
  }
  return (
    <section aria-label={sequenceCopy.picker.heading} className="flex flex-col gap-2">
      <div>
        <h3 className="text-[13px] font-semibold text-text">{sequenceCopy.picker.heading}</h3>
        <p className="text-[13px] text-faint">{sequenceCopy.picker.hint}</p>
      </div>
      <ShotOptionList
        candidates={candidates}
        aspects={aspects}
        firstAspect={firstAspect}
        draftIds={draftIds}
        sequence={sequence}
      />
      <p className="text-[13px] text-faint">{sequenceCopy.picker.faceSwapHint}</p>
    </section>
  )
}
