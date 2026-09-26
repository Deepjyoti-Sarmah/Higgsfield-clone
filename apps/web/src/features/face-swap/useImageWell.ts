import { useCallback, useEffect, useRef, useState } from "react"
import type { RunWithGuestSession } from "../../api/guestSession"
import { checkImageFile } from "./faceSwapTypes"
import type { WellControls, WellState } from "./faceSwapTypes"
import { createUpload, previewUrlOf } from "./wellUpload"
import type { UploadResult } from "./wellUpload"

function useWellState() {
  const [state, setState] = useState<WellState>({ status: "idle" })
  const [rejection, setRejection] = useState<"invalid-file" | null>(null)
  const stateRef = useRef(state)
  const abortRef = useRef<AbortController | null>(null)
  const applyState = useCallback((next: WellState) => {
    stateRef.current = next
    setState(next)
  }, [])
  const cancelUpload = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])
  return { state, rejection, setRejection, stateRef, abortRef, applyState, cancelUpload }
}

type WellStateControls = ReturnType<typeof useWellState>

function applyResult(
  applyState: (next: WellState) => void,
  file: File,
  previewUrl: string,
  result: UploadResult,
): void {
  if (result.kind === "asset") applyState({ status: "ready", file, previewUrl, asset: result.asset })
  else if (result.kind === "failed") applyState({ status: "error", file, previewUrl, errorKind: result.errorKind })
}

function useStartUpload(controls: WellStateControls, run: RunWithGuestSession) {
  const { abortRef, applyState, cancelUpload } = controls
  return useCallback(
    async (file: File, previewUrl: string) => {
      cancelUpload()
      const controller = new AbortController()
      abortRef.current = controller
      applyState({ status: "uploading", file, previewUrl, progress: 0 })
      const onProgress = (fraction: number) => applyState({ status: "uploading", file, previewUrl, progress: fraction })
      let result: UploadResult
      try {
        result = await createUpload(file, controller.signal, onProgress, run)
      } catch {
        result = { kind: "failed", errorKind: "network" }
      }
      if (controller.signal.aborted || result.kind === "silent") return
      applyResult(applyState, file, previewUrl, result)
    },
    [abortRef, applyState, cancelUpload, run],
  )
}

function useWellActions(controls: WellStateControls, start: ReturnType<typeof useStartUpload>) {
  const { rejection, setRejection, stateRef, applyState, cancelUpload } = controls
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

export function useImageWell(run: RunWithGuestSession): WellControls {
  const wellState = useWellState()
  const start = useStartUpload(wellState, run)
  const actions = useWellActions(wellState, start)
  const { cancelUpload, stateRef } = wellState
  useEffect(
    () => () => {
      cancelUpload()
      const previewUrl = previewUrlOf(stateRef.current)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    },
    [cancelUpload, stateRef],
  )
  return { state: wellState.state, ...actions }
}
