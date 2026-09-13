import { useCallback, useEffect, useRef, useState } from "react"
import type { Job } from "./createVideoTypes"

const COPIED_LABEL_MS = 2000

export type ResultActionsControls = {
  shareUrl: string
  isDownloading: boolean
  isCopied: boolean
  downloadVideo: () => void
  copyShareLink: () => void
}

function downloadFileName(job: Job): string {
  return `higgsfield-${job.preset_slug}-${job.id.slice(0, 8)}.mp4`
}

// The presigned URL can expire or lack CORS, so a failed save opens the video instead.
async function saveVideoBlob(job: Job): Promise<boolean> {
  if (job.video_url === null) return false
  try {
    const response = await fetch(job.video_url)
    if (!response.ok) return false
    const objectUrl = URL.createObjectURL(await response.blob())
    const link = document.createElement("a")
    link.href = objectUrl
    link.download = downloadFileName(job)
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
    return true
  } catch {
    return false
  }
}

export function useResultActions(job: Job): ResultActionsControls {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isCopied, setIsCopied] = useState(false)
  const copiedTimerRef = useRef<number | null>(null)
  const shareUrl = `${window.location.origin}/v/${job.id}`

  useEffect(
    () => () => {
      if (copiedTimerRef.current !== null) window.clearTimeout(copiedTimerRef.current)
    },
    [],
  )

  const downloadVideo = useCallback(() => {
    setIsDownloading(true)
    void saveVideoBlob(job).then((saved) => {
      setIsDownloading(false)
      if (!saved && job.video_url !== null) window.open(job.video_url, "_blank", "noopener")
    })
  }, [job])

  const copyShareLink = useCallback(() => {
    const clipboard = navigator.clipboard
    if (!clipboard) {
      window.open(shareUrl, "_blank", "noopener")
      return
    }
    clipboard.writeText(shareUrl).then(
      () => {
        setIsCopied(true)
        copiedTimerRef.current = window.setTimeout(() => setIsCopied(false), COPIED_LABEL_MS)
      },
      () => window.open(shareUrl, "_blank", "noopener"),
    )
  }, [shareUrl])

  return { shareUrl, isDownloading, isCopied, downloadVideo, copyShareLink }
}
