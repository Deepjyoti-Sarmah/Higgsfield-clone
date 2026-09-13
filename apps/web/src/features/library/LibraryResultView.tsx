import type { ReactNode } from "react"
import type { LibraryItem as LibraryItemData } from "../../api/library"
import { ButtonLink } from "../../ui/ButtonLink"
import { buttonClasses } from "../../ui/buttonStyles"
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

function ResultActions({ item }: { item: LibraryItemData }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {item.video_url !== null && (
        <a href={item.video_url} download className={buttonClasses("secondary")}>
          {libraryCopy.result.download}
        </a>
      )}
      <ButtonLink to={makeAnotherHref(item.preset_slug)}>
        {libraryCopy.result.makeAnother}
      </ButtonLink>
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
      {item.video_url !== null && <ResultVideo videoUrl={item.video_url} />}
      <ResultActions item={item} />
    </ResultPanel>
  )
}
