import { Button } from "../../ui/Button"
import { ProgressBar } from "../../ui/ProgressBar"
import { createVideoCopy } from "./createVideoCopy"

type ImageThumbnailProps = {
  previewUrl: string
  progress: number | null
  onReplace: () => void
  onRemove: () => void
}

function UploadOverlay({ progress }: { progress: number }) {
  const label = createVideoCopy.image.uploading(Math.round(progress * 100))
  return (
    <div className="absolute inset-x-0 bottom-0 flex flex-col gap-2 bg-bg/80 p-3">
      <p className="text-xs font-semibold text-text">{label}</p>
      <ProgressBar value={progress} label={label} />
    </div>
  )
}

function ThumbnailActions({ onReplace, onRemove }: { onReplace: () => void; onRemove: () => void }) {
  return (
    <div className="flex items-center gap-2">
      <Button variant="secondary" onClick={onReplace}>
        {createVideoCopy.image.replace}
      </Button>
      <button
        type="button"
        aria-label={createVideoCopy.image.remove}
        onClick={onRemove}
        className="rounded-full border border-border px-3 py-2 text-sm text-muted transition-colors hover:border-red-400 hover:text-red-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        ✕
      </button>
    </div>
  )
}

export function ImageThumbnail({
  previewUrl,
  progress,
  onReplace,
  onRemove,
}: ImageThumbnailProps) {
  const isUploading = progress !== null
  return (
    <div className="flex flex-col gap-2">
      <div className="relative overflow-hidden rounded-xl border border-border">
        <img
          src={previewUrl}
          alt={createVideoCopy.image.alt}
          className="aspect-video w-full object-cover"
        />
        {isUploading && <UploadOverlay progress={progress} />}
      </div>
      {!isUploading && <ThumbnailActions onReplace={onReplace} onRemove={onRemove} />}
    </div>
  )
}
