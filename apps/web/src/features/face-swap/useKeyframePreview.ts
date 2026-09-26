import { useCallback, useRef, useState } from "react"
import { apiClient } from "../../api/client"
import { submitFaceSwap } from "../../api/faceswapJobs"
import type { RunWithGuestSession } from "../../api/guestSession"
import { createUpload } from "./wellUpload"

export type KeyframePhase = "idle" | "working" | "ready" | "failed" | "insufficient"

function loadVideoFrame(url: string): Promise<HTMLVideoElement> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video")
    video.muted = true
    video.preload = "auto"
    video.crossOrigin = "anonymous"
    video.src = url
    video.onloadeddata = () => resolve(video)
    video.onerror = () => reject(new Error("frame-load"))
  })
}

function frameToJpeg(video: HTMLVideoElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement("canvas")
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext("2d")?.drawImage(video, 0, 0)
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("frame-encode"))),
      "image/jpeg",
      0.92,
    )
  })
}

async function uploadKeyframe(run: RunWithGuestSession, blob: Blob, signal: AbortSignal): Promise<string | null> {
  const file = new File([blob], "keyframe.jpg", { type: "image/jpeg" })
  const result = await createUpload(file, signal, () => undefined, run)
  return result.kind === "asset" ? result.asset.id : null
}

async function pollPreviewImage(run: RunWithGuestSession, jobId: string): Promise<string | null> {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000))
    const outcome = await run(() =>
      apiClient.GET("/api/v1/faceswap-jobs/{job_id}", { params: { path: { job_id: jobId } } }),
    )
    if (outcome.outcome === "session-failed") return null
    const job = outcome.result.data
    if (!job) continue
    if (job.status === "succeeded") return job.image_url
    if (job.status === "failed") return null
  }
  return null
}

// Keyframe preview reuses the untouched image submit: frame 0 of the target
// video is uploaded as a photo, then swapped through POST /faceswap-jobs.
export function useKeyframePreview(
  run: RunWithGuestSession,
  faceAssetId: string | null,
  targetUrl: string | null,
  onKeyframeReady: (assetId: string) => void,
) {
  const [phase, setPhase] = useState<KeyframePhase>("idle")
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const busyRef = useRef(false)
  const readyRef = useRef(onKeyframeReady)
  readyRef.current = onKeyframeReady

  const startPreview = useCallback(() => {
    if (faceAssetId === null || targetUrl === null || busyRef.current) return
    busyRef.current = true
    setPhase("working")
    setImageUrl(null)
    const controller = new AbortController()
    void previewPipeline(run, faceAssetId, targetUrl, controller.signal, readyRef).then((result) => {
      busyRef.current = false
      if (result.kind === "ready") {
        setImageUrl(result.url)
        setPhase("ready")
      } else {
        setPhase(result.kind)
      }
    })
  }, [faceAssetId, targetUrl, run])

  return { phase, imageUrl, canPreview: faceAssetId !== null && targetUrl !== null, startPreview }
}

async function previewPipeline(
  run: RunWithGuestSession,
  faceAssetId: string,
  targetUrl: string,
  signal: AbortSignal,
  readyRef: { current: (assetId: string) => void },
): Promise<{ kind: "ready"; url: string } | { kind: "failed" | "insufficient" }> {
  try {
    const video = await loadVideoFrame(targetUrl)
    const blob = await frameToJpeg(video)
    const keyframeId = await uploadKeyframe(run, blob, signal)
    if (keyframeId === null) return { kind: "failed" }
    readyRef.current(keyframeId)
    const preview = await submitFaceSwap(run, faceAssetId, keyframeId)
    if (preview.kind === "insufficient") return { kind: "insufficient" }
    if (preview.kind !== "accepted") return { kind: "failed" }
    const image = await pollPreviewImage(run, preview.jobId)
    return image === null ? { kind: "failed" } : { kind: "ready", url: image }
  } catch {
    return { kind: "failed" }
  }
}
