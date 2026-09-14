import type { ReactNode } from "react"
import type { LibraryItem as LibraryItemData } from "../../api/library"
import { ButtonLink } from "../../ui/ButtonLink"
import { buttonClasses } from "../../ui/buttonStyles"
import { GenerationBadge } from "../../ui/GenerationBadge"
import { libraryCopy } from "./libraryCopy"

type LibraryResultViewProps = {
  item: LibraryItemData | null
}

function makeAnotherHref(presetSlug: string): string {
  return `/create/video?preset=${encodeURIComponent(presetSlug)}`
}

function ResultPanel({ children }: { children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-border bg-surface p-4">
      {children}
    </section>
  )
}

function ResultMessage({ message }: { message: string }) {
  return (
    <ResultPanel>
      <p className="text-sm text-muted">{message}</p>
    </ResultPanel>
  )
}

function ResultVideo({ videoUrl }: { videoUrl: string }) {
  return (
    <video
      src={videoUrl}
      controls
      muted
      autoPlay
      loop
      playsInline
      className="w-full rounded-xl border border-border"
    />
  )
}

function ResultImages({ imageUrls, label }: { imageUrls: string[]; label: string }) {
  return (
    <ul className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
      {imageUrls.map((url, index) => (
        <li key={url}>
          <img
            src={url}
            alt={`${label} ${index + 1}`}
            className="w-full rounded-xl border border-border"
          />
        </li>
      ))}
    </ul>
  )
}

function makeAnotherHrefForItem(item: LibraryItemData): string {
  if (item.kind === "image") return "/create/image"
  return makeAnotherHref(item.preset_slug ?? "")
}

function ResultActions({ item }: { item: LibraryItemData }) {
  const downloadUrl = item.kind === "image" ? (item.image_urls[0] ?? null) : item.video_url
  return (
    <div className="flex flex-wrap items-center gap-3">
      <GenerationBadge generatedBy={item.generated_by} kind={item.kind} />
      {downloadUrl !== null && item.kind === "video" && (
        <a href={downloadUrl} download className={buttonClasses("secondary")}>
          {libraryCopy.result.download}
        </a>
      )}
      <ButtonLink to={makeAnotherHrefForItem(item)}>{libraryCopy.result.makeAnother}</ButtonLink>
    </div>
  )
}

export function LibraryResultView({ item }: LibraryResultViewProps) {
  if (item === null) return <ResultMessage message={libraryCopy.item.missing} />
  if (item.status === "failed") {
    return <ResultMessage message={item.error_message ?? libraryCopy.item.failedFallback} />
  }
  if (item.status !== "succeeded") {
    return <ResultMessage message={libraryCopy.item.status[item.status]} />
  }
  return (
    <ResultPanel>
      {item.kind === "image" ? (
        <ResultImages imageUrls={item.image_urls} label={libraryCopy.item.label(item)} />
      ) : (
        item.video_url !== null && <ResultVideo videoUrl={item.video_url} />
      )}
      <ResultActions item={item} />
    </ResultPanel>
  )
}
