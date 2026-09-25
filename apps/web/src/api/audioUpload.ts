import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "./client"
import type { components } from "./generated/schema"
import { audioErrorKind } from "./audioRules"
import { useGuestSessionRunner } from "./guestSession"
import type { RunWithGuestSession } from "./guestSession"
import { putFileWithProgress } from "./putFileWithProgress"

type UploadContentType = components["schemas"]["UploadCreateRequest"]["content_type"]

export type AudioUploadState =
  | { status: "idle" }
  | { status: "uploading"; name: string; progress: number }
  | { status: "ready"; name: string; assetId: string }
  | { status: "error"; name: string; message: string }

export type AudioUploadControls = {
  state: AudioUploadState
  pickAudio: (file: File) => void
  clearAudio: () => void
}

const AUDIO_CONTENT_TYPES: Record<string, UploadContentType> = {
  "audio/mpeg": "audio/mpeg",
  "audio/mp4": "audio/mp4",
  "audio/wav": "audio/wav",
}

const ERROR_MESSAGES = {
  "wrong-type": "Use an mp3, m4a or wav file.",
  "too-large": "Music files are limited to 10 MB.",
  empty: "That file is empty.",
  session: "The upload failed. Try again.",
  network: "The upload failed. Try again.",
} as const

async function completeAudioUpload(assetId: string): Promise<boolean> {
  const { response } = await apiClient.POST("/api/v1/uploads/{asset_id}/complete", {
    params: { path: { asset_id: assetId } },
  })
  return response.status === 200
}

async function runAudioUpload(
  run: RunWithGuestSession,
  file: File,
  onProgress: (fraction: number) => void,
): Promise<string | null> {
  const contentType = AUDIO_CONTENT_TYPES[file.type]
  if (!contentType) return null
  const posted = await run(() =>
    apiClient.POST("/api/v1/uploads", { body: { content_type: contentType, byte_size: file.size } }),
  )
  if (posted.outcome === "session-failed") return null
  const { data, response } = posted.result
  if (response.status !== 201 || !data) return null
  await putFileWithProgress({
    url: data.upload_url,
    file,
    headers: data.upload_headers,
    signal: new AbortController().signal,
    onProgress,
  })
  const isReady = await completeAudioUpload(data.asset_id)
  return isReady ? data.asset_id : null
}

export function useAudioUpload(session: Parameters<typeof useGuestSessionRunner>[0]): AudioUploadControls {
  const runWithGuestSession = useGuestSessionRunner(session)
  const [state, setState] = useState<AudioUploadState>({ status: "idle" })
  const isMountedRef = useRef(true)
  const runRef = useRef(runWithGuestSession)
  runRef.current = runWithGuestSession

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const pickAudio = useCallback((file: File) => {
    const problem = audioErrorKind(file)
    if (problem !== null) {
      setState({ status: "error", name: file.name, message: ERROR_MESSAGES[problem] })
      return
    }
    setState({ status: "uploading", name: file.name, progress: 0 })
    void runAudioUpload(runRef.current, file, (fraction) =>
      setState((current) =>
        current.status === "uploading" ? { ...current, progress: fraction } : current,
      ),
    ).then((assetId) => {
      if (!isMountedRef.current) return
      if (assetId !== null) {
        setState({ status: "ready", name: file.name, assetId })
      } else {
        setState({ status: "error", name: file.name, message: ERROR_MESSAGES.network })
      }
    })
  }, [])

  const clearAudio = useCallback(() => setState({ status: "idle" }), [])

  return { state, pickAudio, clearAudio }
}
