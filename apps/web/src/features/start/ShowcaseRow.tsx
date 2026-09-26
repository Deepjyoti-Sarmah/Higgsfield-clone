import { useState } from "react"
import type { ShowcaseMedia } from "../../api/webMedia"
import { SHOWCASE_GROUPS } from "../../api/webMedia"

function TileMedia({ item, onError }: { item: ShowcaseMedia; onError: () => void }) {
  if (item.kind === "still") {
    return <img src={item.url} alt="" onError={onError} className="h-full w-full object-cover" />
  }
  return (
    <video
      src={item.url}
      poster={item.poster ?? undefined}
      muted
      loop
      playsInline
      autoPlay
      preload="metadata"
      onError={onError}
      className="h-full w-full object-cover"
    />
  )
}

function ShowcaseTile({ item }: { item: ShowcaseMedia }) {
  const [failed, setFailed] = useState(false)
  if (failed && item.poster === null) return null
  const media = failed ? (
    <img src={item.poster ?? ""} alt="" className="h-full w-full object-cover" />
  ) : (
    <TileMedia item={item} onError={() => setFailed(true)} />
  )
  const aspect = item.kind === "still" ? "aspect-square" : "aspect-video"
  return (
    <figure className="flex flex-col gap-2">
      <div className={aspect + " overflow-hidden rounded-lg border border-border bg-sunken"}>
        {media}
      </div>
      <figcaption className="text-[0.8125rem] leading-snug text-muted">{item.caption}</figcaption>
    </figure>
  )
}

function SourceColumn({ still, previews }: { still: ShowcaseMedia; previews: readonly ShowcaseMedia[] }) {
  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-sm font-semibold text-text">{still.title}</h3>
      <ShowcaseTile item={still} />
      <div className="flex flex-col gap-3">
        {previews.map((preview) => (
          <ShowcaseTile key={preview.id} item={preview} />
        ))}
      </div>
    </section>
  )
}

export function ShowcaseRow() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {SHOWCASE_GROUPS.map((group) => (
        <SourceColumn key={group.source} still={group.still} previews={group.previews} />
      ))}
    </div>
  )
}
