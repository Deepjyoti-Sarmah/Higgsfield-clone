import type { CanvasPhase, JobStatus, SubmitState, UploadState } from "./createVideoTypes"

export function isTerminalJobStatus(status: JobStatus): boolean {
  return status === "succeeded" || status === "failed"
}

const phaseByJobStatus: Record<JobStatus, CanvasPhase> = {
  queued: "queued",
  running: "generating",
  succeeded: "succeeded",
  failed: "failed",
}

const phaseByUploadStatus: Record<UploadState["status"], CanvasPhase> = {
  idle: "empty",
  uploading: "uploading",
  ready: "ready",
  error: "empty",
}

export function deriveCanvasPhase(input: {
  uploadStatus: UploadState["status"]
  submitStatus: SubmitState["status"]
  activeJobId: string | null
  jobStatus: JobStatus | null
  isJobMissing: boolean
}): CanvasPhase {
  if (input.activeJobId !== null) {
    if (input.isJobMissing) return "failed"
    if (input.jobStatus === null) return "queued"
    return phaseByJobStatus[input.jobStatus]
  }
  if (input.submitStatus === "submitting") return "submitting"
  return phaseByUploadStatus[input.uploadStatus]
}

export const CANVAS_TRANSITIONS: Record<CanvasPhase, CanvasPhase[]> = {
  empty: ["uploading", "queued", "generating", "succeeded", "failed"],
  uploading: ["uploading", "ready", "empty"],
  ready: ["uploading", "empty", "submitting", "queued", "generating", "succeeded", "failed"],
  submitting: ["queued", "ready", "empty"],
  queued: ["queued", "generating", "succeeded", "failed", "submitting"],
  generating: ["queued", "generating", "succeeded", "failed", "submitting"],
  succeeded: ["ready", "empty", "submitting", "queued", "generating", "succeeded", "failed"],
  failed: ["submitting", "ready", "empty", "queued", "generating", "succeeded", "failed"],
}
