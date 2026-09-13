import type { components } from "../../api/generated/schema"
import type { Preset, PresetsState } from "../../api/presets"

export type { Preset, PresetsState }

export type PresetCategory = Preset["category"]
export type Asset = components["schemas"]["AssetResponse"]
export type Job = components["schemas"]["JobResponse"]
export type JobStatus = Job["status"]
export type JobStatusEvent = components["schemas"]["JobStatusEvent"]
export type InsufficientCredits = components["schemas"]["InsufficientCreditsResponse"]

export type PresetCategoryFilter = "all" | PresetCategory

export type PresetSelection = {
  selectedSlug: string | null
  selectedPreset: Preset | null
  isUnknownSlug: boolean
  categoryFilter: PresetCategoryFilter
  setCategoryFilter: (v: PresetCategoryFilter) => void
  selectPreset: (slug: string) => void
  clearPreset: () => void
}

export type UploadErrorKind = "invalid-file" | "network" | "session" | "not-finished"

export type UploadState =
  | { status: "idle" }
  | { status: "uploading"; file: File; previewUrl: string; progress: number }
  | { status: "ready"; file: File; previewUrl: string; asset: Asset }
  | {
      status: "error"
      file: File
      previewUrl: string
      errorKind: Exclude<UploadErrorKind, "invalid-file">
    }

export type ImageUploadControls = {
  state: UploadState
  rejection: "invalid-file" | null
  selectImage: (file: File) => void
  clearImage: () => void
  retryUpload: () => void
}

export type JobDraft = {
  presetSlug: string
  presetName: string
  inputAssetId: string
  prompt: string | null
}

export type SubmitErrorKind =
  | "network"
  | "input-missing"
  | "input-not-ready"
  | "session"
  | "invalid"

export type SubmitState =
  | { status: "idle" }
  | { status: "submitting"; draft: JobDraft }
  | { status: "accepted"; jobId: string }
  | { status: "insufficient-credits"; insufficient: InsufficientCredits }
  | { status: "error"; errorKind: SubmitErrorKind; draft: JobDraft }

export type BalanceView =
  | { status: "guest-offer" }
  | { status: "loading" }
  | { status: "error" }
  | { status: "known"; balance: number }

export type GenerateBlockedReason =
  | "no-image-no-preset"
  | "no-image"
  | "no-preset"
  | "uploading"

export type CanvasPhase =
  | "empty"
  | "uploading"
  | "ready"
  | "submitting"
  | "queued"
  | "generating"
  | "succeeded"
  | "failed"

export type JobWatch = {
  job: Job | null
  status: JobStatus | null
  connection: "idle" | "live" | "polling"
  isMissing: boolean
  wasRequeued: boolean
}

export type CanvasView = {
  presetCount: number
  hasPreset: boolean
  job: Job | null
  isMissing: boolean
  inputImageUrl: string | null
  presetName: string
  elapsedSeconds: number
  wasRequeued: boolean
}

export type HistoryEntry = {
  jobId: string
  presetName: string
  status: JobStatus
  thumbnailUrl: string | null
  createdAt: string
}

export type GuestSessionOutcome<T> =
  | { outcome: "done"; result: T }
  | { outcome: "session-failed" }

export type RunWithGuestSession = <T extends { response: Response }>(
  request: () => Promise<T>,
) => Promise<GuestSessionOutcome<T>>
