import type { ImageInsufficient, ImageJob, ImageJobSettings, ImageJobSubmitError } from "../../api/imageJobs"

export type { ImageOptions, ImageOptionsState } from "../../api/imageOptions"
export type { ImageInsufficient, ImageJob }

export type ImageAspectRatio = ImageJobSettings["aspect_ratio"]
export type ImageQuality = ImageJobSettings["quality"]

export type ImageSettings = {
  aspectRatio: ImageAspectRatio
  quality: ImageQuality
  count: number
}

export type ImageSettingsControls = {
  settings: ImageSettings
  setAspectRatio: (value: ImageAspectRatio) => void
  setQuality: (value: ImageQuality) => void
  setCount: (value: number) => void
}

export type ImagePhase =
  | "idle"
  | "submitting"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "missing"

export type ImageStagePhase = "options-loading" | "options-error" | ImagePhase

export type ImageBlockedReason = "no-prompt" | "options-unavailable"

export type ImageSubmitErrorKind = ImageJobSubmitError

export type ImageBalance = {
  status: "loading" | "known" | "error"
  balance: number | null
}

export type ImageGenerateProps = {
  cost: number
  canGenerate: boolean
  blockedReason: ImageBlockedReason | null
  isSubmitting: boolean
  balance: ImageBalance
  insufficient: ImageInsufficient | null
  submitError: ImageSubmitErrorKind | null
  onGenerate: () => void
}

export type ImageJobWatch = {
  job: ImageJob | null
}
