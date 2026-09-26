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

const TILES = [
  SHOWCASE.still,
  SHOWCASE.clip,
  SHOWCASE.faceswap,
  SHOWCASE.sequence,
  SHOWCASE.orbitClip,
  SHOWCASE.canyonStill,
] as const

export function ShowcaseRow() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {TILES.map((tile) => (
        <ShowcaseCell
          key={tile.caption}
          url={tile.url}
          poster={tile.poster}
          caption={tile.caption}
          isVideo={tile.url.endsWith(".mp4")}
        />
      ))}
    </div>
  )
}
