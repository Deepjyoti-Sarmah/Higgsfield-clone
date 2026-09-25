import { useEffect, useRef, useState } from "react"
import type { ChangeEvent, DragEvent } from "react"
import type { SequenceDraftControls } from "../../api/studioContracts"
import { useAudioUpload } from "../../api/audioUpload"
import type { AudioUploadState } from "../../api/audioUpload"
import type { GuestSessionSource } from "../../api/guestSession"
import { sequenceCopy } from "./sequenceCopy"

type MusicDropZoneProps = {
  session: GuestSessionSource
  sequence: SequenceDraftControls
  onUploadingChange?: (isUploading: boolean) => void
}

const AUDIO_ACCEPT = ".mp3,.m4a,.wav,audio/mpeg,audio/mp4,audio/wav"

function useDragHover() {
  const [isDragOver, setIsDragOver] = useState(false)
  const onDragOver = (event: DragEvent) => {
    event.preventDefault()
    setIsDragOver(true)
  }
  const onDragLeave = () => setIsDragOver(false)
  const onDrop = (event: DragEvent, onPick: (file: File) => void) => {
    event.preventDefault()
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file) onPick(file)
  }
  return { isDragOver, onDragOver, onDragLeave, onDrop }
}

function AudioWell({ onPick }: { onPick: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { isDragOver, onDragOver, onDragLeave, onDrop } = useDragHover()
  const wellClasses = `flex items-center justify-between gap-2 rounded-lg border border-dashed p-2 text-[13px] ${
    isDragOver ? "border-accent" : "border-border"
  }`
  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={(event) => onDrop(event, onPick)}
      className={wellClasses}
    >
      <span className="text-faint">{sequenceCopy.music.hint}</span>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="h-8 shrink-0 rounded-md border border-border bg-surface px-2 text-xs font-medium text-text hover:border-accent/60"
      >
        {sequenceCopy.music.browse}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={AUDIO_ACCEPT}
        className="hidden"
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0]
          if (file) onPick(file)
        }}
      />
    </div>
  )
}

function ActiveAudio({ name, onRemove }: { name: string; onRemove: () => void }) {
  return (
    <div className="flex items-center gap-2 text-sm text-text">
      <span className="truncate">{name}</span>
      <button
        type="button"
        onClick={onRemove}
        className="text-xs text-muted underline hover:text-text"
      >
        {sequenceCopy.music.remove}
      </button>
    </div>
  )
}

// The upload hook only knows the asset; the draft is what the render request reads.
function useSyncReadyAudio(state: AudioUploadState, setAudio: SequenceDraftControls["setAudio"]) {
  const readyAssetId = state.status === "ready" ? state.assetId : null
  const readyName = state.status === "ready" ? state.name : null
  useEffect(() => {
    if (readyAssetId !== null && readyName !== null) setAudio({ assetId: readyAssetId, name: readyName })
  }, [readyAssetId, readyName, setAudio])
}

export function MusicDropZone({ session, sequence, onUploadingChange }: MusicDropZoneProps) {
  const upload = useAudioUpload(session)
  const state = upload.state
  const isUploading = state.status === "uploading"
  const audio = sequence.draft.audio

  useEffect(() => {
    onUploadingChange?.(isUploading)
  }, [isUploading, onUploadingChange])
  useSyncReadyAudio(state, sequence.setAudio)

  return (
    <div className="flex flex-col gap-1">
      <p className="text-[13px] font-medium text-muted">{sequenceCopy.music.heading}</p>
      {audio ? (
        <ActiveAudio name={audio.name} onRemove={() => { sequence.setAudio(null); upload.clearAudio() }} />
      ) : (
        <AudioWell onPick={upload.pickAudio} />
      )}
      {isUploading && state.status === "uploading" && (
        <p className="text-[13px] text-faint" aria-live="polite">
          Uploading {state.name}… {Math.round(state.progress * 100)}%
        </p>
      )}
      {state.status === "error" && (
        <p role="alert" className="text-[13px] text-danger">
          {state.message}
        </p>
      )}
      {!audio && !isUploading && (
        <p className="text-[13px] text-faint">{sequenceCopy.music.silent}</p>
      )}
    </div>
  )
}
