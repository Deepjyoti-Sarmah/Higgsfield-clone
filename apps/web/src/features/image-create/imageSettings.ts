import type { ImageOptions, ImageOptionsState } from "../../api/imageOptions"
import type { ImageBlockedReason, ImagePhase, ImageSettings, ImageStagePhase } from "./imageCreateTypes"

export const DEFAULT_IMAGE_SETTINGS: ImageSettings = {
  aspectRatio: "1:1",
  quality: "standard",
  count: 1,
}

export function imageCost(options: ImageOptions, settings: ImageSettings): number {
  const unit =
    settings.quality === "high" ? options.credit_costs.high : options.credit_costs.standard
  return settings.count * unit
}

export function blockedReason(
  prompt: string,
  options: ImageOptions | null,
): ImageBlockedReason | null {
  if (options === null) return "options-unavailable"
  return prompt.trim() === "" ? "no-prompt" : null
}

export function deriveImagePhase(input: {
  optionsStatus: ImageOptionsState["status"]
  jobPhase: ImagePhase
}): ImageStagePhase {
  if (input.optionsStatus === "loading") return "options-loading"
  if (input.optionsStatus === "error") return "options-error"
  return input.jobPhase
}

export type ImageProgressPhase = "submitting" | "queued" | "running"

export function isImageProgressPhase(phase: ImageStagePhase): phase is ImageProgressPhase {
  return phase === "submitting" || phase === "queued" || phase === "running"
}
