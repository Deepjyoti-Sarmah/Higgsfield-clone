import { Button } from "../../ui/Button"
import { buttonClasses } from "../../ui/buttonStyles"
import { createVideoCopy } from "./createVideoCopy"
import type { Job } from "./createVideoTypes"
import { useResultActions } from "./useResultActions"

type ResultActionsProps = {
  job: Job
  onMakeAnother: () => void
}

export function ResultActions({ job, onMakeAnother }: ResultActionsProps) {
  const { isDownloading, isCopied, downloadVideo, copyShareLink } = useResultActions(job)
  const downloadLabel = isDownloading
    ? createVideoCopy.result.downloading
    : createVideoCopy.result.download
  const shareLabel = isCopied ? createVideoCopy.result.linkCopied : createVideoCopy.result.share
  return (
    <div className="flex w-full flex-col items-center gap-2">
      <div className="flex flex-wrap items-center justify-center gap-2">
        <Button onClick={downloadVideo} isLoading={isDownloading} disabled={job.video_url === null}>
          {downloadLabel}
        </Button>
        <Button variant="secondary" onClick={onMakeAnother}>
          {createVideoCopy.result.makeAnother}
        </Button>
        <button type="button" onClick={copyShareLink} className={buttonClasses("secondary")}>
          {shareLabel}
        </button>
      </div>
      <a href={`/v/${job.id}`} className="text-xs text-muted underline hover:text-text">
        {createVideoCopy.result.openSharePage}
      </a>
    </div>
  )
}
