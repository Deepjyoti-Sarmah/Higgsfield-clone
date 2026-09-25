import { describe, expect, it } from "vitest"
import { clipBlockedMessage, clipBlockedReason, clipInputImage, clipJobBody } from "./clipSubmit"

const SEED = { assetId: "seed-1", url: "/still.jpg" }
const COPY = {
  blockedNoImageNoPreset: "Add an image and pick a preset to animate.",
  blockedNoImage: "Add an image to animate.",
  blockedNoPreset: "Pick a preset to animate.",
  blockedUploading: "Wait for the upload to finish.",
}

describe("clip input image", () => {
  it("uses the seeded still with no upload", () => {
    const input = clipInputImage(SEED, null, null)
    expect(input).toEqual({ assetId: "seed-1", previewUrl: "/still.jpg", fromSeed: true })
  })

  it("prefers a freshly uploaded image over the seed", () => {
    const input = clipInputImage(SEED, "upload-9", "/preview.png")
    expect(input).toEqual({ assetId: "upload-9", previewUrl: "/preview.png", fromSeed: false })
  })

  it("is null with neither a seed nor an upload", () => {
    expect(clipInputImage(null, null, null)).toBeNull()
  })
})

describe("clip blocked reasons", () => {
  const input = clipInputImage(SEED, null, null)

  it("needs both an image and a preset", () => {
    expect(clipBlockedReason(null, false, false)).toBe("no-image-no-preset")
    expect(clipBlockedReason(null, true, false)).toBe("no-image")
    expect(clipBlockedReason(input, false, false)).toBe("no-preset")
    expect(clipBlockedReason(input, true, false)).toBeNull()
  })

  it("waits for a running upload first", () => {
    expect(clipBlockedReason(input, true, true)).toBe("uploading")
  })

  it("shows a visible message for each reason", () => {
    expect(clipBlockedMessage("no-preset", COPY)).toBe("Pick a preset to animate.")
    expect(clipBlockedMessage("uploading", COPY)).toBe("Wait for the upload to finish.")
    expect(clipBlockedMessage(null, COPY)).toBeNull()
  })
})

describe("clip job body", () => {
  const input = clipInputImage(SEED, null, null) as NonNullable<ReturnType<typeof clipInputImage>>

  it("sends the seeded asset id as input_asset_id and trims the prompt", () => {
    const body = clipJobBody(input, "dolly-in", "  fog  ", "key-1")
    expect(body).toEqual({
      preset_slug: "dolly-in",
      input_asset_id: "seed-1",
      prompt: "fog",
      idempotency_key: "key-1",
    })
  })

  it("sends null for a blank prompt", () => {
    expect(clipJobBody(input, "dolly-in", "   ", "key-1").prompt).toBeNull()
  })
})
