import { useEffect, useRef, useState } from "react"
import type { FaceSwapSeed } from "../../api/studioContracts"
import { checkVideoFile } from "./videoFaceSwapCost"
import type { VideoFileRejection } from "./videoFaceSwapCost"
import { useHeldSeed } from "./useHeldSeed"
import { useSeedConsumedEffect } from "./useSeedConsumedEffect"

// Video targets stay client-side: rail seeds carry a preview URL, local mp4
// files stay as object URLs for preview + keyframe extraction. The render call
// uses the seeded id, which the API resolves to the caller's output asset.
export type VideoTargetState = {
  url: string | null
  durationMs: number | null
  targetAssetId: string | null
  fromSeed: boolean
  rejection: VideoFileRejection | null
  selectFile: (file: File) => void
  clearFile: () => void
  dropSeed: () => void
}

function useProbedDuration(url: string | null): number | null {
  const [durationMs, setDurationMs] = useState<number | null>(null)
  useEffect(() => {
    setDurationMs(null)
    if (url === null) return
    const probe = document.createElement("video")
    probe.preload = "metadata"
    probe.src = url
    const onLoaded = () => {
      if (Number.isFinite(probe.duration)) setDurationMs(Math.round(probe.duration * 1000))
    }
    probe.addEventListener("loadedmetadata", onLoaded)
    return () => probe.removeAttribute("src")
  }, [url])
  return durationMs
}

function useVideoFile(): { file: File | null; fileUrl: string | null; rejection: VideoFileRejection | null; selectFile: (file: File) => void; clearFile: () => void } {
  const [file, setFile] = useState<File | null>(null)
  const [fileUrl, setFileUrl] = useState<string | null>(null)
  const [rejection, setRejection] = useState<VideoFileRejection | null>(null)
  const urlRef = useRef<string | null>(null)

  const selectFile = (next: File) => {
    const rejected = checkVideoFile(next)
    setRejection(rejected)
    if (rejected !== null) return
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    const url = URL.createObjectURL(next)
    urlRef.current = url
    setFile(next)
    setFileUrl(url)
  }
  const clearFile = () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    urlRef.current = null
    setFile(null)
    setFileUrl(null)
    setRejection(null)
  }
  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
  }, [])
  return { file, fileUrl, rejection, selectFile, clearFile }
}

export function useVideoTargetWell(
  seed: FaceSwapSeed | null,
  onSeedConsumed: () => void,
): VideoTargetState {
  const held = useHeldSeed(seed)
  useSeedConsumedEffect(held.active, onSeedConsumed)
  const local = useVideoFile()

  const url = held.active !== null ? held.active.url : local.fileUrl
  const durationMs = useProbedDuration(url)
  return {
    url,
    durationMs,
    targetAssetId: held.active !== null ? held.active.assetId : null,
    fromSeed: held.active !== null,
    rejection: local.rejection,
    selectFile: local.selectFile,
    clearFile: local.clearFile,
    dropSeed: held.drop,
  }
}
