import { createVideoCopy } from "./createVideoCopy"

type SeededStillProps = {
  previewUrl: string | null
  onReplace: () => void
}

export function SeededStill({ previewUrl, onReplace }: SeededStillProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-sunken p-2">
      {previewUrl !== null ? (
        <img
          src={previewUrl}
          alt={createVideoCopy.image.alt}
          className="h-14 w-24 rounded-lg object-cover"
        />
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="text-[13px] font-medium text-text">
          {createVideoCopy.page.seededLabel}
        </span>
        <button
          type="button"
          onClick={onReplace}
          className="self-start text-xs text-muted underline hover:text-text"
        >
          {createVideoCopy.page.seededRemove}
        </button>
      </div>
    </div>
  )
}
