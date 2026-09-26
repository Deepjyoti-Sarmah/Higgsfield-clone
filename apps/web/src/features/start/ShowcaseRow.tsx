import { useState } from "react"
import { SHOWCASE } from "../../api/webMedia"

type CellProps = { url: string; poster: string | null; caption: string; isVideo: boolean }

function CellMedia({ url, poster, isVideo, onError }: {
  url: string
  poster: string | null
  isVideo: boolean
  onError: () => void
}) {
  if (isVideo) {
    return (
      <video
        src={url}
        poster={poster ?? undefined}
        muted
        loop
        playsInline
        autoPlay
        preload="metadata"
        onError={onError}
        className="h-full w-full object-cover motion-safe:block"
      />
    )
  }
  return <img src={url} alt="" onError={onError} className="h-full w-full object-cover" />
}

function ShowcaseCell({ url, poster, caption, isVideo }: CellProps) {
  const [failed, setFailed] = useState(false)
  if (failed && poster === null) return null
  const media = failed ? (
    <img src={poster ?? ""} alt="" className="h-full w-full object-cover" />
  ) : (
    <CellMedia url={url} poster={poster} isVideo={isVideo} onError={() => setFailed(true)} />
  )
  return (
    <div className="flex flex-col gap-2">
      <div className="aspect-square overflow-hidden rounded-lg border border-border bg-sunken">
        {media}
      </div>
      <p className="font-mono text-[11px] text-muted">{caption}</p>
    </div>
  )
}

export function ShowcaseRow() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-[2fr_1fr_1fr_1fr]">
      <ShowcaseCell url={SHOWCASE.still.url} poster={SHOWCASE.still.poster} caption={SHOWCASE.still.caption} isVideo={false} />
      <ShowcaseCell url={SHOWCASE.clip.url} poster={SHOWCASE.clip.poster} caption={SHOWCASE.clip.caption} isVideo />
      <ShowcaseCell url={SHOWCASE.faceswap.url} poster={SHOWCASE.faceswap.poster} caption={SHOWCASE.faceswap.caption} isVideo={false} />
      <ShowcaseCell url={SHOWCASE.sequence.url} poster={SHOWCASE.sequence.poster} caption={SHOWCASE.sequence.caption} isVideo />
    </div>
  )
}
