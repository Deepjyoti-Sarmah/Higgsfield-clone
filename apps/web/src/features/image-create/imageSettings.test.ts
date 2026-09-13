import { expect, test } from "vitest"
import type { ImageOptions } from "../../api/imageOptions"
import type { ImagePhase } from "./imageCreateTypes"
import { DEFAULT_IMAGE_SETTINGS, blockedReason, deriveImagePhase, imageCost } from "./imageSettings"

const options: ImageOptions = {
  aspect_ratios: ["1:1", "4:5", "3:2", "16:9", "9:16"],
  qualities: ["standard", "high"],
  max_count: 4,
  credit_costs: { standard: 5, high: 12 },
}

test("imageCost multiplies the count by the unit cost of the chosen quality", () => {
  expect(imageCost(options, { ...DEFAULT_IMAGE_SETTINGS, count: 1 })).toBe(5)
  expect(imageCost(options, { aspectRatio: "16:9", quality: "high", count: 4 })).toBe(48)
  expect(imageCost(options, { ...DEFAULT_IMAGE_SETTINGS, quality: "high", count: 2 })).toBe(24)
  expect(imageCost(options, { ...DEFAULT_IMAGE_SETTINGS, count: 3 })).toBe(15)
})

test("blockedReason reports an empty prompt, whitespace, and unavailable options", () => {
  expect(blockedReason("", options)).toBe("no-prompt")
  expect(blockedReason("   ", options)).toBe("no-prompt")
  expect(blockedReason("a cat on a roof", options)).toBeNull()
  expect(blockedReason("a cat on a roof", null)).toBe("options-unavailable")
})

test("deriveImagePhase puts the options state ahead of every job phase", () => {
  const phases: ImagePhase[] = [
    "idle",
    "submitting",
    "queued",
    "running",
    "succeeded",
    "failed",
    "missing",
  ]
  expect(deriveImagePhase({ optionsStatus: "loading", jobPhase: "succeeded" })).toBe("options-loading")
  expect(deriveImagePhase({ optionsStatus: "error", jobPhase: "idle" })).toBe("options-error")
  for (const jobPhase of phases) {
    expect(deriveImagePhase({ optionsStatus: "ready", jobPhase })).toBe(jobPhase)
  }
})
