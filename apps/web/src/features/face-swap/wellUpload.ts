import { apiClient } from "../../api/client"
import type { RunWithGuestSession } from "../../api/guestSession"
import { putFileWithProgress } from "../../api/putFileWithProgress"
import type { Asset, WellState } from "./faceSwapTypes"

const RETRY_DELAY_MS = 1000

export type UploadResult =
  | { kind: "asset"; asset: Asset }
  | { kind: "reject" }
  | { kind: "failed"; errorKind: "network" | "session" | "not-finished" }
  | { kind: "silent" }

export function previewUrlOf(state: WellState): string | null {
  return state.status === "idle" ? null : state.previewUrl
}

async function pollComplete(assetId: string): Promise<UploadResult | null> {
  const { data, response } = await apiClient.POST("/api/v1/uploads/{asset_id}/complete", {
    params: { path: { asset_id: assetId } },
  })
  if (response.status === 422) return { kind: "reject" }
  if (data) return { kind: "asset", asset: data }
  if (response.status !== 409) return { kind: "failed", errorKind: response.status === 401 ? "session" : "network" }
  return null
}

async function finalizeUpload(assetId: string): Promise<UploadResult> {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    if (attempt > 0) await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS))
    const result = await pollComplete(assetId)
    if (result !== null) return result
  }
  return { kind: "failed", errorKind: "not-finished" }
}

async function postUpload(
  file: File,
  run: RunWithGuestSession,
): Promise<{ kind: "ready"; assetId: string; url: string; headers: Record<string, string> } | UploadResult> {
  const posted = await run(() =>
    apiClient.POST("/api/v1/uploads", { body: { content_type: file.type as "image/jpeg", byte_size: file.size } }),
  )
  if (posted.outcome === "session-failed") return { kind: "failed", errorKind: "session" }
  const { response, data } = posted.result
  if (response.status === 401) return { kind: "failed", errorKind: "session" }
  if (response.status === 422) return { kind: "reject" }
  if (response.status !== 201 || !data) return { kind: "failed", errorKind: "network" }
  return { kind: "ready", assetId: data.asset_id, url: data.upload_url, headers: data.upload_headers }
}

export async function createUpload(
  file: File,
  signal: AbortSignal,
  onProgress: (fraction: number) => void,
  run: RunWithGuestSession,
): Promise<UploadResult> {
  const posted = await postUpload(file, run)
  if (posted.kind !== "ready") return posted
  try {
    await putFileWithProgress({ url: posted.url, file, headers: posted.headers, signal, onProgress })
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return { kind: "silent" }
    return { kind: "failed", errorKind: "network" }
  }
  return finalizeUpload(posted.assetId)
}
