import { useRef, useState } from "react"
import type { DragEvent, RefObject } from "react"
import { faceSwapCopy } from "./faceSwapCopy"
import { ACCEPTED_IMAGE_TYPES } from "./faceSwapTypes"
import type { WellControls } from "./faceSwapTypes"
import { SeededPreview, WellPreview } from "./WellPreview"

type ImageWellProps = {
  label: string
  hint: string
  seedUrl: string | null
  onDropSeed: () => void
  upload: WellControls
}

function DropZone({ isDragging, upload, onBrowse, onDragEvents }: {
  isDragging: boolean
  upload: WellControls
  onBrowse: () => void
  onDragEvents: { onDragOver: (e: DragEvent) => void; onDragLeave: () => void; onDrop: (e: DragEvent) => void }
}) {
  const border = isDragging ? "border-accent bg-accent/5" : "border-border"
  return (
    <div {...onDragEvents} className={`rounded-xl border-2 border-dashed transition-colors ${border}`}>
      <WellPreview upload={upload} onBrowse={onBrowse} />
    </div>
  )
}

function HiddenFileInput({ inputRef, onSelect }: {
  inputRef: RefObject<HTMLInputElement | null>
  onSelect: (file: File) => void
}) {
  return (
    <input
      ref={inputRef}
      type="file"
      accept={ACCEPTED_IMAGE_TYPES.join(",")}
      onChange={(event) => {
        const picked = event.target.files?.[0]
        if (picked) onSelect(picked)
        event.target.value = ""
      }}
      className="hidden"
    />
  )
}

function useDragDrop(onFile: (file: File) => void) {
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

export function ImageWell({ label, hint, seedUrl, onDropSeed, upload }: ImageWellProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const drag = useDragDrop(upload.selectImage)

  return (
    <div className="flex-1 space-y-1">
      <p className="text-sm font-medium text-text">{label}</p>
      <p className="text-xs text-muted">{hint}</p>
      {seedUrl !== null ? (
        <SeededPreview url={seedUrl} onReplace={onDropSeed} />
      ) : (
        <DropZone
          isDragging={drag.isDragging}
          upload={upload}
          onBrowse={() => inputRef.current?.click()}
          onDragEvents={drag}
        />
      )}
      <HiddenFileInput inputRef={inputRef} onSelect={upload.selectImage} />
      {upload.rejection === "invalid-file" && (
        <p role="alert" className="text-xs text-danger">
          {faceSwapCopy.image.hint}
        </p>
      )}
    </div>
  )
}
