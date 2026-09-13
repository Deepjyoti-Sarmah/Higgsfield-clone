import { useRef, useState } from "react"
import type { DragEvent, ReactNode, RefObject } from "react"
import { Button } from "../../ui/Button"
import { createVideoCopy } from "./createVideoCopy"
import type { ImageUploadControls, UploadErrorKind } from "./createVideoTypes"
import { ACCEPTED_IMAGE_TYPES } from "./imageFileRules"
import { ImageThumbnail } from "./ImageThumbnail"
import { useClipboardImagePaste } from "./useClipboardImagePaste"

type ImageDropZoneProps = {
  upload: ImageUploadControls
}

const HINT_ID = "create-video-image-hint"
const ERROR_ID = "create-video-image-error"

const errorMessage: Record<Exclude<UploadErrorKind, "invalid-file">, string> = {
  network: createVideoCopy.image.networkError,
  session: createVideoCopy.image.sessionError,
  "not-finished": createVideoCopy.image.notFinishedError,
}

function IdleContent({ isDragging, onBrowse }: { isDragging: boolean; onBrowse: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <p className="text-sm font-semibold text-text">
        {isDragging ? createVideoCopy.image.draggingTitle : createVideoCopy.image.idleTitle}
      </p>
      <p className="text-xs text-muted">{createVideoCopy.image.idleBody}</p>
      <Button variant="secondary" onClick={onBrowse}>
        {createVideoCopy.image.browse}
      </Button>
    </div>
  )
}

function UploadError({
  kind,
  onRetry,
}: {
  kind: Exclude<UploadErrorKind, "invalid-file">
  onRetry: () => void
}) {
  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <p id={ERROR_ID} role="alert" className="text-xs text-red-400">
        {errorMessage[kind]}
      </p>
      <Button variant="secondary" onClick={onRetry}>
        {createVideoCopy.image.retry}
      </Button>
    </div>
  )
}

type DropZoneProps = {
  isDragging: boolean
  isInvalidFile: boolean
  hasUploadError: boolean
  onDragOver: (event: DragEvent) => void
  onDragLeave: () => void
  onDrop: (event: DragEvent) => void
  children: ReactNode
}

function DropZone({
  isDragging,
  isInvalidFile,
  hasUploadError,
  onDragOver,
  onDragLeave,
  onDrop,
  children,
}: DropZoneProps) {
  const border = isDragging ? "border-accent bg-accent/5" : "border-border"
  const describedBy = isInvalidFile || !hasUploadError ? HINT_ID : `${HINT_ID} ${ERROR_ID}`
  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      aria-describedby={describedBy}
      className={`rounded-2xl border-2 border-dashed p-3 transition-colors ${border}`}
    >
      {children}
    </div>
  )
}

function DropBody({
  upload,
  isDragging,
  onBrowse,
}: {
  upload: ImageUploadControls
  isDragging: boolean
  onBrowse: () => void
}) {
  const state = upload.state
  if (state.status === "idle") return <IdleContent isDragging={isDragging} onBrowse={onBrowse} />
  if (state.status === "error") {
    return <UploadError kind={state.errorKind} onRetry={upload.retryUpload} />
  }
  return (
    <ImageThumbnail
      previewUrl={state.previewUrl}
      progress={state.status === "uploading" ? state.progress : null}
      onReplace={onBrowse}
      onRemove={upload.clearImage}
    />
  )
}

function HiddenFileInput({
  inputRef,
  onSelect,
}: {
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

function DropHint({ isInvalidFile }: { isInvalidFile: boolean }) {
  return (
    <p
      id={HINT_ID}
      role={isInvalidFile ? "alert" : undefined}
      className={`mt-2 text-xs ${isInvalidFile ? "text-red-400" : "text-muted"}`}
    >
      {createVideoCopy.image.hint}
    </p>
  )
}

export function ImageDropZone({ upload }: ImageDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  useClipboardImagePaste(upload.selectImage)
  const browseFiles = () => inputRef.current?.click()

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setIsDragging(false)
    const dropped = event.dataTransfer.files[0]
    if (dropped) upload.selectImage(dropped)
  }

  return (
    <div>
      <DropZone
        isDragging={isDragging}
        isInvalidFile={upload.rejection === "invalid-file"}
        hasUploadError={upload.state.status === "error"}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <DropBody upload={upload} isDragging={isDragging} onBrowse={browseFiles} />
      </DropZone>
      <HiddenFileInput inputRef={inputRef} onSelect={upload.selectImage} />
      <DropHint isInvalidFile={upload.rejection === "invalid-file"} />
    </div>
  )
}
