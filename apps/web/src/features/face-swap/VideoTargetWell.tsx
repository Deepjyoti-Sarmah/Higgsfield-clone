import { useRef, useState } from "react"
import type { DragEvent, RefObject } from "react"
import { faceSwapCopy } from "./faceSwapCopy"
import { VIDEO_FACESWAP_TARGET_MIME, isVideoTargetTooLong, videoRenderCost } from "./videoFaceSwapCost"
import type { VideoTargetState } from "./useVideoTargetWell"

const copy = faceSwapCopy.videoTarget

function CostLine({ durationMs }: { durationMs: number | null }) {
  if (durationMs === null) return <p className="text-xs text-muted">{copy.readingDuration}</p>
  if (isVideoTargetTooLong(durationMs)) {
    return (
      <p role="alert" className="text-xs text-danger">
        {copy.tooLong}
      </p>
    )
  }
  return (
    <p className="font-mono text-xs text-muted">
      {`Render cost: ${videoRenderCost(durationMs)} credits`}
    </p>
  )
}

function ActiveVideo({ target }: { target: VideoTargetState }) {
  if (target.url === null) return null
  const onReplace = target.fromSeed ? target.dropSeed : target.clearFile
  return (
    <div className="space-y-1">
      <video
        src={target.url}
        muted
        playsInline
        controls
        preload="metadata"
        className="max-h-48 w-full rounded-xl border border-border object-contain"
      />
      <div className="flex items-center gap-3">
        <CostLine durationMs={target.durationMs} />
        <button type="button" onClick={onReplace} className="text-xs text-muted underline hover:text-text">
          {copy.replace}
        </button>
      </div>
    </div>
  )
}

function HiddenVideoInput({ inputRef, onSelect }: {
  inputRef: RefObject<HTMLInputElement | null>
  onSelect: (file: File) => void
}) {
  return (
    <input
      ref={inputRef}
      type="file"
      accept={`${VIDEO_FACESWAP_TARGET_MIME},.mp4`}
      onChange={(event) => {
        const picked = event.target.files?.[0]
        if (picked) onSelect(picked)
        event.target.value = ""
      }}
      className="hidden"
    />
  )
}

function useVideoDragDrop(onFile: (file: File) => void) {
  const [isDragging, setIsDragging] = useState(false)
  return {
    isDragging,
    onDragOver: (event: DragEvent) => {
      event.preventDefault()
      setIsDragging(true)
    },
    onDragLeave: () => setIsDragging(false),
    onDrop: (event: DragEvent) => {
      event.preventDefault()
      setIsDragging(false)
      const dropped = event.dataTransfer.files[0]
      if (dropped) onFile(dropped)
    },
  }
}

function DropVideo({ target }: { target: VideoTargetState }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const drag = useVideoDragDrop(target.selectFile)
  const border = drag.isDragging ? "border-accent bg-accent/5" : "border-border"
  return (
    <div
      onDragOver={drag.onDragOver}
      onDragLeave={drag.onDragLeave}
      onDrop={drag.onDrop}
      className={`rounded-xl border-2 border-dashed transition-colors ${border}`}
    >
      <div className="flex flex-col items-center gap-2 py-4 text-center">
        <p className="text-xs text-muted">{copy.dropTitle}</p>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="h-9 rounded-[10px] border border-border bg-surface px-4 text-sm font-medium text-text hover:border-accent/60"
        >
          {copy.browse}
        </button>
      </div>
      <HiddenVideoInput inputRef={inputRef} onSelect={target.selectFile} />
    </div>
  )
}

export function VideoTargetWell({ target }: { target: VideoTargetState }) {
  return (
    <div className="flex-1 space-y-1">
      <p className="text-sm font-medium text-text">{copy.label}</p>
      <p className="text-xs text-muted">{copy.hint}</p>
      {target.url !== null ? <ActiveVideo target={target} /> : <DropVideo target={target} />}
      {target.rejection === "invalid-type" && (
        <p role="alert" className="text-xs text-danger">
          {copy.invalidType}
        </p>
      )}
      {target.rejection === "too-big" && (
        <p role="alert" className="text-xs text-danger">
          {copy.tooBig}
        </p>
      )}
      {target.url === null && <p className="mt-1 text-xs text-muted">{copy.seedHint}</p>}
    </div>
  )
}
