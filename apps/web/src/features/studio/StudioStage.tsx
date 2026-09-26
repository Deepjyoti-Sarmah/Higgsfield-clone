import type { LibraryItem } from "../../api/library"
import { GenerationBadge } from "../../ui/GenerationBadge"
import { railItemTitle } from "./railItemTitle"
import { formatDuration } from "./formatDuration"
import { StageActions } from "./StageActions"
import { StageProgress } from "./StageProgress"

type StudioStageProps = {
  item: LibraryItem | null
  liveStatus: "queued" | "running" | "succeeded" | "failed" | null
  onAnimateThis: (item: LibraryItem, imageUrl: string, assetId: string) => void
  onAddToSequence: (item: LibraryItem) => void
  sequenceFull: boolean
  onJobSettled: () => void
}

export type { StudioStageProps }

function PlaceholderCaption({ generatedBy }: { generatedBy: string | null | undefined }) {
  if (generatedBy !== "placeholder" && generatedBy !== "local-motion") return null
  const text =
    generatedBy === "placeholder"
      ? "Placeholder image: the model was unavailable"
      : "Motion preview: the local fallback rendered this clip"
  return <p className="text-[13px] text-muted">{text}</p>
}

function EmptyStage() {
  return (
    <div className="flex min-h-[40dvh] flex-col items-center justify-center gap-2 text-center">
      <p className="font-display text-2xl text-text">Pick something from the rail.</p>
      <p className="text-sm text-muted">Your work shows up here while it renders.</p>
    </div>
  )
}

function TerminalMedia({ item, onPickImage }: {
  item: LibraryItem
  onPickImage: (url: string, assetId: string) => void
}) {
  if (item.kind === "video" || item.kind === "sequence") {
    return (
      <video
        controls
        playsInline
        poster={item.thumbnail_url ?? undefined}
        src={item.video_url ?? undefined}
        className="max-h-[56dvh] max-w-full rounded-xl object-contain"
      />
    )
  }
  return (
    <div className="flex flex-wrap justify-center gap-3">
      {item.images.map((image) => (
        <button
          key={image.asset_id}
          type="button"
          onClick={() => onPickImage(image.url, image.asset_id)}
          aria-label="Animate this still"
          className="rounded-xl border border-border transition-transform hover:scale-[1.02]"
        >
          <img src={image.url} alt="" className="max-h-[52dvh] rounded-xl object-contain" />
        </button>
      ))}
    </div>
  )
}

function StageMedia({ item, onPickImage }: {
  item: LibraryItem
  onPickImage: (url: string, assetId: string) => void
}) {
  if (item.status === "failed") {
    return (
      <p className="max-w-[65ch] text-center text-sm text-danger">
        {item.error_message ?? "Render failed. Your credit was refunded."}
      </p>
    )
  }
  return <TerminalMedia item={item} onPickImage={onPickImage} />
}

function CaptionLine({ item }: { item: LibraryItem }) {
  const duration = formatDuration(item.duration_ms)
  const meta = [
    item.kind === "sequence" && item.clip_count !== null ? `${item.clip_count} shots` : null,
    duration,
    item.generated_by,
  ].filter(Boolean).join(" · ")
  return (
    <div className="flex items-center gap-3">
      <span className="truncate text-sm text-text">{railItemTitle(item)}</span>
      <span className="truncate font-mono text-[13px] text-muted">{meta}</span>
      <GenerationBadge generatedBy={item.generated_by} kind={item.kind} />
    </div>
  )
}

function StageFooter({ item, liveStatus, onAddToSequence, onAnimateThis, sequenceFull }: {
  item: LibraryItem
  liveStatus: StudioStageProps["liveStatus"]
  onAddToSequence: (item: LibraryItem) => void
  onAnimateThis: StudioStageProps["onAnimateThis"]
  sequenceFull: boolean
}) {
  const isLive = liveStatus === "queued" || liveStatus === "running"
  return (
    <div className="w-full space-y-3">
      {isLive ? (
        <p className="text-sm text-muted" aria-live="polite">
          {liveStatus === "running" ? "Rendering…" : "Queued…"}
        </p>
      ) : (
        <CaptionLine item={item} />
      )}
      <PlaceholderCaption generatedBy={item.generated_by} />
      <StageActions
        item={item}
        onAddToSequence={onAddToSequence}
        onAnimateThis={onAnimateThis}
        sequenceFull={sequenceFull}
      />
    </div>
  )
}

export function StudioStage(props: StudioStageProps) {
  const { item, liveStatus, onAddToSequence, sequenceFull } = props
  if (item === null) return <EmptyStage />

  const isTerminal = item.status === "succeeded" || item.status === "failed"
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 p-4 sm:p-6">
      <div className="flex w-full flex-1 items-center justify-center rounded-xl bg-sunken p-4">
        {isTerminal ? (
          <StageMedia item={item} onPickImage={(url, assetId) => props.onAnimateThis(item, url, assetId)} />
        ) : (
          <StageProgress kind={item.kind} jobId={item.id} status={liveStatus} onSettled={props.onJobSettled} />
        )}
      </div>
      <StageFooter
        item={item}
        liveStatus={liveStatus}
        onAddToSequence={onAddToSequence}
        onAnimateThis={props.onAnimateThis}
        sequenceFull={sequenceFull}
      />
    </div>
  )
}
