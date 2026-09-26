import { useState } from "react"
import { SHOWCASE } from "../../api/webMedia"

export function StillStepMedia() {
  const [failed, setFailed] = useState(false)
  if (failed) return null
  return (
    <img
      src={SHOWCASE.still.url}
      alt="A generated still"
      onError={() => setFailed(true)}
      className="h-36 w-full rounded-lg border border-border object-cover sm:h-44"
    />
  )
}

export function ClipStepMedia() {
  const [failed, setFailed] = useState(false)
  if (failed) return null
  return (
    <video
      src={SHOWCASE.clip.url}
      poster={SHOWCASE.clip.poster ?? undefined}
      muted
      loop
      playsInline
      autoPlay
      preload="metadata"
      onError={() => setFailed(true)}
      className="h-36 w-full rounded-lg border border-border object-cover motion-safe:sm:h-44"
    />
  )
}

export function SequenceStepMedia() {
  const [failed, setFailed] = useState(false)
  if (failed) return null
  return (
    <video
      src={SHOWCASE.sequence.url}
      poster={SHOWCASE.sequence.poster ?? undefined}
      muted
      loop
      playsInline
      autoPlay
      preload="metadata"
      onError={() => setFailed(true)}
      className="h-36 w-full rounded-lg border border-border object-cover motion-safe:sm:h-44"
    />
  )
}
