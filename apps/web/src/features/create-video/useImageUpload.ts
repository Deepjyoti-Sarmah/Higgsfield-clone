import { useCallback, useEffect, useRef, useState } from "react"
import { apiClient } from "../../api/client"
import type {
  Asset,
  ImageUploadControls,
  RunWithGuestSession,
  UploadErrorKind,
  UploadState,
} from "./createVideoTypes"
import { checkImageFile } from "./imageFileRules"
import { putFileWithProgress } from "./putFileWithProgress"

const RETRY_DELAY_MS = 1000

type FileErrorKind = Exclude<UploadErrorKind, "invalid-file">
type UploadResult =
  | { kind: "asset"; asset: Asset }
  | { kind: "reject" }
  | { kind: "failed"; errorKind: FileErrorKind }
  | { kind: "silent" }
type PresignedUpload = { upload_url: string; upload_headers: Record<string, string> }
type UploadSequence = {
  file: File
  signal: AbortSignal
  onProgress: (fraction: number) => void
}

function postUpload(file: File) {
  const body = { content_type: file.type as "image/jpeg", byte_size: file.size }
  return apiClient.POST("/api/v1/uploads", { body })
}

function previewUrlOf(state: UploadState): string | null {
  return state.status === "idle" ? null : state.previewUrl
}

async function completeUpload(assetId: string): Promise<{ status: number; asset: Asset | null }> {
  const { data, response } = await apiClient.POST("/api/v1/uploads/{asset_id}/complete", {
    params: { path: { asset_id: assetId } },
  })
  return { status: response.status, asset: data ?? null }
}

// 409 means storage has not seen the object yet, so one retry after 1s is enough.
async function finalizeUpload(assetId: string): Promise<UploadResult> {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (attempt > 0) await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS))
    const { status, asset } = await completeUpload(assetId)
    if (status === 422) return { kind: "reject" }
    if (asset) return { kind: "asset", asset }
    if (status !== 409) return { kind: "failed", errorKind: status === 401 ? "session" : "network" }
  }
  return { kind: "failed", errorKind: "not-finished" }
}

async function presignUpload(
  input: UploadSequence & { assetId: string; upload: PresignedUpload },
): Promise<UploadResult> {
  try {
    await putFileWithProgress({
      url: input.upload.upload_url,
      file: input.file,
      headers: input.upload.upload_headers,
      signal: input.signal,
      onProgress: input.onProgress,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return { kind: "silent" }
    return { kind: "failed", errorKind: "network" }
  }
  return finalizeUpload(input.assetId)
}

async function createUpload(input: UploadSequence, run: RunWithGuestSession): Promise<UploadResult> {
  const posted = await run(() => postUpload(input.file))
  if (posted.outcome === "session-failed") return { kind: "failed", errorKind: "session" }
  const { response, data } = posted.result
  if (response.status === 401) return { kind: "failed", errorKind: "session" }
  if (response.status === 422) return { kind: "reject" }
  if (response.status !== 201 || !data) return { kind: "failed", errorKind: "network" }
  const upload = { upload_url: data.upload_url, upload_headers: data.upload_headers }
  return presignUpload({ ...input, assetId: data.asset_id, upload })
}

type UploadOrchestration = {
  run: RunWithGuestSession
  applyState: (next: UploadState) => void
  cancelUpload: () => void
  setAbort: (controller: AbortController | null) => void
}

async function beginUpload(
  orchestration: UploadOrchestration,
  file: File,
  previewUrl: string,
): Promise<void> {
  orchestration.cancelUpload()
  const controller = new AbortController()
  orchestration.setAbort(controller)
  const applyState = orchestration.applyState
  applyState({ status: "uploading", file, previewUrl, progress: 0 })
  const onProgress = (fraction: number) =>
    applyState({ status: "uploading", file, previewUrl, progress: fraction })
  let result: UploadResult
  try {
    result = await createUpload(
      { file, signal: controller.signal, onProgress },
      orchestration.run,
    )
  } catch {
    result = { kind: "failed", errorKind: "network" }
  }
  if (controller.signal.aborted || result.kind === "silent") return
  if (result.kind === "asset") applyState({ status: "ready", file, previewUrl, asset: result.asset })
  else if (result.kind === "failed") {
    applyState({ status: "error", file, previewUrl, errorKind: result.errorKind })
  }
}

function useUploadControls() {
  const [state, setState] = useState<UploadState>({ status: "idle" })
  const [rejection, setRejection] = useState<"invalid-file" | null>(null)
  const stateRef = useRef<UploadState>(state)
  const abortRef = useRef<AbortController | null>(null)
  const applyState = useCallback((next: UploadState) => {
    stateRef.current = next
    setState(next)
  }, [])
  const cancelUpload = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])
  const setAbort = useCallback((controller: AbortController | null) => {
    abortRef.current = controller
  }, [])
  return { state, rejection, setRejection, stateRef, applyState, cancelUpload, setAbort }
}

type UploadControls = ReturnType<typeof useUploadControls> & { run: RunWithGuestSession }

function useUploadActions(controls: UploadControls) {
  const { rejection, setRejection, stateRef, applyState, cancelUpload, setAbort, run } = controls
  const start = useCallback(
    (file: File, previewUrl: string) =>
      beginUpload({ run, applyState, cancelUpload, setAbort }, file, previewUrl),
    [run, applyState, cancelUpload, setAbort],
  )
  const selectImage = useCallback(
    (file: File) => {
      setRejection(null)
      if (!checkImageFile(file)) {
        setRejection("invalid-file")
        return
      }
      const oldPreviewUrl = previewUrlOf(stateRef.current)
      if (oldPreviewUrl) URL.revokeObjectURL(oldPreviewUrl)
      void start(file, URL.createObjectURL(file))
    },
    [setRejection, start, stateRef],
  )
  const retryUpload = useCallback(() => {
    const current = stateRef.current
    if (current.status !== "error") return
    setRejection(null)
    void start(current.file, current.previewUrl)
  }, [setRejection, start, stateRef])
  const clearImage = useCallback(() => {
    cancelUpload()
    const previewUrl = previewUrlOf(stateRef.current)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setRejection(null)
    applyState({ status: "idle" })
  }, [applyState, cancelUpload, setRejection, stateRef])
  return { selectImage, retryUpload, clearImage, rejection }
}

export function useImageUpload(runWithGuestSession: RunWithGuestSession): ImageUploadControls {
  const uploadState = useUploadControls()
  const actions = useUploadActions({ ...uploadState, run: runWithGuestSession })
  const { cancelUpload, stateRef } = uploadState
  useEffect(
    () => () => {
      cancelUpload()
      const previewUrl = previewUrlOf(stateRef.current)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    },
    [cancelUpload, stateRef],
  )
  return { state: uploadState.state, ...actions }
}
